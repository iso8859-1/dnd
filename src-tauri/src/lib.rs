//! Tauri desktop deck builder (replaces the former Textual TUI).
//!
//! Native dialogs and file opening are driven from Rust, so the web UI only
//! needs to call the app's own commands — no plugin permissions are exposed.

use std::path::{Path, PathBuf};
use std::sync::Mutex;

use dnd_cards_core::{
    compose_pdf, compose_pdf_duplex, config, layout_info, load_card, load_deck, loader::load_name,
    resolve_deck, save_deck as write_deck, scan_cards, scanner::discover_languages, text::slugify,
    CardData, DeckProfile, LayoutInfo,
};
use indexmap::IndexMap;
use serde::Serialize;
use tauri::{AppHandle, Manager, State};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_opener::OpenerExt;

struct AppState {
    data_dir: PathBuf,
    /// Deck passed on the command line (`dnd-cards-app my-deck.yaml`).
    initial_deck: Mutex<Option<PathBuf>>,
    /// Last directory used in a deck / PDF dialog.
    last_dir: Mutex<Option<PathBuf>>,
}

type CmdResult<T> = Result<T, String>;

#[derive(Serialize)]
struct CardInfo {
    key: String,
    name: String,
    card_type: String,
    lang: String,
    /// How the card prints; `None` if it can't be printed (see `error`).
    layout: Option<LayoutInfo>,
    error: Option<String>,
}

#[derive(Serialize)]
struct Catalog {
    data_dir: String,
    languages: Vec<String>,
    types: Vec<String>,
    cards: Vec<CardInfo>,
}

#[derive(Serialize)]
struct LoadedDeck {
    path: String,
    name: String,
    cards: Vec<(String, u32)>,
}

fn deck_profile(name: &str, cards: Vec<(String, u32)>) -> DeckProfile {
    let cards: IndexMap<String, u32> = cards.into_iter().filter(|(_, q)| *q > 0).collect();
    DeckProfile {
        name: name.trim().to_string(),
        cards,
    }
}

fn file_stem_or(name: &str, fallback: &str) -> String {
    let slug = slugify(name);
    if slug.is_empty() {
        fallback.to_string()
    } else {
        slug
    }
}

fn start_dir(app: &AppHandle, state: &AppState) -> Option<PathBuf> {
    state
        .last_dir
        .lock()
        .unwrap()
        .clone()
        .or_else(|| app.path().document_dir().ok())
}

fn remember_dir(state: &AppState, path: &Path) {
    if let Some(parent) = path.parent() {
        *state.last_dir.lock().unwrap() = Some(parent.to_path_buf());
    }
}

fn read_deck(path: &Path) -> CmdResult<LoadedDeck> {
    let deck = load_deck(path).map_err(|e| e.to_string())?;
    Ok(LoadedDeck {
        path: path.display().to_string(),
        name: deck.name,
        cards: deck.cards.into_iter().collect(),
    })
}

// ── Commands ─────────────────────────────────────────────────────────────────

/// Index the data store and read every card's display name.
#[tauri::command]
async fn catalog(state: State<'_, AppState>) -> CmdResult<Catalog> {
    let data_dir = state.data_dir.clone();
    if !data_dir.is_dir() {
        return Err(format!(
            "Card data directory not found: {}",
            data_dir.display()
        ));
    }
    let index = scan_cards(&data_dir);
    let mut types: Vec<String> = index.values().map(|r| r.card_type.clone()).collect();
    types.sort();
    types.dedup();
    let cards = index
        .into_iter()
        .map(|(key, r)| {
            let (name, layout, error) = match load_card(&r.path) {
                Ok(card) => (card.name.clone(), Some(layout_info(&card)), None),
                Err(e) => (load_name(&r.path), None, Some(e.to_string())),
            };
            CardInfo {
                name,
                key,
                card_type: r.card_type,
                lang: r.lang,
                layout,
                error,
            }
        })
        .collect();
    Ok(Catalog {
        data_dir: data_dir.display().to_string(),
        languages: discover_languages(&data_dir),
        types,
        cards,
    })
}

/// Full card data for the preview pane.
#[tauri::command]
async fn card_details(state: State<'_, AppState>, key: String) -> CmdResult<CardData> {
    let index = scan_cards(&state.data_dir);
    let r = index
        .get(&key)
        .ok_or_else(|| format!("Card not found: {key}"))?;
    load_card(&r.path).map_err(|e| e.to_string())
}

/// Deck given on the command line, if any (consumed on first call).
#[tauri::command]
fn initial_deck(state: State<'_, AppState>) -> CmdResult<Option<LoadedDeck>> {
    match state.initial_deck.lock().unwrap().take() {
        Some(p) => read_deck(&p).map(Some),
        None => Ok(None),
    }
}

#[tauri::command]
async fn open_deck(app: AppHandle, state: State<'_, AppState>) -> CmdResult<Option<LoadedDeck>> {
    let mut dlg = app
        .dialog()
        .file()
        .set_title("Open deck")
        .add_filter("Deck", &["yaml", "yml"]);
    if let Some(dir) = start_dir(&app, &state) {
        dlg = dlg.set_directory(dir);
    }
    let Some(picked) = dlg.blocking_pick_file() else {
        return Ok(None);
    };
    let path = picked.into_path().map_err(|e| e.to_string())?;
    remember_dir(&state, &path);
    read_deck(&path).map(Some)
}

/// Save the deck. Without `path` (or with `save_as`), ask for a location.
/// Returns the written path, or `None` if the user cancelled.
#[tauri::command]
async fn save_deck(
    app: AppHandle,
    state: State<'_, AppState>,
    path: Option<String>,
    save_as: bool,
    name: String,
    cards: Vec<(String, u32)>,
) -> CmdResult<Option<String>> {
    let deck = deck_profile(&name, cards);
    if deck.name.is_empty() {
        return Err("Please give the deck a name first.".into());
    }
    let target = match path.filter(|_| !save_as) {
        Some(p) => PathBuf::from(p),
        None => {
            let mut dlg = app
                .dialog()
                .file()
                .set_title("Save deck")
                .add_filter("Deck", &["yaml"])
                .set_file_name(format!("{}.yaml", file_stem_or(&deck.name, "deck")));
            if let Some(dir) = start_dir(&app, &state) {
                dlg = dlg.set_directory(dir);
            }
            let Some(picked) = dlg.blocking_save_file() else {
                return Ok(None);
            };
            picked.into_path().map_err(|e| e.to_string())?
        }
    };
    write_deck(&target, &deck).map_err(|e| e.to_string())?;
    remember_dir(&state, &target);
    Ok(Some(target.display().to_string()))
}

/// Build the PDF for the current selection, ask where to save it, then open it.
#[tauri::command]
async fn generate_pdf(
    app: AppHandle,
    state: State<'_, AppState>,
    name: String,
    cards: Vec<(String, u32)>,
    duplex: bool,
) -> CmdResult<Option<String>> {
    let deck = deck_profile(&name, cards);
    if deck.cards.is_empty() {
        return Err("The deck is empty — add cards with + first.".into());
    }
    let label = if deck.name.is_empty() {
        "untitled".to_string()
    } else {
        deck.name.clone()
    };
    let resolved =
        resolve_deck(&deck, &scan_cards(&state.data_dir), &label).map_err(|e| e.to_string())?;
    let bytes = if duplex {
        compose_pdf_duplex(&resolved)
    } else {
        compose_pdf(&resolved)
    };

    let suffix = if duplex { "-duplex" } else { "" };
    let mut dlg = app
        .dialog()
        .file()
        .set_title(if duplex {
            "Save duplex PDF"
        } else {
            "Save PDF"
        })
        .add_filter("PDF", &["pdf"])
        .set_file_name(format!("{}{suffix}.pdf", file_stem_or(&deck.name, "deck")));
    if let Some(dir) = start_dir(&app, &state) {
        dlg = dlg.set_directory(dir);
    }
    let Some(picked) = dlg.blocking_save_file() else {
        return Ok(None);
    };
    let out = picked.into_path().map_err(|e| e.to_string())?;
    std::fs::write(&out, bytes).map_err(|e| format!("{}: {e}", out.display()))?;
    remember_dir(&state, &out);

    // Opening is a convenience; a missing PDF viewer shouldn't fail the command.
    let _ = app
        .opener()
        .open_path(out.display().to_string(), None::<&str>);
    Ok(Some(out.display().to_string()))
}

// ── Setup ────────────────────────────────────────────────────────────────────

fn resolve_data_dir(app: &AppHandle) -> PathBuf {
    if let Some(p) = std::env::var_os("DND_CARDS_DATA") {
        return PathBuf::from(p);
    }
    let bundled = app
        .path()
        .resource_dir()
        .ok()
        .map(|d| d.join("data"))
        .filter(|d| d.is_dir());
    bundled
        .or_else(config::find_data_dir)
        .unwrap_or_else(|| PathBuf::from("data"))
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let initial_deck = std::env::args_os()
                .nth(1)
                .map(PathBuf::from)
                .filter(|p| p.is_file());
            app.manage(AppState {
                data_dir: resolve_data_dir(app.handle()),
                last_dir: Mutex::new(
                    initial_deck
                        .as_ref()
                        .and_then(|p| p.parent().map(Path::to_path_buf)),
                ),
                initial_deck: Mutex::new(initial_deck),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            catalog,
            card_details,
            initial_deck,
            open_deck,
            save_deck,
            generate_pdf
        ])
        .run(tauri::generate_context!())
        .expect("error while running DnD Cards");
}

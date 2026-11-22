//! Tauri desktop deck builder (replaces the former Textual TUI).
//!
//! Native dialogs and file opening are driven from Rust, so the web UI only
//! needs to call the app's own commands — no plugin permissions are exposed.

mod sources;

use std::path::{Path, PathBuf};
use std::sync::Mutex;

use dnd_cards_core::{
    compose_pdf, compose_pdf_duplex, layout_info, load_card, load_deck, loader::load_name,
    resolve_deck, save_deck as write_deck, scan_cards, scanner::discover_languages, sort_cards,
    text::slugify, CardData, DeckProfile, LayoutInfo,
};
use indexmap::IndexMap;
use serde::Serialize;
use tauri::{AppHandle, Manager, State};
use tauri_plugin_dialog::DialogExt;
use tauri_plugin_opener::OpenerExt;

struct AppState {
    /// Directory of the selected data source.
    data_dir: Mutex<PathBuf>,
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
    /// Spell grade, class feature level or minimum level of a feat (for the level filter).
    level: Option<i64>,
    /// How the card prints; `None` if it can't be printed (see `error`).
    layout: Option<LayoutInfo>,
    error: Option<String>,
}

#[derive(Serialize)]
struct Catalog {
    data_dir: String,
    /// Display name of the selected data source.
    source: String,
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
        .filter(|d| d.is_dir())
        .or_else(|| app.path().document_dir().ok())
}

/// Remember the folder of `path` for the next dialog, also across restarts.
fn remember_dir(app: &AppHandle, state: &AppState, path: &Path) {
    let Some(parent) = path.parent() else {
        return;
    };
    *state.last_dir.lock().unwrap() = Some(parent.to_path_buf());
    let mut settings = sources::load_settings(app);
    if settings.last_dir.as_deref() != Some(parent) {
        settings.last_dir = Some(parent.to_path_buf());
        // best effort: a failed write only loses the remembered folder
        let _ = sources::save_settings(app, &settings);
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

/// Level used by the UI's level filter: the card's `level`, or for feats the
/// minimum level from the category ("… (Voraussetzung: min. 4. Stufe)"),
/// 1 for feats without a level requirement.
fn filter_level(card: &CardData) -> Option<i64> {
    if card.level.is_some() {
        return card.level;
    }
    if card.card_type != "talent" {
        return None;
    }
    let typ = card.typ.as_deref().unwrap_or("");
    let min_level = typ.find("min.").and_then(|i| {
        let digits: String = typ[i + 4..]
            .trim_start()
            .chars()
            .take_while(|c| c.is_ascii_digit())
            .collect();
        let rest = typ[i + 4..].trim_start()[digits.len()..].trim_start();
        (rest.starts_with(". Stufe") || rest.starts_with(".Stufe"))
            .then(|| digits.parse().ok())
            .flatten()
    });
    Some(min_level.unwrap_or(1))
}

// ── Commands ─────────────────────────────────────────────────────────────────

/// Index the data store and read every card's display name.
#[tauri::command]
async fn catalog(app: AppHandle, state: State<'_, AppState>) -> CmdResult<Catalog> {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let source = sources::discover(&app, &sources::load_settings(&app))
        .into_iter()
        .find(|s| Path::new(&s.path) == data_dir)
        .map(|s| s.name)
        .unwrap_or_else(|| data_dir.display().to_string());
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
            let (name, level, layout, error) = match load_card(&r.path) {
                Ok(card) => (
                    card.name.clone(),
                    filter_level(&card),
                    Some(layout_info(&card)),
                    None,
                ),
                Err(e) => (load_name(&r.path), None, None, Some(e.to_string())),
            };
            CardInfo {
                name,
                key,
                card_type: r.card_type,
                lang: r.lang,
                level,
                layout,
                error,
            }
        })
        .collect();
    Ok(Catalog {
        data_dir: data_dir.display().to_string(),
        source,
        languages: discover_languages(&data_dir),
        types,
        cards,
    })
}

/// Full card data for the preview pane.
#[tauri::command]
async fn card_details(state: State<'_, AppState>, key: String) -> CmdResult<CardData> {
    let index = scan_cards(&state.data_dir.lock().unwrap());
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
    remember_dir(&app, &state, &path);
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
    remember_dir(&app, &state, &target);
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
    let mut resolved = resolve_deck(&deck, &scan_cards(&state.data_dir.lock().unwrap()), &label)
        .map_err(|e| e.to_string())?;
    sort_cards(&mut resolved);
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
    remember_dir(&app, &state, &out);

    // Opening is a convenience; a missing PDF viewer shouldn't fail the command.
    let _ = app
        .opener()
        .open_path(out.display().to_string(), None::<&str>);
    Ok(Some(out.display().to_string()))
}

// ── Data sources ─────────────────────────────────────────────────────────────

#[derive(Serialize)]
struct SourceList {
    sources: Vec<sources::DataSource>,
    active: Option<String>,
    /// Where dataset installers put their data.
    datasets_dir: Option<String>,
}

fn source_list(app: &AppHandle, state: &AppState) -> SourceList {
    let settings = sources::load_settings(app);
    let list = sources::discover(app, &settings);
    let current = state.data_dir.lock().unwrap().clone();
    let active = list
        .iter()
        .find(|s| Path::new(&s.path) == current)
        .map(|s| s.id.clone());
    SourceList {
        sources: list,
        active,
        datasets_dir: sources::datasets_dir(app).map(|d| d.display().to_string()),
    }
}

/// Available data sources and the selected one.
#[tauri::command]
fn data_sources(app: AppHandle, state: State<'_, AppState>) -> SourceList {
    source_list(&app, &state)
}

/// Switch to another data source and remember the choice.
#[tauri::command]
fn set_data_source(
    app: AppHandle,
    state: State<'_, AppState>,
    id: String,
) -> CmdResult<SourceList> {
    let mut settings = sources::load_settings(&app);
    let src = sources::discover(&app, &settings)
        .into_iter()
        .find(|s| s.id == id)
        .ok_or_else(|| format!("Unknown data source: {id}"))?;
    *state.data_dir.lock().unwrap() = PathBuf::from(&src.path);
    settings.data_source = Some(id);
    sources::save_settings(&app, &settings)?;
    Ok(source_list(&app, &state))
}

/// Pick a folder with card data, add it as a source and select it.
#[tauri::command]
async fn add_data_source(
    app: AppHandle,
    state: State<'_, AppState>,
) -> CmdResult<Option<SourceList>> {
    let Some(picked) = app
        .dialog()
        .file()
        .set_title("Choose a card data folder")
        .blocking_pick_folder()
    else {
        return Ok(None);
    };
    let dir = picked.into_path().map_err(|e| e.to_string())?;
    if !sources::looks_like_data(&dir) {
        return Err(format!(
            "{} contains no card data (expected <lang>/<book>/<type>/*.yaml).",
            dir.display()
        ));
    }
    let mut settings = sources::load_settings(&app);
    if !settings.custom_sources.contains(&dir) {
        settings.custom_sources.push(dir.clone());
    }
    let id = format!("custom:{}", dir.display());
    settings.data_source = Some(id.clone());
    sources::save_settings(&app, &settings)?;
    *state.data_dir.lock().unwrap() = dir;
    Ok(Some(source_list(&app, &state)))
}

/// Forget a folder added with `add_data_source` (the files are not touched).
#[tauri::command]
fn remove_data_source(
    app: AppHandle,
    state: State<'_, AppState>,
    id: String,
) -> CmdResult<SourceList> {
    let path = id
        .strip_prefix("custom:")
        .ok_or("Only added folders can be removed.")?;
    let mut settings = sources::load_settings(&app);
    settings.custom_sources.retain(|p| p != Path::new(path));
    if settings.data_source.as_deref() == Some(id.as_str()) {
        settings.data_source = None;
    }
    sources::save_settings(&app, &settings)?;
    let list = sources::discover(&app, &settings);
    if let Some(src) = sources::active(&list, &settings) {
        *state.data_dir.lock().unwrap() = PathBuf::from(&src.path);
    }
    Ok(source_list(&app, &state))
}

/// Open the folder where dataset installers put their data (creating it).
#[tauri::command]
fn open_datasets_folder(app: AppHandle) -> CmdResult<()> {
    let dir = sources::datasets_dir(&app).ok_or("No data directory available")?;
    std::fs::create_dir_all(&dir).map_err(|e| format!("{}: {e}", dir.display()))?;
    app.opener()
        .open_path(dir.display().to_string(), None::<&str>)
        .map_err(|e| e.to_string())
}

// ── Setup ────────────────────────────────────────────────────────────────────

fn resolve_data_dir(app: &AppHandle) -> PathBuf {
    let settings = sources::load_settings(app);
    let list = sources::discover(app, &settings);
    sources::active(&list, &settings)
        .map(|s| PathBuf::from(&s.path))
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
                data_dir: Mutex::new(resolve_data_dir(app.handle())),
                last_dir: Mutex::new(
                    initial_deck
                        .as_ref()
                        .and_then(|p| p.parent().map(Path::to_path_buf))
                        .or_else(|| sources::load_settings(app.handle()).last_dir),
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
            generate_pdf,
            data_sources,
            set_data_source,
            add_data_source,
            remove_data_source,
            open_datasets_folder
        ])
        .run(tauri::generate_context!())
        .expect("error while running DnD Cards");
}

#[cfg(test)]
mod tests {
    use super::*;
    use dnd_cards_core::models::Language;

    fn card(card_type: &str, level: Option<i64>, typ: Option<&str>) -> CardData {
        CardData {
            id: "x".into(),
            card_type: card_type.into(),
            template: None,
            name: "X".into(),
            lang: Language::De,
            level,
            school: None,
            casting_time: None,
            range: None,
            components: None,
            duration: None,
            typ: typ.map(Into::into),
            description: "d".into(),
            edition: None,
            source_book: None,
            class_name: None,
            subclass: None,
        }
    }

    #[test]
    fn filter_level_uses_level_or_feat_prerequisite() {
        assert_eq!(filter_level(&card("spell", Some(0), None)), Some(0));
        assert_eq!(
            filter_level(&card("class_feature", Some(17), None)),
            Some(17)
        );
        assert_eq!(filter_level(&card("rule", None, None)), None);
        let general = "Allgemeines Talent (Voraussetzung: min. 4. Stufe, min. Stärke 13)";
        assert_eq!(filter_level(&card("talent", None, Some(general))), Some(4));
        let epic = "Epische-Gabe-Talent (Voraussetzung: min.19. Stufe)";
        assert_eq!(filter_level(&card("talent", None, Some(epic))), Some(19));
        assert_eq!(
            filter_level(&card("talent", None, Some("Herkunftstalent"))),
            Some(1)
        );
    }
}

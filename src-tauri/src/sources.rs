//! Card data sources: the SRD data bundled with the app, datasets installed
//! by separate installers, folders added by the user and `$DND_CARDS_DATA`.
//!
//! A source is a data directory (`<lang>/<book>/<type>/*.yaml`). An optional
//! `dataset.json` in its root gives it a display name:
//! `{ "name": "Spielerhandbuch 2024", "description": "…" }`.
//!
//! Installed datasets live in `<app data dir>/datasets/<folder>/`, e.g.
//! `%APPDATA%\io.github.dnd-cards\datasets\phb-2024` on Windows.

use std::path::{Path, PathBuf};

use dnd_cards_core::config;
use serde::{Deserialize, Serialize};
use tauri::{AppHandle, Manager};

pub const BUNDLED: &str = "bundled";
pub const ENV: &str = "env";
const SETTINGS_FILE: &str = "settings.json";

#[derive(Debug, Clone, Serialize)]
pub struct DataSource {
    /// Stable id: `bundled`, `env`, `dataset:<folder>` or `custom:<path>`.
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub path: String,
    /// `bundled`, `installed`, `custom` or `env`.
    pub kind: &'static str,
}

#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct Settings {
    /// Id of the selected source; `None` = default (env, else bundled).
    #[serde(default)]
    pub data_source: Option<String>,
    /// Folders added with "Add folder…".
    #[serde(default)]
    pub custom_sources: Vec<PathBuf>,
    /// Folder of the last deck / PDF opened or saved.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_dir: Option<PathBuf>,
}

#[derive(Deserialize)]
struct Manifest {
    name: Option<String>,
    description: Option<String>,
}

fn manifest(dir: &Path) -> Option<Manifest> {
    let text = std::fs::read_to_string(dir.join("dataset.json")).ok()?;
    serde_json::from_str(text.trim_start_matches('\u{feff}')).ok()
}

/// A directory looks like card data if it has YAML files in `<lang>/<book>/<type>/`.
pub fn looks_like_data(dir: &Path) -> bool {
    dir.is_dir()
        && walkdir::WalkDir::new(dir)
            .min_depth(2)
            .max_depth(5)
            .into_iter()
            .flatten()
            .any(|e| {
                e.file_type().is_file()
                    && e.path().extension().and_then(|x| x.to_str()) == Some("yaml")
            })
}

fn source(id: String, dir: &Path, kind: &'static str, fallback_name: String) -> DataSource {
    let m = manifest(dir);
    DataSource {
        id,
        name: m
            .as_ref()
            .and_then(|m| m.name.clone())
            .unwrap_or(fallback_name),
        description: m.and_then(|m| m.description),
        path: dir.display().to_string(),
        kind,
    }
}

pub fn datasets_dir(app: &AppHandle) -> Option<PathBuf> {
    app.path().app_data_dir().ok().map(|d| d.join("datasets"))
}

fn settings_path(app: &AppHandle) -> Option<PathBuf> {
    app.path()
        .app_config_dir()
        .ok()
        .map(|d| d.join(SETTINGS_FILE))
}

pub fn load_settings(app: &AppHandle) -> Settings {
    settings_path(app)
        .and_then(|p| std::fs::read_to_string(p).ok())
        // tolerate a UTF-8 BOM (Notepad, PowerShell)
        .and_then(|t| serde_json::from_str(t.trim_start_matches('\u{feff}')).ok())
        .unwrap_or_default()
}

pub fn save_settings(app: &AppHandle, settings: &Settings) -> Result<(), String> {
    let path = settings_path(app).ok_or("No configuration directory available")?;
    if let Some(dir) = path.parent() {
        std::fs::create_dir_all(dir).map_err(|e| format!("{}: {e}", dir.display()))?;
    }
    let text = serde_json::to_string_pretty(settings).map_err(|e| e.to_string())?;
    std::fs::write(&path, text).map_err(|e| format!("{}: {e}", path.display()))
}

fn bundled_dir(app: &AppHandle) -> Option<PathBuf> {
    app.path()
        .resource_dir()
        .ok()
        .map(|d| d.join("data"))
        .filter(|d| d.is_dir())
        // development builds: ./data or data/ next to the executable
        .or_else(config::find_default_data_dir)
}

/// All available sources, in menu order.
pub fn discover(app: &AppHandle, settings: &Settings) -> Vec<DataSource> {
    let mut out = Vec::new();
    if let Some(p) = std::env::var_os("DND_CARDS_DATA").map(PathBuf::from) {
        out.push(source(ENV.into(), &p, "env", "$DND_CARDS_DATA".into()));
    }
    if let Some(dir) = bundled_dir(app) {
        out.push(source(
            BUNDLED.into(),
            &dir,
            "bundled",
            "SRD (mitgeliefert)".into(),
        ));
    }
    if let Some(root) = datasets_dir(app) {
        let mut dirs: Vec<PathBuf> = std::fs::read_dir(&root)
            .into_iter()
            .flatten()
            .flatten()
            .map(|e| e.path())
            .filter(|p| looks_like_data(p))
            .collect();
        dirs.sort();
        for d in dirs {
            let folder = d
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .into_owned();
            out.push(source(format!("dataset:{folder}"), &d, "installed", folder));
        }
    }
    for d in &settings.custom_sources {
        let name = d
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_else(|| d.display().to_string());
        out.push(source(format!("custom:{}", d.display()), d, "custom", name));
    }
    out
}

/// The source to use: the saved choice if it still exists, else the first one
/// (`$DND_CARDS_DATA` if set, otherwise the bundled SRD).
pub fn active<'a>(sources: &'a [DataSource], settings: &Settings) -> Option<&'a DataSource> {
    settings
        .data_source
        .as_deref()
        .and_then(|id| sources.iter().find(|s| s.id == id))
        .or_else(|| sources.first())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_card_data() {
        let d = tempfile_dir();
        assert!(!looks_like_data(&d));
        let spells = d.join("de").join("Buch").join("spells");
        std::fs::create_dir_all(&spells).unwrap();
        assert!(!looks_like_data(&d));
        std::fs::write(spells.join("feuerball.yaml"), "").unwrap();
        assert!(looks_like_data(&d));
        std::fs::remove_dir_all(&d).unwrap();
    }

    fn tempfile_dir() -> PathBuf {
        let d = std::env::temp_dir().join(format!("dnd-cards-src-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&d);
        std::fs::create_dir_all(&d).unwrap();
        d
    }
}

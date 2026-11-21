//! Data-store discovery: no YAML is parsed, the card type is the parent
//! directory name and the language is the first path component.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CardRef {
    pub path: PathBuf,
    /// Immediate parent directory, e.g. `spells`.
    pub card_type: String,
    /// First directory below the data root, e.g. `de`.
    pub lang: String,
}

/// Recursively index every `*.yaml` under `data_dir`.
/// Keys are `{card_type}/{stem}`, e.g. `spells/feuerball`.
pub fn scan_cards(data_dir: &Path) -> BTreeMap<String, CardRef> {
    let mut out = BTreeMap::new();
    let walker = walkdir::WalkDir::new(data_dir)
        .sort_by_file_name()
        .into_iter();
    for entry in walker.filter_map(|e| e.ok()) {
        let path = entry.path();
        if !entry.file_type().is_file() || path.extension().and_then(|e| e.to_str()) != Some("yaml")
        {
            continue;
        }
        let (Some(stem), Some(parent)) =
            (path.file_stem(), path.parent().and_then(|p| p.file_name()))
        else {
            continue;
        };
        let card_type = parent.to_string_lossy().into_owned();
        let lang = path
            .strip_prefix(data_dir)
            .ok()
            .and_then(|rel| rel.components().next())
            .filter(|_| path.parent() != Some(data_dir))
            .map(|c| c.as_os_str().to_string_lossy().into_owned())
            .unwrap_or_else(|| "?".into());
        let key = format!("{card_type}/{}", stem.to_string_lossy());
        out.insert(
            key,
            CardRef {
                path: path.to_path_buf(),
                card_type,
                lang,
            },
        );
    }
    out
}

/// Sorted first-level subdirectories of `data_dir` (language codes).
pub fn discover_languages(data_dir: &Path) -> Vec<String> {
    let mut langs: Vec<String> = std::fs::read_dir(data_dir)
        .into_iter()
        .flatten()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().map(|t| t.is_dir()).unwrap_or(false))
        .map(|e| e.file_name().to_string_lossy().into_owned())
        .collect();
    langs.sort();
    langs
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn indexes_by_parent_dir_and_stem() {
        let d = tempfile::tempdir().unwrap();
        let spells = d.path().join("de/SRD 5.2/spells");
        let rules = d.path().join("de/SRD 5.2/rules");
        fs::create_dir_all(&spells).unwrap();
        fs::create_dir_all(&rules).unwrap();
        fs::write(spells.join("feuerball.yaml"), "").unwrap();
        fs::write(rules.join("abenteuer.yaml"), "").unwrap();
        fs::write(rules.join("notes.txt"), "").unwrap();

        let idx = scan_cards(d.path());
        assert_eq!(idx.len(), 2);
        let r = &idx["spells/feuerball"];
        assert_eq!(r.card_type, "spells");
        assert_eq!(r.lang, "de");
        assert!(idx.contains_key("rules/abenteuer"));
        assert_eq!(discover_languages(d.path()), ["de"]);
    }

    #[test]
    fn missing_dir_is_empty() {
        assert!(scan_cards(Path::new("does/not/exist")).is_empty());
    }
}

//! YAML parsing + validation for card and deck files.

use std::path::Path;

use serde::de::DeserializeOwned;

use crate::error::{Error, Result};
use crate::models::{CardData, DeckProfile};

fn read(path: &Path) -> Result<String> {
    std::fs::read_to_string(path).map_err(|e| Error::YamlParse(format!("{}: {e}", path.display())))
}

/// Parse `text` as a YAML mapping, then deserialize it into `T`.
/// Syntax errors → `YamlParse` (with line), schema errors → `Validation`.
fn parse<T: DeserializeOwned>(path: &Path, text: &str) -> Result<T> {
    let value: serde_yaml_ng::Value = serde_yaml_ng::from_str(text).map_err(|e| {
        let line = e.location().map(|l| l.line()).unwrap_or(0);
        Error::YamlParse(format!(
            "{}: YAML syntax error at line {line}: {e}",
            path.display()
        ))
    })?;
    if !value.is_mapping() {
        return Err(Error::YamlParse(format!(
            "{}: YAML file is empty or does not contain a mapping",
            path.display()
        )));
    }
    serde_yaml_ng::from_value(value)
        .map_err(|e| Error::Validation(format!("{}: {e}", path.display())))
}

pub fn load_card(path: &Path) -> Result<CardData> {
    let mut card: CardData = parse(path, &read(path)?)?;
    if card.template.is_none() && card.card_type == "class_feature" {
        card.template = Some("class-feature-v1".into());
    }
    Ok(card)
}

pub fn load_deck(path: &Path) -> Result<DeckProfile> {
    parse(path, &read(path)?)
}

/// Write a deck profile as YAML (UTF-8, block style, insertion order kept).
pub fn save_deck(path: &Path, deck: &DeckProfile) -> Result<()> {
    let yaml = serde_yaml_ng::to_string(deck).map_err(|e| Error::Generation(e.to_string()))?;
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)
                .map_err(|e| Error::Generation(format!("{}: {e}", parent.display())))?;
        }
    }
    std::fs::write(path, yaml).map_err(|e| Error::Generation(format!("{}: {e}", path.display())))
}

/// Read only the `name` field of a card (fast path for listings).
pub fn load_name(path: &Path) -> String {
    #[derive(serde::Deserialize)]
    struct NameOnly {
        name: Option<serde_yaml_ng::Value>,
    }
    let stem = || {
        path.file_stem()
            .map(|s| s.to_string_lossy().into_owned())
            .unwrap_or_default()
    };
    std::fs::read_to_string(path)
        .ok()
        .and_then(|t| serde_yaml_ng::from_str::<NameOnly>(&t).ok())
        .and_then(|n| match n.name? {
            serde_yaml_ng::Value::String(s) => Some(s),
            other => serde_yaml_ng::to_string(&other)
                .ok()
                .map(|s| s.trim().to_string()),
        })
        .unwrap_or_else(stem)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::Language;
    use std::fs;

    fn write(dir: &Path, name: &str, body: &str) -> std::path::PathBuf {
        let p = dir.join(name);
        fs::write(&p, body).unwrap();
        p
    }

    const SPELL: &str = "id: fireball\ntype: spell\ntemplate: zauber-v1\nname: Fireball\nlang: en\nlevel: 3\nschool: Evocation\ncasting_time: 1 action\nrange: 150 ft\ncomponents: V, S, M\nduration: Instantaneous\ndescription: A bright streak flashes.\nedition: 5e\nsource_book: SRD 5.1\n";

    #[test]
    fn loads_valid_card() {
        let d = tempfile::tempdir().unwrap();
        let c = load_card(&write(d.path(), "fireball.yaml", SPELL)).unwrap();
        assert_eq!(c.id, "fireball");
        assert_eq!(c.card_type, "spell");
        assert_eq!(c.template.as_deref(), Some("zauber-v1"));
        assert_eq!(c.lang, Language::En);
        assert_eq!(c.level, Some(3));
        assert_eq!(c.range.as_deref(), Some("150 ft"));
        assert!(c.description.contains("streak"));
    }

    #[test]
    fn missing_description_is_validation_error() {
        let d = tempfile::tempdir().unwrap();
        let p = write(
            d.path(),
            "x.yaml",
            "id: x\ntype: spell\nname: X\nlang: de\n",
        );
        let err = load_card(&p).unwrap_err();
        assert!(matches!(err, Error::Validation(_)));
        let msg = err.to_string();
        assert!(msg.contains("description"), "{msg}");
        assert!(msg.contains(&p.display().to_string()));
    }

    #[test]
    fn malformed_yaml_reports_line() {
        let d = tempfile::tempdir().unwrap();
        let p = write(d.path(), "bad.yaml", "id: x\nname: [unclosed\n");
        let err = load_card(&p).unwrap_err();
        assert!(matches!(err, Error::YamlParse(_)));
        assert!(err.to_string().contains("line"));
        assert!(err.to_string().contains("bad.yaml"));
    }

    #[test]
    fn empty_and_non_mapping_rejected() {
        let d = tempfile::tempdir().unwrap();
        let e = load_card(&write(d.path(), "e.yaml", "")).unwrap_err();
        assert!(e.to_string().to_lowercase().contains("empty"));
        let e = load_card(&write(d.path(), "l.yaml", "- a\n- b\n")).unwrap_err();
        assert!(e.to_string().contains("mapping"));
    }

    #[test]
    fn invalid_lang_rejected() {
        let d = tempfile::tempdir().unwrap();
        let p = write(
            d.path(),
            "x.yaml",
            "id: x\ntype: spell\nname: X\nlang: fr\ndescription: d\n",
        );
        assert!(matches!(load_card(&p).unwrap_err(), Error::Validation(_)));
    }

    #[test]
    fn class_feature_default_template_and_alias() {
        let d = tempfile::tempdir().unwrap();
        let p = write(
            d.path(),
            "b.yaml",
            "id: b\ntype: class_feature\nclass: Barbar\nlang: de\nlevel: 1\nname: Kampfrausch\ndescription: d\n",
        );
        let c = load_card(&p).unwrap();
        assert_eq!(c.template.as_deref(), Some("class-feature-v1"));
        assert_eq!(c.class_name.as_deref(), Some("Barbar"));
        assert_eq!(c.level, Some(1));
    }

    #[test]
    fn numeric_text_fields_accepted() {
        let d = tempfile::tempdir().unwrap();
        let p = write(
            d.path(),
            "x.yaml",
            "id: 42\ntype: rule\nname: 7\nlang: de\ndescription: 1.5\n",
        );
        let c = load_card(&p).unwrap();
        assert_eq!(c.id, "42");
        assert_eq!(c.description, "1.5");
    }

    #[test]
    fn deck_roundtrip_preserves_order() {
        let d = tempfile::tempdir().unwrap();
        let p = write(
            d.path(),
            "deck.yaml",
            "name: Multi Deck\ncards:\n  spells/magisches-geschoss: 2\n  spells/feuerball: 1\n",
        );
        let deck = load_deck(&p).unwrap();
        assert_eq!(deck.name, "Multi Deck");
        let keys: Vec<_> = deck.cards.keys().cloned().collect();
        assert_eq!(keys, ["spells/magisches-geschoss", "spells/feuerball"]);
        assert_eq!(deck.cards["spells/magisches-geschoss"], 2);

        let out = d.path().join("sub/out.yaml");
        save_deck(&out, &deck).unwrap();
        assert_eq!(load_deck(&out).unwrap(), deck);
    }

    #[test]
    fn deck_missing_name_rejected() {
        let d = tempfile::tempdir().unwrap();
        let p = write(d.path(), "deck.yaml", "cards:\n  spells/x: 1\n");
        let err = load_deck(&p).unwrap_err();
        assert!(matches!(err, Error::Validation(_)));
        assert!(err.to_string().contains("name"));
        assert!(err.to_string().contains(&p.display().to_string()));
    }

    #[test]
    fn deck_without_cards_is_empty() {
        let d = tempfile::tempdir().unwrap();
        let p = write(d.path(), "deck.yaml", "name: Leer\ncards:\n");
        assert!(load_deck(&p).unwrap().cards.is_empty());
    }

    #[test]
    fn load_name_falls_back_to_stem() {
        let d = tempfile::tempdir().unwrap();
        assert_eq!(
            load_name(&write(d.path(), "a.yaml", "name: Zauber\n")),
            "Zauber"
        );
        assert_eq!(load_name(&write(d.path(), "b-c.yaml", "id: x\n")), "b-c");
    }
}

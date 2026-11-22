//! Core library for dnd-cards: card data model, data-store scanning,
//! deck profiles and print-ready PDF composition.

pub mod composer;
pub mod config;
pub mod error;
pub mod layout;
pub mod loader;
pub mod models;
pub mod scanner;
pub mod text;

mod metrics;
mod pdf;

pub use composer::{compose_pdf, compose_pdf_duplex};
pub use error::{Error, Result};
pub use layout::{layout_info, printed_count, LayoutInfo};
pub use loader::{load_card, load_deck, save_deck};
pub use models::{CardData, DeckProfile, Language};
pub use scanner::{scan_cards, CardRef};

use std::path::Path;

/// Resolve every entry of a deck against the card index and load the cards,
/// repeating each one `quantity` times (deck order is preserved).
pub fn resolve_deck(
    deck: &DeckProfile,
    index: &std::collections::BTreeMap<String, CardRef>,
    deck_label: &str,
) -> Result<Vec<CardData>> {
    let mut cards = Vec::new();
    for (key, &qty) in &deck.cards {
        let card_ref = index.get(key).ok_or_else(|| {
            Error::CardNotFound(format!("Card not found: {key} (deck: {deck_label})"))
        })?;
        let card = load_card(&card_ref.path)?;
        cards.extend(std::iter::repeat_n(card, qty as usize));
    }
    Ok(cards)
}

/// Print order of card types; unknown types come after these, alphabetically.
const TYPE_ORDER: &[&str] = &[
    "class_feature",
    "species_trait",
    "spell",
    "talent",
    "rule",
    "monster",
];

/// Sort cards for printing: by type (see [`TYPE_ORDER`]), then level (cards
/// without a level last), then class, then species (species traits, whose
/// `typ` names the species), then name. Copies stay together.
pub fn sort_cards(cards: &mut [CardData]) {
    fn type_rank(t: &str) -> usize {
        TYPE_ORDER
            .iter()
            .position(|&x| x == t)
            .unwrap_or(TYPE_ORDER.len())
    }
    fn fold(s: &str) -> String {
        s.to_lowercase()
            .replace('ä', "a")
            .replace('ö', "o")
            .replace('ü', "u")
            .replace('ß', "ss")
    }
    cards.sort_by_cached_key(|c| {
        (
            type_rank(&c.card_type),
            c.card_type.clone(),
            c.level.is_none(),
            c.level,
            c.class_name.as_deref().map(fold),
            (c.card_type == "species_trait")
                .then(|| c.typ.as_deref().map(fold))
                .flatten(),
            fold(&c.name),
        )
    });
}

/// Compose `cards` and write the PDF to `out`, creating parent directories.
pub fn write_pdf(cards: &[CardData], out: &Path, duplex: bool) -> Result<()> {
    let bytes = if duplex {
        compose_pdf_duplex(cards)
    } else {
        compose_pdf(cards)
    };
    if let Some(parent) = out.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)
                .map_err(|e| Error::Generation(format!("{}: {e}", parent.display())))?;
        }
    }
    std::fs::write(out, bytes).map_err(|e| Error::Generation(format!("{}: {e}", out.display())))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn card(card_type: &str, level: Option<i64>, name: &str) -> CardData {
        CardData {
            id: name.to_lowercase(),
            card_type: card_type.into(),
            template: None,
            name: name.into(),
            lang: Language::De,
            level,
            school: None,
            casting_time: None,
            range: None,
            components: None,
            duration: None,
            typ: None,
            description: "x".into(),
            edition: None,
            source_book: None,
            class_name: None,
            subclass: None,
        }
    }

    fn species(typ: &str, name: &str) -> CardData {
        CardData {
            typ: Some(typ.into()),
            ..card("species_trait", None, name)
        }
    }

    #[test]
    fn sorts_by_type_then_level_then_name() {
        let mut cards = vec![
            card("rule", None, "Vorteil"),
            card("spell", Some(3), "Feuerball"),
            card("talent", None, "Zäh"),
            card("spell", Some(0), "Widerstand"),
            card("custom", None, "Eigenes"),
            card("class_feature", Some(2), "Wildgestalt"),
            card("spell", Some(0), "Ärger"),
            card("class_feature", Some(1), "Urtümliche Ordnung"),
            species("Zwerg", "Dunkelsicht (Zwerg)"),
            species("Elf · Elfische Abstammung", "Drow (Elf)"),
            species("Elf", "Trance (Elf)"),
        ];
        sort_cards(&mut cards);
        let names: Vec<_> = cards.iter().map(|c| c.name.as_str()).collect();
        assert_eq!(
            names,
            [
                "Urtümliche Ordnung",
                "Wildgestalt",
                "Trance (Elf)",
                "Drow (Elf)",
                "Dunkelsicht (Zwerg)",
                "Ärger",
                "Widerstand",
                "Feuerball",
                "Zäh",
                "Vorteil",
                "Eigenes",
            ]
        );
    }
}

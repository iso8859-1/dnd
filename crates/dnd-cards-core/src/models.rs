use indexmap::IndexMap;
use serde::{Deserialize, Deserializer, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Language {
    De,
    En,
}

impl Language {
    pub fn as_str(self) -> &'static str {
        match self {
            Language::De => "de",
            Language::En => "en",
        }
    }
}

/// Parsed and validated card data from a YAML file.
/// Unknown keys (e.g. the monster stat-block fields) are ignored.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CardData {
    #[serde(deserialize_with = "scalar_string")]
    pub id: String,
    #[serde(rename = "type", deserialize_with = "scalar_string")]
    pub card_type: String,
    /// Legacy template name; kept for data compatibility, not used for layout.
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub template: Option<String>,
    #[serde(deserialize_with = "scalar_string")]
    pub name: String,
    pub lang: Language,
    // Spell-specific
    #[serde(default)]
    pub level: Option<i64>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub school: Option<String>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub casting_time: Option<String>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub range: Option<String>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub components: Option<String>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub duration: Option<String>,
    /// Talent category string.
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub typ: Option<String>,
    /// Required for every card type.
    #[serde(deserialize_with = "scalar_string")]
    pub description: String,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub edition: Option<String>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub source_book: Option<String>,
    // Class feature fields
    #[serde(rename = "class", default, deserialize_with = "opt_scalar_string")]
    pub class_name: Option<String>,
    #[serde(default, deserialize_with = "opt_scalar_string")]
    pub subclass: Option<String>,
}

/// A deck profile: a name plus an ordered `card_key → quantity` map.
/// On disk: `name: ...` and `cards: { "spells/feuerball": 2, ... }`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DeckProfile {
    pub name: String,
    #[serde(default, deserialize_with = "null_as_default")]
    pub cards: IndexMap<String, u32>,
}

// ── Lenient scalar handling ──────────────────────────────────────────────────
// YAML happily types `range: 18` or `ub: +4` as numbers; accept any scalar
// for text fields so hand-edited data doesn't fail on a technicality.

fn scalar_to_string<E: serde::de::Error>(v: serde_yaml_ng::Value) -> Result<Option<String>, E> {
    use serde_yaml_ng::Value;
    match v {
        Value::Null => Ok(None),
        Value::String(s) => Ok(Some(s)),
        Value::Number(n) => Ok(Some(n.to_string())),
        Value::Bool(b) => Ok(Some(b.to_string())),
        _ => Err(E::custom("expected a text value")),
    }
}

fn scalar_string<'de, D: Deserializer<'de>>(d: D) -> Result<String, D::Error> {
    let v = serde_yaml_ng::Value::deserialize(d)?;
    scalar_to_string(v)?.ok_or_else(|| serde::de::Error::custom("must not be empty"))
}

fn opt_scalar_string<'de, D: Deserializer<'de>>(d: D) -> Result<Option<String>, D::Error> {
    let v = serde_yaml_ng::Value::deserialize(d)?;
    scalar_to_string(v)
}

fn null_as_default<'de, D, T>(d: D) -> Result<T, D::Error>
where
    D: Deserializer<'de>,
    T: Deserialize<'de> + Default,
{
    Ok(Option::<T>::deserialize(d)?.unwrap_or_default())
}

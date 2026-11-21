//! Small text helpers shared by the CLI and the desktop app.

/// Lowercase slug: transliterate German umlauts, whitespace → hyphen,
/// strip everything else that isn't `[a-z0-9-]`.
pub fn slugify(name: &str) -> String {
    let mut s = String::with_capacity(name.len());
    for ch in name.chars() {
        match ch {
            'ä' | 'Ä' => s.push('a'),
            'ö' | 'Ö' => s.push('o'),
            'ü' | 'Ü' => s.push('u'),
            'ß' => s.push_str("ss"),
            c if c.is_ascii_alphanumeric() => s.push(c.to_ascii_lowercase()),
            c if c.is_whitespace() || c == '-' => s.push('-'),
            _ => {}
        }
    }
    s.split('-')
        .filter(|p| !p.is_empty())
        .collect::<Vec<_>>()
        .join("-")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn slugs() {
        assert_eq!(slugify("Feuerball"), "feuerball");
        assert_eq!(slugify("Magisches Geschoss"), "magisches-geschoss");
        assert_eq!(slugify("Größe ändern"), "grosse-andern");
        assert_eq!(slugify("  Spaß -- (Test)!  "), "spass-test");
        assert_eq!(slugify("Mein Deck 2"), "mein-deck-2");
    }
}

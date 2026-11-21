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

/// Greedy word wrap by character count (matches the original layout engine).
pub fn wrap(text: &str, max_chars: usize) -> Vec<String> {
    let mut lines = Vec::new();
    let mut current = String::new();
    for word in text.split_whitespace() {
        if current.is_empty() {
            current.push_str(word);
        } else if current.chars().count() + 1 + word.chars().count() <= max_chars {
            current.push(' ');
            current.push_str(word);
        } else {
            lines.push(std::mem::take(&mut current));
            current.push_str(word);
        }
    }
    if !current.is_empty() || lines.is_empty() {
        lines.push(current);
    }
    lines
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

    #[test]
    fn wrapping() {
        assert_eq!(wrap("", 10), [""]);
        assert_eq!(wrap("aa bb cc", 5), ["aa bb", "cc"]);
        assert_eq!(
            wrap("averyveryverylongword x", 5),
            ["averyveryverylongword", "x"]
        );
        assert_eq!(wrap("äö üß", 5), ["äö üß"]);
    }
}

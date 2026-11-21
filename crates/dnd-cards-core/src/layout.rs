//! Text measuring, wrapping and per-card layout planning.
//!
//! Every card face is 63×88mm in both print modes, so a card's layout is
//! planned once, independent of fold-strip or duplex output. Planning tries,
//! in order, until the description fits:
//!
//! 1. front only at 6pt
//! 2. front only at 5.5pt
//! 3. front + back at 6pt
//! 4. front + back at 5.5pt
//! 5. front + back at 5.5pt, plus follow-on cards ("Name (2/3)") with text on
//!    both faces
//!
//! No text is ever dropped.

use serde::Serialize;

use crate::config::{CARD_FOLDED_HEIGHT_MM, CARD_STRIP_WIDTH_MM};
use crate::metrics;
use crate::models::CardData;
use crate::pdf::{encode_win_ansi, mm, Font, MM_TO_PT};

/// Header band height.
pub(crate) const HEADER_MM: f32 = 7.5;
/// Border stroke: one third of the header height (~7.1pt).
pub(crate) const BORDER_PT: f32 = HEADER_MM * MM_TO_PT / 3.0;
/// Horizontal text inset from the card edge (both sides).
pub(crate) const PAD_MM: f32 = 3.0;

const FIELD_SIZE: f32 = 7.0;
const FIELD_LINE: f32 = 11.0;
const TITLE_MAX: f32 = 9.0;
const TITLE_MIN: f32 = 6.0;

/// Preferred description font size.
pub const BODY_SIZE: f32 = 6.0;
/// Smallest description font size used before spilling onto more faces.
pub const BODY_MIN: f32 = 5.5;

/// Attempts in order: (font size, may use the back face).
const ATTEMPTS: [(f32, bool); 4] = [
    (BODY_SIZE, false),
    (BODY_MIN, false),
    (BODY_SIZE, true),
    (BODY_MIN, true),
];

pub(crate) fn face_w() -> f32 {
    mm(CARD_STRIP_WIDTH_MM)
}

pub(crate) fn face_h() -> f32 {
    mm(CARD_FOLDED_HEIGHT_MM)
}

pub(crate) fn pad() -> f32 {
    mm(PAD_MM)
}

fn text_w() -> f32 {
    face_w() - 2.0 * pad()
}

/// Lowest baseline that clears the border's inner edge.
pub(crate) fn safe_bottom() -> f32 {
    BORDER_PT / 2.0 + 4.0
}

/// Line pitch for body text (8pt at 6pt, as in the original layout).
fn body_line(size: f32) -> f32 {
    size * 4.0 / 3.0
}

pub(crate) fn text_width(font: Font, size: f32, text: &str) -> f32 {
    metrics::width(font, size, &encode_win_ansi(text))
}

/// Greedy word wrap by measured width. Words wider than a line are split.
pub(crate) fn wrap(text: &str, font: Font, size: f32, max_w: f32) -> Vec<String> {
    let fits = |s: &str| text_width(font, size, s) <= max_w;
    let mut lines = Vec::new();
    let mut cur = String::new();
    for word in text.split_whitespace() {
        let candidate = if cur.is_empty() {
            word.to_string()
        } else {
            format!("{cur} {word}")
        };
        if fits(&candidate) {
            cur = candidate;
            continue;
        }
        if !cur.is_empty() {
            lines.push(std::mem::take(&mut cur));
        }
        if fits(word) {
            cur = word.to_string();
        } else {
            for ch in word.chars() {
                cur.push(ch);
                if !fits(&cur) && cur.chars().count() > 1 {
                    let last = cur.pop().unwrap();
                    lines.push(std::mem::take(&mut cur));
                    cur.push(last);
                }
            }
        }
    }
    if !cur.is_empty() || lines.is_empty() {
        lines.push(cur);
    }
    lines
}

/// Largest title size (9pt → 6pt) that fits the header; truncated with `…` at 6pt.
pub(crate) fn fit_title(title: &str) -> (String, f32) {
    let max_w = text_w();
    let mut size = TITLE_MAX;
    while size >= TITLE_MIN {
        if text_width(Font::HelveticaBold, size, title) <= max_w {
            return (title.to_string(), size);
        }
        size -= 0.5;
    }
    let mut chars: Vec<char> = title.chars().collect();
    while !chars.is_empty() {
        chars.pop();
        let t: String = chars.iter().collect::<String>().trim_end().to_string() + "…";
        if text_width(Font::HelveticaBold, TITLE_MIN, &t) <= max_w {
            return (t, TITLE_MIN);
        }
    }
    ("…".into(), TITLE_MIN)
}

// ── Plan ─────────────────────────────────────────────────────────────────────

/// A positioned line of text; `y` is the baseline relative to the face bottom,
/// x is always the left padding.
#[derive(Debug, Clone, PartialEq)]
pub(crate) struct Line {
    pub font: Font,
    pub size: f32,
    pub y: f32,
    pub text: String,
}

/// One physical card (front + back face).
#[derive(Debug, Clone)]
pub(crate) struct PrintCard<'a> {
    pub card: &'a CardData,
    pub title: String,
    pub front: Vec<Line>,
    /// Source line, printed on the main front only.
    pub source: Option<&'a str>,
    /// Text on the back; `None` → type icon.
    pub back: Option<Vec<Line>>,
    pub body_size: f32,
}

/// How a card will be printed.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct LayoutInfo {
    /// Description font size in points.
    pub font_size: f32,
    /// Description continues on the back face.
    pub uses_back: bool,
    /// Physical cards needed (1 unless follow-on cards are required).
    pub cards: usize,
}

impl LayoutInfo {
    /// True when the card prints as a single front-only card at full size.
    pub fn is_default(&self) -> bool {
        self.cards == 1 && !self.uses_back && self.font_size >= BODY_SIZE
    }
}

fn source(card: &CardData) -> Option<&str> {
    card.source_book.as_deref().filter(|s| !s.is_empty())
}

fn opt(s: &Option<String>) -> &str {
    s.as_deref().unwrap_or("")
}

/// Header lines of the main front face for `card`, plus the y from which the
/// description starts and the lowest allowed description baseline.
fn main_block(card: &CardData, body_size: f32) -> (Vec<Line>, f32, f32) {
    let max_w = text_w();
    let floor = safe_bottom()
        + if source(card).is_some() {
            body_line(body_size)
        } else {
            0.0
        };
    let mut y = face_h() - mm(HEADER_MM);
    let mut lines = Vec::new();
    let mut push = |font, y: f32, text: String| {
        lines.push(Line {
            font,
            size: FIELD_SIZE,
            y,
            text,
        })
    };

    match card.card_type.as_str() {
        "spell" => {
            y -= 10.0;
            let level = card.level.map(|l| l.to_string()).unwrap_or_default();
            push(
                Font::Helvetica,
                y,
                format!("Stufe {level} · {}", opt(&card.school)),
            );
            let fields = [
                ("Zeit", &card.casting_time),
                ("Reichweite", &card.range),
                ("Komp.", &card.components),
                ("Dauer", &card.duration),
            ];
            for (label, value) in fields {
                for l in wrap(
                    &format!("{label}: {}", opt(value)),
                    Font::Helvetica,
                    FIELD_SIZE,
                    max_w,
                ) {
                    y -= FIELD_LINE;
                    push(Font::Helvetica, y, l);
                }
            }
            y -= 6.0;
        }
        "class_feature" => {
            let cls = opt(&card.class_name);
            let line = match card.level {
                Some(l) => format!("{cls} · Stufe {l}"),
                None => cls.to_string(),
            };
            y -= 10.0;
            push(Font::HelveticaOblique, y, line);
            if let Some(sub) = card.subclass.as_deref().filter(|s| !s.is_empty()) {
                y -= FIELD_LINE;
                push(Font::HelveticaOblique, y, format!("({sub})"));
            }
            y -= 4.0;
        }
        _ => match card.typ.as_deref().filter(|s| !s.is_empty()) {
            Some(typ) => {
                y -= 10.0;
                for l in wrap(typ, Font::HelveticaOblique, FIELD_SIZE, max_w) {
                    push(Font::HelveticaOblique, y, l);
                    y -= FIELD_LINE;
                }
                y -= 4.0;
            }
            None => y -= 10.0,
        },
    }
    lines.retain(|l| l.y >= floor);
    (lines, y, floor)
}

/// Start y and floor for a face that carries only body text.
fn text_face() -> (f32, f32) {
    (face_h() - mm(HEADER_MM) - 4.0, safe_bottom())
}

fn capacity(y0: f32, floor: f32, line: f32) -> usize {
    if y0 < floor {
        0
    } else {
        ((y0 - floor) / line + 1e-3).floor() as usize
    }
}

fn place(lines: &[String], y0: f32, size: f32) -> Vec<Line> {
    let step = body_line(size);
    lines
        .iter()
        .enumerate()
        .map(|(i, t)| Line {
            font: Font::Helvetica,
            size,
            y: y0 - step * (i + 1) as f32,
            text: t.clone(),
        })
        .collect()
}

/// Plan the physical card(s) for `card`.
pub(crate) fn plan(card: &CardData) -> Vec<PrintCard<'_>> {
    let (text_y0, text_floor) = text_face();
    let single = |front: Vec<Line>, back: Option<Vec<Line>>, size| PrintCard {
        card,
        title: card.name.clone(),
        front,
        source: source(card),
        back,
        body_size: size,
    };

    for (size, use_back) in ATTEMPTS {
        let (mut front, y0, floor) = main_block(card, size);
        let body = wrap(&card.description, Font::Helvetica, size, text_w());
        let cap = capacity(y0, floor, body_line(size));
        if body.len() <= cap {
            front.extend(place(&body, y0, size));
            return vec![single(front, None, size)];
        }
        let back_cap = capacity(text_y0, text_floor, body_line(size));
        if use_back && body.len() <= cap + back_cap {
            front.extend(place(&body[..cap], y0, size));
            let back = place(&body[cap..], text_y0, size);
            return vec![single(front, Some(back), size)];
        }
    }

    // Follow-on cards at the minimum size.
    let size = BODY_MIN;
    let (mut front, y0, floor) = main_block(card, size);
    let body = wrap(&card.description, Font::Helvetica, size, text_w());
    let cap = capacity(y0, floor, body_line(size));
    let text_cap = capacity(text_y0, text_floor, body_line(size)).max(1);

    front.extend(place(&body[..cap], y0, size));
    let mut rest = body[cap..].chunks(text_cap);
    let back = rest.next().map(|c| place(c, text_y0, size));
    let mut cards = vec![single(front, back, size)];
    while let Some(chunk) = rest.next() {
        cards.push(PrintCard {
            card,
            title: card.name.clone(),
            front: place(chunk, text_y0, size),
            source: None,
            back: rest.next().map(|c| place(c, text_y0, size)),
            body_size: size,
        });
    }
    let n = cards.len();
    for (i, pc) in cards.iter_mut().enumerate() {
        pc.title = format!("{} ({}/{n})", card.name, i + 1);
    }
    cards
}

/// Summarise how `card` will be printed.
pub fn layout_info(card: &CardData) -> LayoutInfo {
    let cards = plan(card);
    LayoutInfo {
        font_size: cards[0].body_size,
        uses_back: cards.iter().any(|c| c.back.is_some()),
        cards: cards.len(),
    }
}

/// Number of physical cards needed to print `cards`.
pub fn printed_count(cards: &[CardData]) -> usize {
    cards.iter().map(|c| plan(c).len()).sum()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::Language;

    pub(crate) fn card(card_type: &str, description: &str) -> CardData {
        CardData {
            id: "x".into(),
            card_type: card_type.into(),
            template: None,
            name: "Feuerball".into(),
            lang: Language::De,
            level: Some(3),
            school: Some("Hervorrufung".into()),
            casting_time: Some("Aktion".into()),
            range: Some("45 m".into()),
            components: Some("V, G, M (eine Kugel aus Fledermausguano und Schwefel)".into()),
            duration: Some("Unmittelbar".into()),
            typ: Some("Allgemeines Talent".into()),
            description: description.into(),
            edition: None,
            source_book: Some("SRD 5.2.1".into()),
            class_name: Some("Barbar".into()),
            subclass: None,
        }
    }

    fn words(n: usize) -> String {
        "Ein heller Strahl schießt aus deinem Finger.".repeat(n)
    }

    fn all_text(cards: &[PrintCard]) -> String {
        cards
            .iter()
            .flat_map(|c| c.front.iter().chain(c.back.iter().flatten()))
            .filter(|l| l.font == Font::Helvetica && l.size < FIELD_SIZE)
            .map(|l| l.text.as_str())
            .collect::<Vec<_>>()
            .join(" ")
    }

    #[test]
    fn wrap_respects_width_and_keeps_words() {
        let text = words(20);
        let lines = wrap(&text, Font::Helvetica, 6.0, 100.0);
        assert!(lines.len() > 1);
        for l in &lines {
            assert!(text_width(Font::Helvetica, 6.0, l) <= 100.0, "{l}");
        }
        assert_eq!(
            lines.join(" "),
            text.split_whitespace().collect::<Vec<_>>().join(" ")
        );
        assert_eq!(wrap("", Font::Helvetica, 6.0, 100.0), [""]);
    }

    #[test]
    fn wrap_splits_overlong_words() {
        let lines = wrap(&"x".repeat(200), Font::Helvetica, 6.0, 50.0);
        assert!(lines.len() > 1);
        assert!(lines
            .iter()
            .all(|l| text_width(Font::Helvetica, 6.0, l) <= 50.0));
        assert_eq!(lines.concat(), "x".repeat(200));
    }

    #[test]
    fn short_card_is_default() {
        let info = layout_info(&card("spell", "Kurz."));
        assert!(info.is_default(), "{info:?}");
    }

    #[test]
    fn escalates_without_losing_text() {
        let mut last = LayoutInfo {
            font_size: BODY_SIZE,
            uses_back: false,
            cards: 1,
        };
        let mut seen_back = false;
        let mut seen_small = false;
        for n in [1, 10, 20, 30, 40, 60, 90, 150] {
            let c = card("spell", &words(n));
            let cards = plan(&c);
            let expected = c
                .description
                .split_whitespace()
                .collect::<Vec<_>>()
                .join(" ");
            assert_eq!(all_text(&cards), expected, "text lost at n={n}");
            let info = layout_info(&c);
            assert!(info.cards >= last.cards);
            seen_back |= info.uses_back;
            seen_small |= info.font_size < BODY_SIZE;
            for (i, pc) in cards.iter().enumerate() {
                for l in pc.front.iter().chain(pc.back.iter().flatten()) {
                    assert!(l.y >= safe_bottom() - 1e-3, "line below border at n={n}");
                }
                if cards.len() > 1 {
                    assert!(pc.title.ends_with(&format!("({}/{})", i + 1, cards.len())));
                }
            }
            last = info;
        }
        assert!(seen_back && seen_small && last.cards > 1, "{last:?}");
    }

    #[test]
    fn title_fits_header() {
        let (t, s) = fit_title("Feuerball");
        assert_eq!((t.as_str(), s), ("Feuerball", 9.0));
        let long = "Pfad des Berserkers: Geistloser Kampfrausch (Barbar) (2/2)";
        let (t, s) = fit_title(long);
        assert!(s < 9.0);
        assert!(text_width(Font::HelveticaBold, s, &t) <= text_w());
        let (t, s) = fit_title(&"Sehr langer Name ".repeat(10));
        assert_eq!(s, TITLE_MIN);
        assert!(t.ends_with('…'));
    }
}

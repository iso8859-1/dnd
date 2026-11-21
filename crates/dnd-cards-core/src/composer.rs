//! Card layout: fold strips (A4 landscape, 4 × 63×176mm) and duplex
//! (A4 portrait, 3×3 faces of 63×88mm, backs mirrored for long-edge flip).

use std::f32::consts::PI;

use crate::config::*;
use crate::models::CardData;
use crate::pdf::{mm, Canvas, Font, Rgb, MM_TO_PT};
use crate::text::wrap;

const WHITE: Rgb = (1.0, 1.0, 1.0);
const BLACK: Rgb = (0.0, 0.0, 0.0);
const GREY_TEXT: Rgb = (0.4, 0.4, 0.4);

/// Header band height.
const HEADER_MM: f32 = 7.5;
/// Border stroke: one third of the header height (~7.1pt).
const BORDER_PT: f32 = HEADER_MM * MM_TO_PT / 3.0;

/// Approximate characters per line inside the usable width (63mm − 2×3mm).
const WRAP_7PT: usize = 40;
const WRAP_6PT: usize = 48;
const LINE_7: f32 = 11.0;
const LINE_6: f32 = 8.0;

const ICON_MM: f32 = 22.0;

fn card_color(card_type: &str) -> Rgb {
    match card_type {
        "spell" => (0.75, 0.62, 0.85),         // pastel violet
        "class_feature" => (0.85, 0.75, 0.55), // warm amber
        _ => (0.62, 0.62, 0.65),               // pastel grey (talent, rule, …)
    }
}

fn darker((r, g, b): Rgb) -> Rgb {
    (r * 0.72, g * 0.72, b * 0.72)
}

fn opt(s: &Option<String>) -> &str {
    s.as_deref().unwrap_or("")
}

fn level_str(card: &CardData) -> String {
    card.level.map(|l| l.to_string()).unwrap_or_default()
}

// ── Public entry points ──────────────────────────────────────────────────────

/// Fold-strip PDF: each card is a 63×176mm strip, front on top, back below
/// (rotated 180°) so it reads correctly after folding at 88mm.
pub fn compose_pdf(cards: &[CardData]) -> Vec<u8> {
    let (page_w, page_h) = (mm(A4_HEIGHT_MM), mm(A4_WIDTH_MM)); // landscape
    let mut c = Canvas::new(page_w, page_h);

    let strip_w = mm(CARD_STRIP_WIDTH_MM);
    let strip_h = mm(CARD_STRIP_HEIGHT_MM);
    let gap = mm(CARD_GAP_MM);
    let n = CARDS_PER_ROW as f32;
    let x_origin = (page_w - (n * strip_w + (n - 1.0) * gap)) / 2.0;
    let y_origin = (page_h - strip_h) / 2.0;

    for (i, card) in cards.iter().enumerate() {
        let pos = i % CARDS_PER_ROW;
        if i > 0 && pos == 0 {
            c.show_page();
        }
        let x = x_origin + pos as f32 * (strip_w + gap);
        draw_strip(&mut c, card, x, y_origin, strip_w, strip_h);
    }
    c.finish()
}

/// Duplex PDF: fronts on odd pages, backs on even pages, no folding needed.
pub fn compose_pdf_duplex(cards: &[CardData]) -> Vec<u8> {
    let layout = DuplexLayout::a4();
    let mut c = Canvas::new(layout.page_w, layout.page_h);
    let per_page = DUPLEX_COLS * DUPLEX_ROWS;

    for (g, group) in cards.chunks(per_page).enumerate() {
        if g > 0 {
            c.show_page();
        }
        for (i, card) in group.iter().enumerate() {
            let (x, y) = layout.slot(i, false);
            draw_front_face(&mut c, card, x, y, layout.face_w, layout.face_h);
        }
        c.show_page();
        for (i, card) in group.iter().enumerate() {
            let (x, y) = layout.slot(i, true);
            draw_back_face(&mut c, card, x, y, layout.face_w, layout.face_h);
        }
    }
    c.finish()
}

struct DuplexLayout {
    page_w: f32,
    page_h: f32,
    face_w: f32,
    face_h: f32,
    gap: f32,
    x_origin: f32,
    y_origin: f32,
}

impl DuplexLayout {
    fn a4() -> Self {
        let (page_w, page_h) = (mm(A4_WIDTH_MM), mm(A4_HEIGHT_MM));
        let face_w = mm(CARD_STRIP_WIDTH_MM);
        let face_h = mm(CARD_FOLDED_HEIGHT_MM);
        let gap = mm(CARD_GAP_MM);
        let (cols, rows) = (DUPLEX_COLS as f32, DUPLEX_ROWS as f32);
        let total_w = cols * face_w + (cols - 1.0) * gap;
        let total_h = rows * face_h + (rows - 1.0) * gap;
        Self {
            page_w,
            page_h,
            face_w,
            face_h,
            gap,
            x_origin: (page_w - total_w) / 2.0,
            y_origin: (page_h - total_h) / 2.0,
        }
    }

    /// Lower-left corner of slot `i`; back pages mirror the column.
    fn slot(&self, i: usize, back: bool) -> (f32, f32) {
        let mut col = i % DUPLEX_COLS;
        if back {
            col = DUPLEX_COLS - 1 - col;
        }
        let row = i / DUPLEX_COLS;
        (
            self.x_origin + col as f32 * (self.face_w + self.gap),
            self.y_origin + row as f32 * (self.face_h + self.gap),
        )
    }
}

// ── Faces ────────────────────────────────────────────────────────────────────

fn fill_header(c: &mut Canvas, x: f32, y_top: f32, w: f32, h: f32, r: f32, color: Rgb) {
    c.fill(color);
    c.round_rect(x, y_top - h, w, h, r, false, true);
    // Square off the bottom corners of the band.
    c.rect(x, y_top - h, w, r, false, true);
}

fn border(c: &mut Canvas, x: f32, y: f32, w: f32, h: f32, r: f32, color: Rgb) {
    c.line_width(BORDER_PT);
    c.stroke_color(color);
    c.round_rect(x, y, w, h, r, true, false);
}

fn draw_title(c: &mut Canvas, card: &CardData, x: f32, face_top: f32) {
    c.fill(WHITE);
    c.set_font(Font::HelveticaBold, 9.0);
    c.draw_string(
        x + mm(3.0),
        face_top - mm(HEADER_MM) / 2.0 - 3.0,
        &card.name,
    );
}

/// Draw `lines` at descending baselines; stop once below `floor`.
fn draw_lines(
    c: &mut Canvas,
    x: f32,
    line_y: &mut f32,
    step: f32,
    floor: f32,
    lines: Vec<String>,
) -> bool {
    for line in lines {
        *line_y -= step;
        if *line_y < floor {
            return false;
        }
        c.draw_string(x, *line_y, &line);
    }
    true
}

/// Card front as a standalone w×h face with its lower-left corner at (x, y).
fn draw_front_face(c: &mut Canvas, card: &CardData, x: f32, y: f32, w: f32, h: f32) {
    let r = mm(CARD_CORNER_RADIUS_MM);
    let pad = mm(3.0);
    let header_h = mm(HEADER_MM);
    let color = card_color(&card.card_type);
    let face_top = y + h;
    let tx = x + pad;

    fill_header(c, x, face_top, w, header_h, r, color);
    border(c, x, y, w, h, r, color);
    draw_title(c, card, x, face_top);
    c.fill(BLACK);

    let safe_bottom = y + BORDER_PT / 2.0 + 4.0;
    let src = card.source_book.as_deref().filter(|s| !s.is_empty());
    let floor = if src.is_some() {
        safe_bottom + LINE_6
    } else {
        safe_bottom
    };
    let mut line_y = face_top - header_h;

    if card.card_type == "spell" {
        c.set_font(Font::Helvetica, 7.0);
        line_y -= 10.0;
        c.draw_string(
            tx,
            line_y,
            &format!("Stufe {} · {}", level_str(card), opt(&card.school)),
        );
        let fields = [
            ("Zeit", &card.casting_time),
            ("Reichweite", &card.range),
            ("Komp.", &card.components),
            ("Dauer", &card.duration),
        ];
        for (label, value) in fields {
            if !draw_lines(
                c,
                tx,
                &mut line_y,
                LINE_7,
                floor,
                wrap(&format!("{label}: {}", opt(value)), WRAP_7PT),
            ) {
                break;
            }
        }
        line_y -= 6.0;
    } else {
        if card.card_type == "class_feature" {
            let cls = opt(&card.class_name);
            let class_line = match card.level {
                Some(l) => format!("{cls} · Stufe {l}"),
                None => cls.to_string(),
            };
            c.set_font(Font::HelveticaOblique, 7.0);
            line_y -= 10.0;
            c.draw_string(tx, line_y, &class_line);
            if let Some(sub) = card.subclass.as_deref().filter(|s| !s.is_empty()) {
                line_y -= LINE_7;
                c.draw_string(tx, line_y, &format!("({sub})"));
            }
        } else if let Some(typ) = card.typ.as_deref().filter(|s| !s.is_empty()) {
            c.set_font(Font::HelveticaOblique, 7.0);
            line_y -= 10.0;
            for tl in wrap(typ, WRAP_7PT) {
                c.draw_string(tx, line_y, &tl);
                line_y -= LINE_7;
                if line_y < floor {
                    break;
                }
            }
        } else {
            line_y -= 6.0;
        }
        line_y -= 4.0;
    }

    c.set_font(Font::Helvetica, 6.0);
    draw_lines(
        c,
        tx,
        &mut line_y,
        LINE_6,
        floor,
        wrap(&card.description, WRAP_6PT),
    );

    if let Some(src) = src {
        c.fill(GREY_TEXT);
        c.draw_string(tx, safe_bottom, src);
        c.fill(BLACK);
    }
}

/// Card back (header + type icon) upright with its lower-left corner at (x, y).
fn draw_back_face(c: &mut Canvas, card: &CardData, x: f32, y: f32, w: f32, h: f32) {
    let r = mm(CARD_CORNER_RADIUS_MM);
    let header_h = mm(HEADER_MM);
    let color = card_color(&card.card_type);

    fill_header(c, x, y + h, w, header_h, r, color);
    border(c, x, y, w, h, r, color);
    draw_title(c, card, x, y + h);
    draw_back_icon(
        c,
        x + w / 2.0,
        y + (h - header_h) / 2.0,
        mm(ICON_MM),
        &card.card_type,
        color,
    );
}

fn draw_strip(c: &mut Canvas, card: &CardData, x: f32, y: f32, w: f32, h: f32) {
    let fold_h = mm(CARD_FOLDED_HEIGHT_MM);
    let color = card_color(&card.card_type);

    // Front: upper half.
    draw_front_face(c, card, x, y + fold_h, w, h - fold_h);

    // Fold edge — double width because both halves' borders stack when folded.
    c.line_width(2.0 * BORDER_PT);
    c.stroke_color(color);
    c.line(x, y + fold_h, x + w, y + fold_h);

    // Dashed fold guide.
    c.line_width(0.25);
    c.dash(Some((3.0, 3.0)));
    c.stroke_color((0.5, 0.5, 0.5));
    c.line(x, y + fold_h, x + w, y + fold_h);
    c.dash(None);
    c.stroke_color(BLACK);

    // Back: lower half, rotated 180° so it reads correctly after folding.
    c.save_state();
    c.translate_rotate_180(x + w, y + fold_h);
    draw_back_face(c, card, 0.0, 0.0, w, fold_h);
    c.restore_state();
}

// ── Icons ────────────────────────────────────────────────────────────────────

fn draw_back_icon(c: &mut Canvas, cx: f32, cy: f32, size: f32, card_type: &str, color: Rgb) {
    match card_type {
        "spell" => spellbook_icon(c, cx, cy, size, color),
        "talent" => shield_icon(c, cx, cy, size, color),
        "class_feature" => sword_icon(c, cx, cy, size, color),
        _ => scroll_icon(c, cx, cy, size, color),
    }
}

/// Four-pointed star with outer radius `r`.
fn sparkle(c: &mut Canvas, cx: f32, cy: f32, r: f32, color: Rgb) {
    let inner = r * 0.38;
    let pts: Vec<(f32, f32)> = (0..8)
        .map(|i| {
            let angle = PI / 4.0 * i as f32 - PI / 2.0;
            let radius = if i % 2 == 0 { r } else { inner };
            (cx + radius * angle.cos(), cy + radius * angle.sin())
        })
        .collect();
    c.fill(color);
    c.polygon(&pts, false, true);
}

fn white_lines(c: &mut Canvas, width: f32, x0: f32, x1: f32, ys: impl IntoIterator<Item = f32>) {
    c.stroke_color(WHITE);
    c.line_width(width);
    for y in ys {
        c.line(x0, y, x1, y);
    }
}

fn spellbook_icon(c: &mut Canvas, cx: f32, cy: f32, size: f32, color: Rgb) {
    let dv = darker(color);
    let (bw, bh) = (size * 0.68, size * 0.82);
    let (bx, by) = (cx - bw / 2.0, cy - bh / 2.0);
    let spine_w = bw * 0.22;

    c.fill(dv);
    c.rect(bx, by, spine_w, bh, false, true);
    c.fill(color);
    c.rect(bx + spine_w, by, bw - spine_w, bh, false, true);

    c.line_width(1.2);
    c.stroke_color(dv);
    c.round_rect(bx, by, bw, bh, size * 0.05, true, false);

    let (lx0, lx1) = (bx + spine_w + bw * 0.07, bx + bw - bw * 0.07);
    white_lines(c, 0.8, lx0, lx1, [0.30, 0.50, 0.70].map(|f| by + bh * f));

    sparkle(c, cx, by + bh + size * 0.20, size * 0.15, color);
}

fn shield_icon(c: &mut Canvas, cx: f32, cy: f32, size: f32, color: Rgb) {
    let dv = darker(color);
    let (sw, sh) = (size * 0.70, size * 0.85);
    let (sx, sy) = (cx - sw / 2.0, cy - sh / 2.0);

    c.fill(color);
    c.stroke_color(dv);
    c.line_width(1.2);
    c.polygon(
        &[
            (sx, sy + sh * 0.55),
            (sx, sy + sh),
            (sx + sw, sy + sh),
            (sx + sw, sy + sh * 0.55),
            (cx, sy),
        ],
        true,
        true,
    );

    c.stroke_color(WHITE);
    c.line_width(1.5);
    let mid_y = sy + sh * 0.72;
    c.line(cx, sy + sh * 0.48, cx, sy + sh * 0.96);
    c.line(sx + sw * 0.22, mid_y, sx + sw * 0.78, mid_y);

    sparkle(c, cx, sy - size * 0.18, size * 0.14, color);
}

fn scroll_icon(c: &mut Canvas, cx: f32, cy: f32, size: f32, color: Rgb) {
    let dv = darker(color);
    let (rw, rh) = (size * 0.68, size * 0.80);
    let roll = size * 0.10;
    let (rx, ry) = (cx - rw / 2.0, cy - rh / 2.0);

    c.fill(color);
    c.rect(rx, ry + roll, rw, rh - 2.0 * roll, false, true);
    c.round_rect(
        rx,
        ry + rh - roll * 2.0,
        rw,
        roll * 2.0,
        roll * 0.8,
        false,
        true,
    );
    c.round_rect(rx, ry, rw, roll * 2.0, roll * 0.8, false, true);

    c.line_width(1.2);
    c.stroke_color(dv);
    c.round_rect(rx, ry, rw, rh, roll * 0.5, true, false);

    white_lines(
        c,
        0.8,
        rx + rw * 0.12,
        rx + rw * 0.88,
        [0.35, 0.52, 0.69].map(|f| ry + rh * f),
    );

    sparkle(c, cx, ry - size * 0.18, size * 0.14, color);
}

fn sword_icon(c: &mut Canvas, cx: f32, cy: f32, size: f32, color: Rgb) {
    let dv = darker(color);
    let (blade_w, blade_h) = (size * 0.15, size * 0.75);
    let (guard_w, guard_h) = (size * 0.55, size * 0.12);
    let (grip_w, grip_h) = (size * 0.10, size * 0.28);
    let by = cy - blade_h * 0.35;

    c.fill(color);
    c.stroke_color(dv);
    c.line_width(1.0);
    c.polygon(
        &[
            (cx, by + blade_h),
            (cx - blade_w / 2.0, by),
            (cx + blade_w / 2.0, by),
        ],
        true,
        true,
    );

    let (gx, gy) = (cx - guard_w / 2.0, by - guard_h / 2.0);
    c.fill(dv);
    c.rect(gx, gy, guard_w, guard_h, false, true);

    let (r, g, b) = color;
    c.fill((r * 0.85, g * 0.85, b * 0.75));
    c.round_rect(
        cx - grip_w / 2.0,
        gy - grip_h,
        grip_w,
        grip_h,
        grip_w * 0.3,
        false,
        true,
    );

    sparkle(c, cx, by + blade_h + size * 0.12, size * 0.14, color);
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::Language;

    fn card(card_type: &str) -> CardData {
        CardData {
            id: "feuerball".into(),
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
            description: "Ein heller Strahl schießt aus deinem Finger „zu einem Punkt“. "
                .repeat(40),
            edition: None,
            source_book: Some("SRD 5.2.1".into()),
            class_name: Some("Barbar".into()),
            subclass: Some("Pfad des Berserkers".into()),
        }
    }

    fn page_count(pdf: &[u8]) -> usize {
        let s = String::from_utf8_lossy(pdf);
        s.matches("/Type /Page").count() - s.matches("/Type /Pages").count()
    }

    #[test]
    fn strip_pages() {
        let c = card("spell");
        assert_eq!(page_count(&compose_pdf(&[])), 1);
        assert_eq!(page_count(&compose_pdf(&vec![c.clone(); 4])), 1);
        assert_eq!(page_count(&compose_pdf(&vec![c.clone(); 5])), 2);
        let pdf = compose_pdf(&[c]);
        assert!(pdf.starts_with(b"%PDF-"));
        assert!(String::from_utf8_lossy(&pdf).contains("/WinAnsiEncoding"));
    }

    #[test]
    fn duplex_pages() {
        let c = card("spell");
        assert_eq!(page_count(&compose_pdf_duplex(&vec![c.clone(); 1])), 2);
        assert_eq!(page_count(&compose_pdf_duplex(&vec![c.clone(); 9])), 2);
        assert_eq!(page_count(&compose_pdf_duplex(&vec![c; 10])), 4);
    }

    #[test]
    fn all_card_types_render() {
        for t in ["spell", "talent", "rule", "class_feature", "something"] {
            let mut c = card(t);
            compose_pdf(&[c.clone()]);
            c.source_book = None;
            c.typ = None;
            c.subclass = None;
            c.level = None;
            compose_pdf_duplex(&[c]);
        }
    }

    #[test]
    fn duplex_back_mirrors_columns() {
        let l = DuplexLayout::a4();
        for i in 0..9 {
            let (fx, fy) = l.slot(i, false);
            let mirror = (i / DUPLEX_COLS) * DUPLEX_COLS + (DUPLEX_COLS - 1 - i % DUPLEX_COLS);
            let (bx, by) = l.slot(mirror, true);
            assert!((fx - bx).abs() < 1e-3 && (fy - by).abs() < 1e-3);
        }
        assert!(l.slot(0, true).0 > l.slot(0, false).0);
    }
}

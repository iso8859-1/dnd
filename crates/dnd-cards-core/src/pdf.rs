//! Minimal ReportLab-style drawing canvas on top of `pdf-writer`.
//!
//! Uses the PDF base-14 Helvetica family with WinAnsiEncoding, so no font
//! files need to be embedded and German umlauts / „quotes“ render correctly.

use pdf_writer::{Content, Finish, Name, Pdf, Rect, Ref, Str};

pub type Rgb = (f32, f32, f32);

pub const MM_TO_PT: f32 = 72.0 / 25.4;

pub fn mm(v: f32) -> f32 {
    v * MM_TO_PT
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Font {
    Helvetica,
    HelveticaBold,
    HelveticaOblique,
}

impl Font {
    const ALL: [Font; 3] = [Font::Helvetica, Font::HelveticaBold, Font::HelveticaOblique];

    fn resource_name(self) -> Name<'static> {
        match self {
            Font::Helvetica => Name(b"F1"),
            Font::HelveticaBold => Name(b"F2"),
            Font::HelveticaOblique => Name(b"F3"),
        }
    }

    fn base_font(self) -> Name<'static> {
        match self {
            Font::Helvetica => Name(b"Helvetica"),
            Font::HelveticaBold => Name(b"Helvetica-Bold"),
            Font::HelveticaOblique => Name(b"Helvetica-Oblique"),
        }
    }
}

pub struct Canvas {
    page_w: f32,
    page_h: f32,
    pages: Vec<Content>,
    cur: Content,
    font: (Font, f32),
}

impl Canvas {
    pub fn new(page_w: f32, page_h: f32) -> Self {
        Self {
            page_w,
            page_h,
            pages: Vec::new(),
            cur: Content::new(),
            font: (Font::Helvetica, 12.0),
        }
    }

    /// Finish the current page and start a fresh one (graphics state resets).
    pub fn show_page(&mut self) {
        let done = std::mem::replace(&mut self.cur, Content::new());
        self.pages.push(done);
    }

    // ── State ────────────────────────────────────────────────────────────────

    pub fn fill(&mut self, (r, g, b): Rgb) {
        self.cur.set_fill_rgb(r, g, b);
    }

    pub fn stroke_color(&mut self, (r, g, b): Rgb) {
        self.cur.set_stroke_rgb(r, g, b);
    }

    pub fn line_width(&mut self, w: f32) {
        self.cur.set_line_width(w);
    }

    pub fn dash(&mut self, on_off: Option<(f32, f32)>) {
        match on_off {
            Some((on, off)) => self.cur.set_dash_pattern([on, off], 0.0),
            None => self.cur.set_dash_pattern([], 0.0),
        };
    }

    pub fn save_state(&mut self) {
        self.cur.save_state();
    }

    pub fn restore_state(&mut self) {
        self.cur.restore_state();
    }

    /// Translate to (tx, ty), then rotate by 180°.
    pub fn translate_rotate_180(&mut self, tx: f32, ty: f32) {
        self.cur.transform([-1.0, 0.0, 0.0, -1.0, tx, ty]);
    }

    pub fn set_font(&mut self, font: Font, size: f32) {
        self.font = (font, size);
    }

    // ── Shapes ───────────────────────────────────────────────────────────────

    fn paint(&mut self, stroke: bool, fill: bool) {
        match (stroke, fill) {
            (true, true) => self.cur.fill_nonzero_and_stroke(),
            (false, true) => self.cur.fill_nonzero(),
            (true, false) => self.cur.stroke(),
            (false, false) => self.cur.end_path(),
        };
    }

    pub fn rect(&mut self, x: f32, y: f32, w: f32, h: f32, stroke: bool, fill: bool) {
        self.cur.rect(x, y, w, h);
        self.paint(stroke, fill);
    }

    /// Rounded rectangle using ReportLab's curve construction.
    #[allow(clippy::too_many_arguments)]
    pub fn round_rect(&mut self, x: f32, y: f32, w: f32, h: f32, r: f32, stroke: bool, fill: bool) {
        let t = 0.4472 * r;
        let (x0, x1, x2, x3, x4, x5) = (x, x + t, x + r, x + w - r, x + w - t, x + w);
        let (y0, y1, y2, y3, y4, y5) = (y, y + t, y + r, y + h - r, y + h - t, y + h);
        let c = &mut self.cur;
        c.move_to(x2, y0);
        c.line_to(x3, y0);
        c.cubic_to(x4, y0, x5, y1, x5, y2);
        c.line_to(x5, y3);
        c.cubic_to(x5, y4, x4, y5, x3, y5);
        c.line_to(x2, y5);
        c.cubic_to(x1, y5, x0, y4, x0, y3);
        c.line_to(x0, y2);
        c.cubic_to(x0, y1, x1, y0, x2, y0);
        c.close_path();
        self.paint(stroke, fill);
    }

    pub fn line(&mut self, x1: f32, y1: f32, x2: f32, y2: f32) {
        self.cur.move_to(x1, y1);
        self.cur.line_to(x2, y2);
        self.cur.stroke();
    }

    /// Closed polygon through `pts`.
    pub fn polygon(&mut self, pts: &[(f32, f32)], stroke: bool, fill: bool) {
        let Some(&(x0, y0)) = pts.first() else { return };
        self.cur.move_to(x0, y0);
        for &(x, y) in &pts[1..] {
            self.cur.line_to(x, y);
        }
        self.cur.close_path();
        self.paint(stroke, fill);
    }

    // ── Text ─────────────────────────────────────────────────────────────────

    pub fn draw_string(&mut self, x: f32, y: f32, text: &str) {
        let (font, size) = self.font;
        let bytes = encode_win_ansi(text);
        self.cur.begin_text();
        self.cur.set_font(font.resource_name(), size);
        self.cur.next_line(x, y);
        self.cur.show(Str(&bytes));
        self.cur.end_text();
    }

    // ── Output ───────────────────────────────────────────────────────────────

    pub fn finish(mut self) -> Vec<u8> {
        // Like ReportLab, always emit at least one (possibly blank) page.
        self.show_page();

        let mut next = 1;
        let mut alloc = || {
            let r = Ref::new(next);
            next += 1;
            r
        };
        let catalog_id = alloc();
        let tree_id = alloc();
        let font_ids: Vec<Ref> = Font::ALL.iter().map(|_| alloc()).collect();
        let page_ids: Vec<(Ref, Ref)> = self.pages.iter().map(|_| (alloc(), alloc())).collect();

        let mut pdf = Pdf::new();
        pdf.catalog(catalog_id).pages(tree_id);
        pdf.pages(tree_id)
            .kids(page_ids.iter().map(|(p, _)| *p))
            .count(page_ids.len() as i32);

        for (font, id) in Font::ALL.iter().zip(&font_ids) {
            pdf.type1_font(*id)
                .base_font(font.base_font())
                .encoding_predefined(Name(b"WinAnsiEncoding"));
        }

        for (content, (page_id, content_id)) in self.pages.into_iter().zip(&page_ids) {
            let mut page = pdf.page(*page_id);
            page.media_box(Rect::new(0.0, 0.0, self.page_w, self.page_h));
            page.parent(tree_id);
            page.contents(*content_id);
            {
                let mut res = page.resources();
                let mut fonts = res.fonts();
                for (font, id) in Font::ALL.iter().zip(&font_ids) {
                    fonts.pair(font.resource_name(), *id);
                }
                fonts.finish();
            }
            page.finish();
            pdf.stream(*content_id, &content.finish());
        }
        pdf.finish()
    }
}

/// Encode text as Windows-1252 (PDF WinAnsiEncoding); unmappable → `?`.
pub fn encode_win_ansi(text: &str) -> Vec<u8> {
    text.chars()
        .map(|ch| {
            let cp = ch as u32;
            match cp {
                0x20..=0x7E | 0xA0..=0xFF => cp as u8,
                _ => match ch {
                    '€' => 0x80,
                    '‚' => 0x82,
                    'ƒ' => 0x83,
                    '„' => 0x84,
                    '…' => 0x85,
                    '†' => 0x86,
                    '‡' => 0x87,
                    'ˆ' => 0x88,
                    '‰' => 0x89,
                    'Š' => 0x8A,
                    '‹' => 0x8B,
                    'Œ' => 0x8C,
                    'Ž' => 0x8E,
                    '‘' => 0x91,
                    '’' => 0x92,
                    '“' => 0x93,
                    '”' => 0x94,
                    '•' => 0x95,
                    '–' => 0x96,
                    '—' => 0x97,
                    '˜' => 0x98,
                    '™' => 0x99,
                    'š' => 0x9A,
                    '›' => 0x9B,
                    'œ' => 0x9C,
                    'ž' => 0x9E,
                    'Ÿ' => 0x9F,
                    '\u{2212}' | '\u{2010}' | '\u{2011}' => b'-',
                    '\u{202F}' => 0xA0,
                    c if c.is_whitespace() => b' ',
                    _ => b'?',
                },
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn win_ansi() {
        assert_eq!(encode_win_ansi("Größe"), [b'G', b'r', 0xF6, 0xDF, b'e']);
        assert_eq!(
            encode_win_ansi("„x“ – …"),
            [0x84, b'x', 0x93, b' ', 0x96, b' ', 0x85]
        );
        assert_eq!(encode_win_ansi("·"), [0xB7]);
        assert_eq!(encode_win_ansi("✓"), [b'?']);
    }
}

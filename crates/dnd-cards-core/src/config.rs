//! Layout constants (millimetres unless noted).

/// Width of each card strip / face = standard Magic card width.
pub const CARD_STRIP_WIDTH_MM: f32 = 63.0;
/// Height of a fold strip = 2 × folded height.
pub const CARD_STRIP_HEIGHT_MM: f32 = 176.0;
/// Height of one card face after folding = Magic card height.
pub const CARD_FOLDED_HEIGHT_MM: f32 = 88.0;

/// Fold-strip layout on A4 landscape: 4 columns × 1 row.
/// 4×63 + 3×5 = 267mm ≤ 297mm; 176mm ≤ 210mm.
pub const CARDS_PER_ROW: usize = 4;

/// Duplex layout on A4 portrait: 3 × 3 faces per page pair.
/// 3×63 + 2×5 = 199mm ≤ 210mm; 3×88 + 2×5 = 274mm ≤ 297mm.
pub const DUPLEX_COLS: usize = 3;
pub const DUPLEX_ROWS: usize = 3;

pub const CARD_GAP_MM: f32 = 5.0;
pub const CARD_CORNER_RADIUS_MM: f32 = 3.0;

pub const A4_WIDTH_MM: f32 = 210.0;
pub const A4_HEIGHT_MM: f32 = 297.0;

/// Locate the card data store. Order: `$DND_CARDS_DATA`, `./data`, then
/// `data/` next to (or one/two levels above) the running executable.
pub fn find_data_dir() -> Option<std::path::PathBuf> {
    use std::path::PathBuf;
    if let Some(p) = std::env::var_os("DND_CARDS_DATA").map(PathBuf::from) {
        return Some(p);
    }
    let mut candidates = vec![PathBuf::from("data")];
    if let Some(exe_dir) = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|d| d.to_path_buf()))
    {
        candidates.extend(exe_dir.ancestors().take(3).map(|d| d.join("data")));
    }
    candidates.into_iter().find(|p| p.is_dir())
}

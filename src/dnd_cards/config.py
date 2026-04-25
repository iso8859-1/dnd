"""Global constants for PDF layout and application defaults."""

__all__ = [
    "A4_WIDTH_MM",
    "A4_HEIGHT_MM",
    "CARD_STRIP_WIDTH_MM",
    "CARD_STRIP_HEIGHT_MM",
    "CARD_FOLDED_HEIGHT_MM",
    "CARDS_PER_ROW",
    "CARDS_PER_COL",
    "CARD_GAP_MM",
    "CARD_CORNER_RADIUS_MM",
    "DUPLEX_COLS",
    "DUPLEX_ROWS",
    "DEFAULT_DATA_DIR",
    "DEFAULT_OUTPUT_DIR",
]

# A4 dimensions (used in landscape: 297×210mm)
A4_WIDTH_MM: float = 210.0
A4_HEIGHT_MM: float = 297.0

# Card strip dimensions on paper (strip is portrait-oriented on A4 landscape)
# Folded card target size: 63×88mm (standard Magic card, portrait)
# Fold axis is horizontal at 88mm from bottom: top half = front, bottom half = back
CARD_STRIP_WIDTH_MM: float = 63.0    # width of each strip on page = Magic card width
CARD_STRIP_HEIGHT_MM: float = 176.0  # height of each strip on page = 2 × 88mm
CARD_FOLDED_HEIGHT_MM: float = 88.0  # half-height after folding = Magic card height

# Grid layout on A4 landscape (297×210mm): 4 columns × 1 row = 4 cards per page
# Verification: 4×63 + 3×5 = 267mm ≤ 297mm (landscape width) ✓
#               1×176mm = 176mm ≤ 210mm (landscape height) ✓
CARDS_PER_ROW: int = 4
CARDS_PER_COL: int = 1

# Duplex layout on A4 portrait: 3 columns × 3 rows = 9 cards per page pair
# Verification: 3×63 + 2×5 = 199mm ≤ 210mm ✓  |  3×88 + 2×5 = 274mm ≤ 297mm ✓
DUPLEX_COLS: int = 3
DUPLEX_ROWS: int = 3

# Gap between cards and rounded corner radius
CARD_GAP_MM: float = 5.0
CARD_CORNER_RADIUS_MM: float = 3.0

# Default directories — when frozen by PyInstaller, data is bundled inside
# sys._MEIPASS; otherwise fall back to CWD-relative paths.
import sys as _sys

def _bundled(rel: str) -> str:
    base = getattr(_sys, "_MEIPASS", None)
    return str(_sys.modules["pathlib"].Path(base) / rel) if base else rel

DEFAULT_DATA_DIR: str = _bundled("data")
DEFAULT_OUTPUT_DIR: str = "output"

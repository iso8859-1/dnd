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

# Gap between cards and rounded corner radius
CARD_GAP_MM: float = 5.0
CARD_CORNER_RADIUS_MM: float = 3.0

# Default directories (relative to CWD at runtime)
DEFAULT_DATA_DIR: str = "data"
DEFAULT_OUTPUT_DIR: str = "output"

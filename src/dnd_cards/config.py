"""Global constants for PDF layout and application defaults."""

__all__ = [
    "A4_WIDTH_MM",
    "A4_HEIGHT_MM",
    "CARD_STRIP_WIDTH_MM",
    "CARD_STRIP_HEIGHT_MM",
    "CARD_FOLDED_WIDTH_MM",
    "CARDS_PER_ROW",
    "CARDS_PER_COL",
    "CROP_MARK_LENGTH_MM",
    "CROP_MARK_OFFSET_MM",
    "CROP_MARK_LINE_WIDTH_PT",
    "DEFAULT_DATA_DIR",
    "DEFAULT_OUTPUT_DIR",
]

# A4 dimensions
A4_WIDTH_MM: float = 210.0
A4_HEIGHT_MM: float = 297.0

# Card strip dimensions (before folding)
CARD_STRIP_WIDTH_MM: float = 126.0   # folds to 63mm
CARD_STRIP_HEIGHT_MM: float = 88.0
CARD_FOLDED_WIDTH_MM: float = 63.0   # Magic card width

# Grid layout: 2 columns × 4 rows = 8 cards per page
CARDS_PER_ROW: int = 2
CARDS_PER_COL: int = 4

# Crop marks: 0.5pt black, 5mm long, 2mm offset from strip corner
CROP_MARK_LENGTH_MM: float = 5.0
CROP_MARK_OFFSET_MM: float = 2.0
CROP_MARK_LINE_WIDTH_PT: float = 0.5

# Default directories (relative to CWD at runtime)
DEFAULT_DATA_DIR: str = "data"
DEFAULT_OUTPUT_DIR: str = "output"

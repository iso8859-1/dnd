"""ReportLab PDF layout: A4 2×4 grid of 126×88mm fold-strips with crop marks."""

from pathlib import Path

from dnd_cards.models import CardData

__all__ = ["register_fonts", "compose_pdf"]


def register_fonts() -> None:
    """Register custom fonts from assets/fonts/ via importlib.resources.
    Must be called once before any canvas operations. Implementation in Story 2.3."""


def compose_pdf(cards: list[CardData], output_path: Path) -> None:
    """Compose a PDF from card data. Implementation in Story 2.3."""
    raise NotImplementedError

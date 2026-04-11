"""Jinja2 template rendering for card data."""

from typing import Any

from dnd_cards.models import CardData

__all__ = ["render_card"]


def render_card(card: CardData, template_name: str) -> dict[str, Any]:
    """Render a card to a context dict via Jinja2. Implementation in Story 2.2."""
    raise NotImplementedError

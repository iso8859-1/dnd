"""Jinja2 template rendering for card data."""

from pathlib import Path
from typing import Any

import jinja2

from dnd_cards.errors import GenerationError
from dnd_cards.models import CardData

__all__ = ["render_card"]

# Module-level constant — patch `dnd_cards.renderer._TEMPLATES_DIR` in tests
_TEMPLATES_DIR: Path = Path("templates")


def render_card(card: CardData, template_name: str) -> dict[str, Any]:
    """Render a card to a context dict via Jinja2.

    Validates the template exists, then returns a dict of all card field
    values for use by compose_pdf(). No canvas or PDF objects are created here.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
    )
    try:
        env.get_template(f"{template_name}.jinja2")
    except jinja2.TemplateNotFound as exc:
        raise GenerationError(f"Template not found: {template_name}") from exc

    context: dict[str, Any] = {
        "id": card.id,
        "type": card.type,
        "template": card.template,
        "name": card.name,
        "lang": card.lang.value,
        "level": card.level,
        "school": card.school,
        "casting_time": card.casting_time,
        "range": card.range,
        "components": card.components,
        "duration": card.duration,
        "description": card.description,
        "edition": card.edition,
        "source_book": card.source_book,
    }
    return context

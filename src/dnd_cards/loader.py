"""PyYAML parsing + Pydantic validation for card and deck YAML files."""

from pathlib import Path

import pydantic
import yaml

from dnd_cards.errors import ValidationError, YamlParseError
from dnd_cards.models import CardData, DeckProfile

__all__ = ["load_card", "load_deck"]


def load_card(path: Path) -> CardData:
    """Parse and validate a card YAML file."""
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.MarkedYAMLError as exc:
        mark = exc.problem_mark
        line_num: int = (mark.line + 1) if mark is not None else 0
        raise YamlParseError(
            f"{path}: YAML syntax error at line {line_num}: {exc.problem}"
        ) from exc
    except yaml.YAMLError as exc:
        raise YamlParseError(f"{path}: YAML error: {exc}") from exc

    if not isinstance(raw, dict):
        raise YamlParseError(
            f"{path}: YAML file is empty or does not contain a mapping"
        )

    try:
        return CardData.model_validate(raw)
    except pydantic.ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        msg = first_error["msg"]
        raise ValidationError(f"{path}: field '{field}' {msg}") from exc


def load_deck(path: Path) -> DeckProfile:
    """Parse and validate a deck profile YAML file."""
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.MarkedYAMLError as exc:
        mark = exc.problem_mark
        line_num: int = (mark.line + 1) if mark is not None else 0
        raise YamlParseError(
            f"{path}: YAML syntax error at line {line_num}: {exc.problem}"
        ) from exc
    except yaml.YAMLError as exc:
        raise YamlParseError(f"{path}: YAML error: {exc}") from exc

    if not isinstance(raw, dict):
        raise YamlParseError(
            f"{path}: YAML file is empty or does not contain a mapping"
        )

    # Reshape: YAML 'cards' dict → 'entries' list[DeckEntry]
    # The YAML format uses 'cards: {card_key: quantity}' but the model uses
    # 'entries: list[DeckEntry]' — manual reshape required before model_validate().
    cards_raw = raw.get("cards") or {}
    shaped: dict[str, object] = {
        "name": raw.get("name"),
        "entries": [
            {"card_key": k, "quantity": v}
            for k, v in (cards_raw.items() if isinstance(cards_raw, dict) else [])
        ],
    }

    try:
        return DeckProfile.model_validate(shaped)
    except pydantic.ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        msg = first_error["msg"]
        raise ValidationError(f"{path}: field '{field}' {msg}") from exc

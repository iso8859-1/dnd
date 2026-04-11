"""Tests for models module."""

import pydantic
import pytest

from dnd_cards.models import CardData, Language


def test_language_enum_values() -> None:
    assert Language.DE.value == "de"
    assert Language.EN.value == "en"


def test_language_enum_from_string() -> None:
    assert Language("de") == Language.DE
    assert Language("en") == Language.EN


def test_card_data_frozen(valid_card_data: CardData) -> None:
    with pytest.raises(pydantic.ValidationError):
        valid_card_data.name = "mutated"  # type: ignore[misc]

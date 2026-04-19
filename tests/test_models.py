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


def test_card_data_talent_minimal() -> None:
    """Talent card with only non-spell required fields."""
    card = CardData(
        id="ringer",
        type="talent",
        template="talent-v1",
        name="Ringer",
        lang=Language.DE,
        description="Du erhältst folgende Vorzüge.",
        typ="Allgemeines Talent",
        source_book="SRD 5.2.1",
    )
    assert card.level is None
    assert card.school is None
    assert card.casting_time is None
    assert card.range is None
    assert card.components is None
    assert card.duration is None
    assert card.typ == "Allgemeines Talent"


def test_card_data_class_feature_minimal() -> None:
    """Class feature card with required fields and no spell fields."""
    card = CardData(
        id="barbar-kampfrausch",
        type="class_feature",
        template="class-feature-v1",
        name="Kampfrausch",
        lang=Language.DE,
        description="Eine Urmacht...",
        class_name="Barbar",
        level=1,
        source_book="SRD 5.2.1",
    )
    assert card.class_name == "Barbar"
    assert card.subclass is None
    assert card.school is None
    assert card.casting_time is None


def test_card_data_class_feature_with_subclass() -> None:
    """Class feature with subclass field."""
    card = CardData(
        id="barbar-raserei",
        type="class_feature",
        template="class-feature-v1",
        name="Raserei",
        lang=Language.DE,
        description="...",
        class_name="Barbar",
        level=3,
        subclass="Pfad des Berserkers",
    )
    assert card.subclass == "Pfad des Berserkers"

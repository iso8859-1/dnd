"""Tests for loader module."""

from pathlib import Path

import pytest

from dnd_cards.errors import ValidationError, YamlParseError
from dnd_cards.loader import load_card, load_deck
from dnd_cards.models import DeckEntry, DeckProfile, Language


def test_load_card_valid(fixture_path: Path) -> None:
    card = load_card(fixture_path / "spells" / "valid_spell.yaml")
    assert card.id == "fireball"
    assert card.type == "spell"
    assert card.template == "zauber-v1"
    assert card.name == "Fireball"
    assert card.lang == Language.EN
    assert card.level == 3
    assert card.school == "Evocation"
    assert card.casting_time == "1 action"
    assert card.range == "150 ft"
    assert card.components == "V, S, M"
    assert card.duration == "Instantaneous"
    assert "streak" in card.description
    assert card.edition == "5e"
    assert card.source_book == "SRD 5.1"


def test_load_card_missing_required_field(tmp_path: Path) -> None:
    # All required fields except 'level'
    missing_level = tmp_path / "no_level.yaml"
    missing_level.write_text(
        "id: x\ntype: spell\ntemplate: t\nname: X\nlang: en\n"
        "school: Evoc\ncasting_time: 1a\nrange: 10ft\ncomponents: V\n"
        "duration: 1r\ndescription: d\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError) as exc_info:
        load_card(missing_level)
    err = str(exc_info.value)
    assert "level" in err
    assert str(missing_level) in err


def test_load_card_malformed_yaml_raises_yaml_parse_error(fixture_path: Path) -> None:
    with pytest.raises(YamlParseError) as exc_info:
        load_card(fixture_path / "spells" / "malformed_spell.yaml")
    err = str(exc_info.value)
    assert "malformed_spell.yaml" in err
    assert "line" in err


def test_load_card_yaml_error_includes_line_number(tmp_path: Path) -> None:
    bad = tmp_path / "bad_syntax.yaml"
    bad.write_text("id: [unclosed bracket\n", encoding="utf-8")
    with pytest.raises(YamlParseError) as exc_info:
        load_card(bad)
    assert "line" in str(exc_info.value)


def test_load_card_empty_yaml_raises_yaml_parse_error(tmp_path: Path) -> None:
    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(YamlParseError) as exc_info:
        load_card(empty)
    assert "empty" in str(exc_info.value).lower()


def test_load_card_non_mapping_yaml_raises_yaml_parse_error(tmp_path: Path) -> None:
    scalar = tmp_path / "scalar.yaml"
    scalar.write_text("just a string\n", encoding="utf-8")
    with pytest.raises(YamlParseError) as exc_info:
        load_card(scalar)
    assert "mapping" in str(exc_info.value).lower()


def test_load_card_invalid_lang_value(tmp_path: Path) -> None:
    bad_lang = tmp_path / "bad_lang.yaml"
    bad_lang.write_text(
        "id: x\ntype: spell\ntemplate: t\nname: X\nlang: fr\n"
        "level: 1\nschool: S\ncasting_time: 1a\nrange: 10ft\n"
        "components: V\nduration: 1r\ndescription: d\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError) as exc_info:
        load_card(bad_lang)
    assert "lang" in str(exc_info.value)


# ---------------------------------------------------------------------------
# load_deck tests
# ---------------------------------------------------------------------------


def test_load_deck_valid(fixture_path: Path) -> None:
    profile = load_deck(fixture_path / "decks" / "minimal_deck.yaml")
    assert isinstance(profile, DeckProfile)
    assert profile.name == "Test Deck"
    assert len(profile.entries) == 1
    entry = profile.entries[0]
    assert isinstance(entry, DeckEntry)
    assert entry.card_key == "spells/fireball"
    assert entry.quantity == 1


def test_load_deck_multiple_entries(tmp_path: Path) -> None:
    deck_file = tmp_path / "multi.yaml"
    deck_file.write_text(
        "name: Multi Deck\ncards:\n  spells/feuerball: 1\n  spells/magisches-geschoss: 2\n",
        encoding="utf-8",
    )
    profile = load_deck(deck_file)
    assert profile.name == "Multi Deck"
    assert len(profile.entries) == 2
    keys = {e.card_key for e in profile.entries}
    assert keys == {"spells/feuerball", "spells/magisches-geschoss"}
    qty_map = {e.card_key: e.quantity for e in profile.entries}
    assert qty_map["spells/magisches-geschoss"] == 2


def test_load_deck_preserves_card_key_without_resolution(tmp_path: Path) -> None:
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        "name: Test\ncards:\n  spells/feuerball: 1\n",
        encoding="utf-8",
    )
    profile = load_deck(deck_file)
    assert profile.entries[0].card_key == "spells/feuerball"


def test_load_deck_malformed_yaml_raises_yaml_parse_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: [unclosed bracket\n", encoding="utf-8")
    with pytest.raises(YamlParseError) as exc_info:
        load_deck(bad)
    err = str(exc_info.value)
    assert str(bad) in err
    assert "line" in err


def test_load_deck_missing_name_raises_validation_error(tmp_path: Path) -> None:
    deck_file = tmp_path / "no_name.yaml"
    deck_file.write_text("cards:\n  spells/fireball: 1\n", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        load_deck(deck_file)
    err = str(exc_info.value)
    assert "name" in err
    assert str(deck_file) in err

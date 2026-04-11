"""Tests for loader module."""

from pathlib import Path

import pytest

from dnd_cards.errors import ValidationError, YamlParseError
from dnd_cards.loader import load_card
from dnd_cards.models import Language


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

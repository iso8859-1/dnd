"""Tests for scanner module."""

from pathlib import Path

from dnd_cards.scanner import CardRef, scan_cards


def _make_card(base: Path, lang: str, card_type: str, stem: str) -> Path:
    """Helper: create a stub .yaml file at base/{lang}/{card_type}/{stem}.yaml."""
    card_dir = base / lang / card_type
    card_dir.mkdir(parents=True, exist_ok=True)
    card_file = card_dir / f"{stem}.yaml"
    card_file.write_text(f"id: {stem}\n", encoding="utf-8")
    return card_file


def test_scan_cards_returns_correct_key_and_ref(tmp_path: Path) -> None:
    card_file = _make_card(tmp_path, "en", "spells", "fireball")
    result = scan_cards(tmp_path)
    assert "spells/fireball" in result
    ref = result["spells/fireball"]
    assert ref.card_type == "spells"
    assert ref.path == card_file


def test_scan_cards_multi_language(tmp_path: Path) -> None:
    _make_card(tmp_path, "en", "spells", "fireball")
    _make_card(tmp_path, "de", "spells", "feuerball")
    result = scan_cards(tmp_path)
    assert len(result) == 2
    assert "spells/fireball" in result
    assert "spells/feuerball" in result
    assert result["spells/fireball"].card_type == "spells"
    assert result["spells/feuerball"].card_type == "spells"


def test_scan_cards_ignores_yml_extension(tmp_path: Path) -> None:
    yml_dir = tmp_path / "en" / "spells"
    yml_dir.mkdir(parents=True)
    (yml_dir / "fireball.yml").write_text("id: fireball\n", encoding="utf-8")
    result = scan_cards(tmp_path)
    assert len(result) == 0


def test_scan_cards_empty_directory(tmp_path: Path) -> None:
    result = scan_cards(tmp_path)
    assert result == {}


def test_scan_cards_no_collision_same_stem_different_type(tmp_path: Path) -> None:
    _make_card(tmp_path, "de", "conditions", "vergiftet")
    _make_card(tmp_path, "de", "spells", "vergiftet")
    result = scan_cards(tmp_path)
    assert "conditions/vergiftet" in result
    assert "spells/vergiftet" in result
    assert len(result) == 2
    assert result["conditions/vergiftet"].card_type == "conditions"
    assert result["spells/vergiftet"].card_type == "spells"


def test_card_ref_is_namedtuple(tmp_path: Path) -> None:
    _make_card(tmp_path, "en", "spells", "fireball")
    result = scan_cards(tmp_path)
    ref = result["spells/fireball"]
    assert isinstance(ref, CardRef)
    assert isinstance(ref.path, Path)
    assert isinstance(ref.card_type, str)

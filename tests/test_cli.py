"""Tests for cli module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dnd_cards.cli import app
from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
from dnd_cards.models import CardData, DeckEntry, DeckProfile, Language
from dnd_cards.scanner import CardRef

runner = CliRunner()  # Typer's CliRunner always mixes stderr into output


# ── Existing Story 1.1 tests ────────────────────────────────────────────────

def test_help_shows_subcommands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "generate" in result.output
    assert "validate" in result.output
    assert "list" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "dnd-cards" in result.output


# ── Story 1.2: Error routing tests ──────────────────────────────────────────

def test_generate_yaml_parse_error_exits_1() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=YamlParseError("bad.yaml: YAML syntax error at line 1: mapping issues"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "bad.yaml"])
    assert result.exit_code == 1
    assert "bad.yaml" in result.output


def test_generate_validation_error_exits_1() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=ValidationError("deck.yaml: field 'name' is required"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "deck.yaml"])
    assert result.exit_code == 1
    assert "deck.yaml" in result.output


def test_generate_card_not_found_error_exits_1() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=CardNotFoundError("Card not found: spells/feuerbaal (deck: deck.yaml)"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "deck.yaml"])
    assert result.exit_code == 1
    assert "feuerbaal" in result.output


def test_generate_generation_error_exits_2() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=GenerationError("PDF generation failed: canvas error"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "deck.yaml"])
    assert result.exit_code == 2
    assert "PDF generation failed" in result.output


def test_generate_unexpected_error_exits_2() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=RuntimeError("something unexpected broke"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "test.yaml"])
    assert result.exit_code == 2


def test_unexpected_error_writes_traceback() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=RuntimeError("boom"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "test.yaml"])
    assert result.exit_code == 2
    assert "RuntimeError" in result.output


# ── Story 1.5: List subcommand tests ────────────────────────────────────────

def test_list_no_filter_shows_all_cards() -> None:
    fake_index = {
        "spells/fireball": CardRef(
            path=Path("data/en/spells/fireball.yaml"), card_type="spells"
        ),
        "conditions/frightened": CardRef(
            path=Path("data/en/conditions/frightened.yaml"), card_type="conditions"
        ),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines == ["fireball [spells]", "frightened [conditions]"]


def test_list_type_filter_restricts_output() -> None:
    fake_index = {
        "spells/fireball": CardRef(
            path=Path("data/en/spells/fireball.yaml"), card_type="spells"
        ),
        "conditions/frightened": CardRef(
            path=Path("data/en/conditions/frightened.yaml"), card_type="conditions"
        ),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list", "--type", "spells"])
    assert result.exit_code == 0
    assert "fireball [spells]" in result.output
    assert "frightened" not in result.output


def test_list_no_match_filter_empty_output() -> None:
    fake_index = {
        "spells/fireball": CardRef(
            path=Path("data/en/spells/fireball.yaml"), card_type="spells"
        ),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list", "--type", "conditions"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_list_missing_data_dir_returns_empty(tmp_path: Path) -> None:
    nonexistent = str(tmp_path / "no-such-dir")
    with patch("dnd_cards.cli.DEFAULT_DATA_DIR", nonexistent):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_list_scan_error_exits_2() -> None:
    with patch("dnd_cards.cli.scan_cards", side_effect=PermissionError("no access")):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 2


def test_list_output_sorted_alphabetically() -> None:
    fake_index = {
        "spells/zebra": CardRef(
            path=Path("data/en/spells/zebra.yaml"), card_type="spells"
        ),
        "spells/apple": CardRef(
            path=Path("data/en/spells/apple.yaml"), card_type="spells"
        ),
        "spells/mango": CardRef(
            path=Path("data/en/spells/mango.yaml"), card_type="spells"
        ),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines == ["apple [spells]", "mango [spells]", "zebra [spells]"]


# ── Story 2.4: generate subcommand integration tests ────────────────────────

@pytest.fixture
def fake_card() -> CardData:
    return CardData(
        id="fireball",
        type="spell",
        template="zauber-v1",
        name="Fireball",
        lang=Language.EN,
        level=3,
        school="Evocation",
        casting_time="1 action",
        range="150 ft",
        components="V, S, M",
        duration="Instantaneous",
        description="A bright streak flashes from your pointing finger.",
    )


def test_generate_happy_path(tmp_path: Path, fake_card: CardData) -> None:
    deck_file = tmp_path / "lena-stufe5.yaml"
    deck_file.write_text("name: Lena\ncards:\n  spells/fireball: 1\n", encoding="utf-8")
    out_dir = tmp_path / "output"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Lena", entries=[DeckEntry(card_key="spells/fireball", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf") as mock_pdf:
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(out_dir)]
        )

    assert result.exit_code == 0
    assert "lena-stufe5.pdf" in result.output
    assert out_dir.is_dir()
    mock_pdf.assert_called_once()


def test_generate_custom_output_dir(tmp_path: Path, fake_card: CardData) -> None:
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/fireball: 1\n", encoding="utf-8")
    custom_dir = tmp_path / "custom" / "nested"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/fireball", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf"):
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(custom_dir)]
        )

    assert result.exit_code == 0
    assert custom_dir.is_dir()
    assert str(custom_dir) in result.output


def test_generate_missing_card_key_exits_1(tmp_path: Path) -> None:
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/nonexistent: 1\n", encoding="utf-8")

    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/nonexistent", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value={}), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck):
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(tmp_path)]
        )

    assert result.exit_code == 1
    assert "nonexistent" in result.output


def test_generate_quantity_expansion(tmp_path: Path, fake_card: CardData) -> None:
    """DeckEntry(quantity=2) should produce 2 copies in compose_pdf call."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/fireball: 2\n", encoding="utf-8")
    out_dir = tmp_path / "output"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/fireball", quantity=2)])

    mock_pdf = MagicMock()
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf", mock_pdf):
        runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(out_dir)]
        )

    called_cards = mock_pdf.call_args[0][0]  # first positional arg = cards list
    assert len(called_cards) == 2
    assert called_cards[0] is fake_card
    assert called_cards[1] is fake_card


# ── Story 4.5: generate --duplex flag tests ──────────────────────────────────


def test_generate_duplex_flag_calls_compose_pdf_duplex(tmp_path: Path, fake_card: CardData) -> None:
    """--duplex routes to compose_pdf_duplex, not compose_pdf."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/fireball: 1\n", encoding="utf-8")
    out_dir = tmp_path / "output"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/fireball", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf") as mock_regular, \
         patch("dnd_cards.cli.compose_pdf_duplex") as mock_duplex:
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(out_dir), "--duplex"]
        )

    assert result.exit_code == 0
    mock_duplex.assert_called_once()
    mock_regular.assert_not_called()


def test_generate_without_duplex_calls_compose_pdf(tmp_path: Path, fake_card: CardData) -> None:
    """Without --duplex, compose_pdf (fold-strip) is used, not compose_pdf_duplex."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/fireball: 1\n", encoding="utf-8")
    out_dir = tmp_path / "output"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/fireball", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf") as mock_regular, \
         patch("dnd_cards.cli.compose_pdf_duplex") as mock_duplex:
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(out_dir)]
        )

    assert result.exit_code == 0
    mock_regular.assert_called_once()
    mock_duplex.assert_not_called()

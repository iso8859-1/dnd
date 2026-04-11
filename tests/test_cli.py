"""Tests for cli module."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dnd_cards.cli import app
from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
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

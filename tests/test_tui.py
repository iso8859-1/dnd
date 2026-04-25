"""Tests for the TUI deck builder module."""

from pathlib import Path
from unittest.mock import patch

import pytest
from textual.widgets import DataTable, Label

from dnd_cards.scanner import CardRef
from dnd_cards.tui import (
    DeckBuilderApp,
    _discover_languages,
    _discover_types,
    _fuzzy_match,
    slugify,
)


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


def test_slugify_basic() -> None:
    assert slugify("Feuerball") == "feuerball"


def test_slugify_umlauts() -> None:
    assert slugify("Attributswerterhöhung") == "attributswerterhohung"


def test_slugify_spaces_to_hyphens() -> None:
    assert slugify("Wilder Angreifer") == "wilder-angreifer"


def test_slugify_collapses_multiple_hyphens() -> None:
    assert slugify("A  B---C") == "a-b-c"


# ---------------------------------------------------------------------------
# _fuzzy_match
# ---------------------------------------------------------------------------


def test_fuzzy_match_empty_query_always_true() -> None:
    assert _fuzzy_match("", "anything") is True


def test_fuzzy_match_direct_substring() -> None:
    assert _fuzzy_match("feuer", "Feuerball") is True


def test_fuzzy_match_case_insensitive() -> None:
    assert _fuzzy_match("FEUER", "Feuerball") is True


def test_fuzzy_match_subsequence_typo() -> None:
    # 'feurball' is missing the 'e' in the right place but chars appear in order
    assert _fuzzy_match("feurball", "Feuerball") is True


def test_fuzzy_match_no_match() -> None:
    assert _fuzzy_match("xyz", "Feuerball") is False


def test_fuzzy_match_partial_start() -> None:
    assert _fuzzy_match("feuer", "Feuerball") is True


# ---------------------------------------------------------------------------
# _discover_languages
# ---------------------------------------------------------------------------


def test_discover_languages(tmp_path: Path) -> None:
    (tmp_path / "de").mkdir()
    (tmp_path / "en").mkdir()
    (tmp_path / "fr").mkdir()
    assert _discover_languages(tmp_path) == ["de", "en", "fr"]


def test_discover_languages_sorted(tmp_path: Path) -> None:
    (tmp_path / "zh").mkdir()
    (tmp_path / "de").mkdir()
    assert _discover_languages(tmp_path) == ["de", "zh"]


def test_discover_languages_ignores_files(tmp_path: Path) -> None:
    (tmp_path / "de").mkdir()
    (tmp_path / "readme.txt").write_text("x")
    assert _discover_languages(tmp_path) == ["de"]


# ---------------------------------------------------------------------------
# _discover_types
# ---------------------------------------------------------------------------


def test_discover_types_sorted() -> None:
    index = {
        "spells/fireball": CardRef(path=Path("a.yaml"), card_type="spells"),
        "talents/ringer": CardRef(path=Path("b.yaml"), card_type="talents"),
        "rules/abenteuer": CardRef(path=Path("c.yaml"), card_type="rules"),
        "spells/shield": CardRef(path=Path("d.yaml"), card_type="spells"),
    }
    assert _discover_types(index) == ["rules", "spells", "talents"]


def test_discover_types_deduplicates() -> None:
    index = {
        "spells/a": CardRef(path=Path("a.yaml"), card_type="spells"),
        "spells/b": CardRef(path=Path("b.yaml"), card_type="spells"),
    }
    assert _discover_types(index) == ["spells"]


# ---------------------------------------------------------------------------
# DeckBuilderApp — Textual pilot tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    """Minimal data directory with 3 cards across 2 types."""
    spells = tmp_path / "de" / "SRD" / "spells"
    talents = tmp_path / "de" / "SRD" / "talents"
    spells.mkdir(parents=True)
    talents.mkdir(parents=True)
    (spells / "feuerball.yaml").write_text(
        "id: feuerball\ntype: spell\ntemplate: spell\n"
        "name: Feuerball\nlang: de\ndescription: Flammen.\n",
        encoding="utf-8",
    )
    (spells / "blitz.yaml").write_text(
        "id: blitz\ntype: spell\ntemplate: spell\n"
        "name: Blitz\nlang: de\ndescription: Blitz.\n",
        encoding="utf-8",
    )
    (talents / "ringer.yaml").write_text(
        "id: ringer\ntype: talent\ntemplate: talent-v1\n"
        "name: Ringer\nlang: de\ndescription: Vorzüge.\n",
        encoding="utf-8",
    )
    return tmp_path


async def test_tui_launches_and_quits(data_dir: Path) -> None:
    """App opens, receives 'q', exits cleanly."""
    app = DeckBuilderApp(data_dir=data_dir, deck_name="Test")
    async with app.run_test() as pilot:
        await pilot.press("q")


async def test_tui_search_filters_list(data_dir: Path) -> None:
    """Typing 'feuer' reduces visible rows to cards matching the query."""
    app = DeckBuilderApp(data_dir=data_dir, deck_name="Test")
    async with app.run_test() as pilot:
        await pilot.press("f", "e", "u", "e", "r")
        table = app.query_one("#card-table", DataTable)
        assert table.row_count == 1


async def test_tui_search_updates_filter_label(data_dir: Path) -> None:
    """Typing updates the internal search state; Escape clears it."""
    app = DeckBuilderApp(data_dir=data_dir, deck_name="Test")
    async with app.run_test() as pilot:
        await pilot.press("f", "e", "u", "e", "r")
        assert app._search == "feuer"
        await pilot.press("escape")
        assert app._search == ""


async def test_tui_plus_increments_quantity(data_dir: Path) -> None:
    """Pressing '+' on the highlighted row increments its qty to 1."""
    app = DeckBuilderApp(data_dir=data_dir, deck_name="Test")
    async with app.run_test() as pilot:
        # Type to narrow to one card
        await pilot.press("f", "e", "u", "e", "r")
        await pilot.press("plus")
        # The card qty should now be 1
        feuerball = next(c for c in app._cards if "feuerball" in c.key)
        assert feuerball.qty == 1


async def test_tui_non_alpha_keys_ignored_by_filter(data_dir: Path) -> None:
    """Digits, ctrl combos, and special keys must not pollute the filter."""
    app = DeckBuilderApp(data_dir=data_dir, deck_name="Test")
    async with app.run_test() as pilot:
        # These should be handled as bindings/filter toggles, NOT appended to search
        await pilot.press("1")          # type toggle
        await pilot.press("plus")       # qty binding
        await pilot.press("minus")      # qty binding
        assert app._search == ""


async def test_tui_save_writes_yaml(data_dir: Path, tmp_path: Path) -> None:
    """Ctrl+S opens save modal; confirming with Enter writes a valid deck YAML."""
    import yaml as _yaml

    deck_path = tmp_path / "output" / "test-deck.yaml"
    deck_path.parent.mkdir(parents=True)
    app = DeckBuilderApp(
        data_dir=data_dir,
        deck_name="Test Deck",
        deck_file=deck_path,
    )
    async with app.run_test() as pilot:
        # After each '+' search clears, so re-type filter for second press
        await pilot.press("f", "e", "u", "e", "r")
        await pilot.press("plus")  # qty=1
        await pilot.press("plus")  # qty=2
        await pilot.press("ctrl+s")
        await pilot.press("enter")  # confirm name in save modal
        await pilot.press("q")

    assert deck_path.exists()
    data = _yaml.safe_load(deck_path.read_text(encoding="utf-8"))
    assert data["name"] == "Test Deck"
    assert data["cards"]["spells/feuerball"] == 2


# ---------------------------------------------------------------------------
# Story 5.2: ctrl+d duplex generation binding
# ---------------------------------------------------------------------------


async def test_ctrl_d_calls_compose_pdf_duplex(data_dir: Path, tmp_path: Path) -> None:
    """ctrl+d triggers compose_pdf_duplex, not compose_pdf."""
    deck_path = tmp_path / "test.yaml"
    with patch("dnd_cards.tui.compose_pdf") as mock_regular, \
         patch("dnd_cards.tui.compose_pdf_duplex") as mock_duplex:
        app = DeckBuilderApp(data_dir=data_dir, deck_name="Test", deck_file=deck_path)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+d")
            await pilot.pause()

    mock_duplex.assert_called_once()
    mock_regular.assert_not_called()


async def test_ctrl_g_does_not_call_compose_pdf_duplex(data_dir: Path, tmp_path: Path) -> None:
    """ctrl+g triggers compose_pdf (fold-strip), not compose_pdf_duplex."""
    deck_path = tmp_path / "test.yaml"
    with patch("dnd_cards.tui.compose_pdf") as mock_regular, \
         patch("dnd_cards.tui.compose_pdf_duplex") as mock_duplex:
        app = DeckBuilderApp(data_dir=data_dir, deck_name="Test", deck_file=deck_path)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+g")
            await pilot.pause()

    mock_regular.assert_called_once()
    mock_duplex.assert_not_called()


async def test_ctrl_d_empty_deck_does_not_crash(data_dir: Path, tmp_path: Path) -> None:
    """Pressing ctrl+d with 0 cards added completes without crashing the TUI."""
    deck_path = tmp_path / "test.yaml"
    with patch("dnd_cards.tui.compose_pdf_duplex"):
        app = DeckBuilderApp(data_dir=data_dir, deck_name="Test", deck_file=deck_path)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+d")
            await pilot.pause()
            await pilot.press("q")

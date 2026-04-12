---
story_id: "2.4"
story_key: "2-4-generate-subcommand-end-to-end"
epic: "Epic 2: Core PDF Generation"
status: "ready-for-dev"
created: "2026-04-12"
---

# Story 2.4: `generate` Subcommand — End to End

## Story

As Tobias,
I want to run `dnd-cards generate --deck decks/my-deck.yaml` and get a print-ready PDF,
so that I can go from a deck file to a physical card in one command.

---

## Acceptance Criteria

**AC1 — Happy path: valid deck produces PDF at default output path:**
- **Given** a valid deck profile referencing card keys present in `data/`
- **When** `dnd-cards generate --deck decks/lena-stufe5.yaml` is run
- **Then** the generate command orchestrates: `scan_cards()` → `load_deck()` → resolve keys → `load_card()` per key → expand quantities → `compose_pdf()`
- **And** the PDF is written to `output/lena-stufe5.pdf` (filename = deck file stem + `.pdf`)
- **And** `output/` is created if it does not exist
- **And** the resolved PDF path is printed to stdout
- **And** the process exits with code 0

**AC2 — `--output-dir` overrides the output directory:**
- **Given** `--output-dir /tmp/cards` is specified
- **When** the command runs successfully
- **Then** the PDF is written to `/tmp/cards/lena-stufe5.pdf`
- **And** `/tmp/cards/` is created if it does not exist

**AC3 — Missing card key raises `CardNotFoundError`:**
- **Given** a deck entry references a `card_key` not present in the scanner index
- **When** the generate command resolves keys (after `scan_cards()`, before `load_card()`)
- **Then** a `CardNotFoundError` is raised with message: `Card not found: {key} (deck: {deck_file})`
- **And** the message is written to stderr and the process exits with code 1
- **And** no partial PDF is written to disk

**AC4 — Quantity expansion produces duplicate card strips:**
- **Given** `quantity: 2` for a card entry
- **When** the PDF is generated
- **Then** that card appears as two separate strips in the output (i.e. `compose_pdf()` receives `[card, card]`)

---

## Tasks / Subtasks

- [x] Task 1: Update imports in `cli.py` (AC: 1, 2, 3, 4)
  - [x] Add `compose_pdf` to the `from dnd_cards.composer import ...` line
  - [x] Add `DEFAULT_OUTPUT_DIR` to the `from dnd_cards.config import ...` line
  - [x] Add `from dnd_cards.loader import load_card, load_deck`
  - [x] Add `from dnd_cards.models import CardData`
- [x] Task 2: Add `--output-dir` option and update `generate` command signature (AC: 1, 2)
  - [x] Add `output_dir: Optional[str] = typer.Option(None, "--output-dir", ...)` parameter
  - [x] Pass `output_dir` to `_generate_impl(deck, output_dir)`
- [x] Task 3: Implement `_generate_impl()` in `cli.py` (AC: 1, 2, 3, 4)
  - [x] Scan cards: `card_index = scan_cards(Path(DEFAULT_DATA_DIR))`
  - [x] Load deck: `deck_profile = load_deck(deck_path)`
  - [x] Resolve keys + load cards: raise `CardNotFoundError` if key missing; `load_card(ref.path)`
  - [x] Expand quantities: `cards.extend([card] * entry.quantity)`
  - [x] Build output path: `out_dir / f"{deck_path.stem}.pdf"`; `out_dir.mkdir(parents=True, exist_ok=True)`
  - [x] Call `compose_pdf(cards, out_path)`; print path to stdout with `typer.echo(str(out_path))`
- [x] Task 4: Add generate integration tests to `tests/test_cli.py` (AC: 1, 2, 3, 4)
  - [x] Test happy path: valid deck → exit 0 + PDF path in stdout
  - [x] Test `--output-dir`: PDF written to custom dir
  - [x] Test missing card key raises `CardNotFoundError` → exit 1 + key in output
  - [x] Test quantity expansion: `compose_pdf` called with correct card count
- [x] Task 5: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (56 tests green, 4 new + 52 existing)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- **`src/dnd_cards/cli.py`** — `generate` command and `_generate_impl` stub exist:
  ```python
  @app.command()
  def generate(
      deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
  ) -> None:
      """Generate a print-ready PDF from a deck profile."""
      try:
          _generate_impl(deck)
      except Exception as exc:
          _handle_dnd_error(exc)

  def _generate_impl(deck: str) -> None:
      """Implementation in Story 2.4."""
      raise NotImplementedError
  ```
  The `generate` command, `_handle_dnd_error`, and `main` callback (which calls `register_fonts()`) are already wired correctly. Add `--output-dir` option and replace `_generate_impl` stub.

- **Existing generate error tests** — `test_generate_yaml_parse_error_exits_1`, `test_generate_card_not_found_error_exits_1`, etc. all patch `dnd_cards.cli._generate_impl` to raise exceptions. These test the error-handling wrapper and **will continue to pass unchanged** after Story 2.4 — the patch bypasses the real implementation entirely.

- **`scan_cards`, `load_deck`, `load_card`, `compose_pdf`** — all fully implemented in Stories 1.4, 2.1, 1.3, 2.3 respectively. Import and call them directly.

- **`DEFAULT_DATA_DIR = "data"`, `DEFAULT_OUTPUT_DIR = "output"`** — already in `config.py`.

- **52 tests currently passing** — all must stay green.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/cli.py` | Add imports, `--output-dir` param, implement `_generate_impl()` |
| `tests/test_cli.py` | Add 4 new generate integration tests |

### Exact `cli.py` Changes

**Updated import block** (replace the current imports):

```python
import importlib.metadata
import traceback
from pathlib import Path
from typing import NoReturn, Optional

import typer

from dnd_cards.composer import compose_pdf, register_fonts
from dnd_cards.config import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
from dnd_cards.loader import load_card, load_deck
from dnd_cards.models import CardData
from dnd_cards.scanner import scan_cards
```

**Updated `generate` command** (add `--output-dir`):

```python
@app.command()
def generate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Output directory for generated PDF."
    ),
) -> None:
    """Generate a print-ready PDF from a deck profile."""
    try:
        _generate_impl(deck, output_dir)
    except Exception as exc:
        _handle_dnd_error(exc)
```

**`_generate_impl()` implementation**:

```python
def _generate_impl(deck: str, output_dir: Optional[str] = None) -> None:
    deck_path = Path(deck)
    card_index = scan_cards(Path(DEFAULT_DATA_DIR))
    deck_profile = load_deck(deck_path)

    cards: list[CardData] = []
    for entry in deck_profile.entries:
        if entry.card_key not in card_index:
            raise CardNotFoundError(
                f"Card not found: {entry.card_key} (deck: {deck_path})"
            )
        card = load_card(card_index[entry.card_key].path)
        cards.extend([card] * entry.quantity)

    out_dir = Path(output_dir) if output_dir else Path(DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{deck_path.stem}.pdf"

    compose_pdf(cards, out_path)
    typer.echo(str(out_path))
```

**Key implementation notes:**
- `cards.extend([card] * entry.quantity)` — quantity expansion; a `DeckEntry(quantity=2)` adds the same card object twice; compose_pdf receives a list with 2 entries
- `out_dir.mkdir(parents=True, exist_ok=True)` — creates intermediate dirs, no error if already exists
- `out_path = out_dir / f"{deck_path.stem}.pdf"` — stem strips `.yaml` extension: `lena-stufe5.yaml` → `lena-stufe5.pdf`
- `typer.echo(str(out_path))` — prints to stdout (not stderr); `_handle_dnd_error` sends errors to stderr
- Error order: `CardNotFoundError` is raised during key resolution, before `load_card()` or `compose_pdf()` — no partial PDF written

### New Tests for `tests/test_cli.py`

Add these tests after the existing list tests. Required additional imports at top of file:

```python
from unittest.mock import MagicMock, patch

from dnd_cards.models import CardData, DeckEntry, DeckProfile, Language
```

Note: `MagicMock` is needed for `test_generate_quantity_expansion`. Check whether `MagicMock` is already imported — if not, add it to the existing `from unittest.mock import patch` line.

```python
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
```

**Required import additions at top of `test_cli.py`** (update the existing mock import):
```python
from unittest.mock import MagicMock, patch
```
And add to model imports:
```python
from dnd_cards.models import CardData, DeckEntry, DeckProfile, Language
```
Also add `pytest` import if not already present:
```python
import pytest
```

### Architecture Constraints

- **Patch at `dnd_cards.cli.*`** — patch `scan_cards`, `load_deck`, `load_card`, `compose_pdf` where they're used (in `cli.py`), not at their source modules
- **`_generate_impl` signature change** — add `output_dir: Optional[str] = None` second param; existing tests that patch `_generate_impl` are unaffected (they bypass it entirely)
- **No partial PDF on error** — `CardNotFoundError` is raised before `compose_pdf()` is called; `out_dir.mkdir()` may have run but no `.pdf` file is created
- **Absolute imports only** — `from dnd_cards.loader import load_card, load_deck` (ruff TID252)
- **`CardData` type annotation required** — `cards: list[CardData] = []` needs the import for mypy --strict
- **`compose_pdf` accepts `Path | BytesIO`** — passing `Path` is valid (mypy happy)

### Regression Safeguard

All 52 existing tests must remain green. The existing generate error tests patch `_generate_impl` — they are unaffected by the implementation change. Only `cli.py` and `test_cli.py` are modified.

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 52 (all passing)

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — clean implementation, all checks passed first run.

### Completion Notes List

- Implemented `_generate_impl()` in `cli.py` wiring scan_cards → load_deck → key resolution → load_card → quantity expansion → compose_pdf → stdout
- Added `--output-dir` option to `generate` command
- 4 new integration tests added to `test_cli.py`; all 56 tests pass

### File List

- `src/dnd_cards/cli.py`
- `tests/test_cli.py`

### Change Log

- 2026-04-12: Story implemented and moved to review

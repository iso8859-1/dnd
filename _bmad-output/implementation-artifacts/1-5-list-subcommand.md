---
story_id: "1.5"
story_key: "1-5-list-subcommand"
epic: "Epic 1: Foundation & Card Data"
status: "done"
created: "2026-04-11"
---

# Story 1.5: List Subcommand

## Story

As Tobias,
I want to run `dnd-cards list` (with optional `--type` filter) and see all available cards in the data store,
so that I can quickly inspect what cards exist without digging through the directory structure.

---

## Acceptance Criteria

**AC1 — Lists all cards when no filter given:**
- **Given** `data/en/spells/fireball.yaml` and `data/en/conditions/frightened.yaml` exist
- **When** `dnd-cards list` is run
- **Then** stdout contains lines `fireball [spells]` and `frightened [conditions]`, sorted alphabetically by stem, exit 0

**AC2 — `--type` filter restricts output:**
- **Given** `data/en/spells/fireball.yaml` and `data/en/conditions/frightened.yaml` exist
- **When** `dnd-cards list --type spells` is run
- **Then** stdout contains only `fireball [spells]`, not the conditions card, exit 0

**AC3 — No-match filter returns empty output, exit 0:**
- **Given** only `data/en/spells/fireball.yaml` exists
- **When** `dnd-cards list --type conditions` is run
- **Then** stdout is empty, exit 0 (no error)

**AC4 — Missing data directory returns empty output, exit 0:**
- **Given** the `data/` directory does not exist
- **When** `dnd-cards list` is run
- **Then** stdout is empty, exit 0 (no error, no exception)

**AC5 — Output is sorted alphabetically by stem:**
- **Given** cards `zebra`, `apple`, `mango` exist in the same type
- **When** `dnd-cards list` is run
- **Then** output order is `apple [...] → mango [...] → zebra [...]`

---

## Tasks / Subtasks

- [x] Task 1: Add imports to `cli.py` (AC: 1, 2, 3, 4)
  - [x] Add `from pathlib import Path` import
  - [x] Add `from dnd_cards.config import DEFAULT_DATA_DIR`
  - [x] Add `from dnd_cards.scanner import scan_cards`
- [x] Task 2: Implement `_list_cards_impl()` in `cli.py` (AC: 1, 2, 3, 4, 5)
  - [x] Replace `raise NotImplementedError` stub with full implementation
  - [x] Guard with `if not data_dir.is_dir(): return`
  - [x] Filter by `card_type` when `type` arg is provided
  - [x] Sort entries alphabetically by stem before printing
  - [x] Output format: `{stem} [{card_type}]` per line via `typer.echo()`
- [x] Task 3: Implement `tests/test_cli.py` list command tests (AC: 1, 2, 3, 4, 5)
  - [x] Test unfiltered list shows all cards sorted
  - [x] Test `--type` filter restricts to matching type only
  - [x] Test no-match filter returns empty output and exit 0
  - [x] Test missing data directory returns empty output and exit 0
  - [x] Test alphabetical sort order
- [x] Task 4: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- `cli.py` already has the `list_cards` Typer command registered as `@app.command(name="list")` with `--type` option. The stub `_list_cards_impl()` raises `NotImplementedError`.
- `scanner.py` fully implemented: `scan_cards(data_dir: Path) -> dict[str, CardRef]`, `CardRef(NamedTuple)` with `.path: Path` and `.card_type: str`.
- `config.py` has `DEFAULT_DATA_DIR: str = "data"`.
- `data/` directory exists at project root with `.gitkeep` — treat as effectively empty.
- All existing tests (24) must remain green.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/cli.py` | Add 3 imports, replace `_list_cards_impl` stub |
| `tests/test_cli.py` | Add 5 new list command tests |

### Exact `cli.py` Changes

**Add these imports** (after existing imports, before `__all__`):

```python
from pathlib import Path

from dnd_cards.config import DEFAULT_DATA_DIR
from dnd_cards.scanner import scan_cards
```

The full import block at the top of `cli.py` should become:

```python
import traceback
from pathlib import Path
from typing import NoReturn, Optional

import typer

from dnd_cards.composer import register_fonts
from dnd_cards.config import DEFAULT_DATA_DIR
from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
from dnd_cards.scanner import scan_cards
```

**Replace `_list_cards_impl` stub** with:

```python
def _list_cards_impl(type: Optional[str]) -> None:
    data_dir = Path(DEFAULT_DATA_DIR)
    if not data_dir.is_dir():
        return
    index = scan_cards(data_dir)
    entries = sorted(
        (ref.path.stem, ref.card_type)
        for ref in index.values()
        if type is None or ref.card_type == type
    )
    for stem, card_type in entries:
        typer.echo(f"{stem} [{card_type}]")
```

**Key implementation notes:**
- `Path(DEFAULT_DATA_DIR)` resolves relative to CWD at runtime — correct for CLI use
- `data_dir.is_dir()` guard handles missing data directory cleanly (exit 0, no output)
- `sorted(...)` on tuples sorts by first element (stem) then second (card_type) — alphabetical by stem ✓
- `typer.echo(f"{stem} [{card_type}]")` — format is `fireball [spells]` (stem, space, bracketed type)
- `--type` filter is case-sensitive: `--type spells` won't match a card_type of `Spells`
- No YAML content is read — scanner is path-only

### `test_cli.py` — New Tests to Add

The existing `test_cli.py` has 8 tests. Add these 5 new tests. Use `patch("dnd_cards.cli.scan_cards")` to inject controlled `CardRef` data — avoids filesystem dependency.

```python
from unittest.mock import patch

from dnd_cards.scanner import CardRef


def test_list_no_filter_shows_all_cards(runner: CliRunner) -> None:
    fake_index = {
        "spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells"),
        "conditions/frightened": CardRef(path=Path("data/en/conditions/frightened.yaml"), card_type="conditions"),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines == ["fireball [spells]", "frightened [conditions]"]


def test_list_type_filter_restricts_output(runner: CliRunner) -> None:
    fake_index = {
        "spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells"),
        "conditions/frightened": CardRef(path=Path("data/en/conditions/frightened.yaml"), card_type="conditions"),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list", "--type", "spells"])
    assert result.exit_code == 0
    assert "fireball [spells]" in result.output
    assert "frightened" not in result.output


def test_list_no_match_filter_empty_output(runner: CliRunner) -> None:
    fake_index = {
        "spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells"),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list", "--type", "conditions"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_list_missing_data_dir_returns_empty(runner: CliRunner, tmp_path: Path) -> None:
    nonexistent = tmp_path / "no-such-dir"
    with patch("dnd_cards.cli.Path", return_value=nonexistent):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_list_output_sorted_alphabetically(runner: CliRunner) -> None:
    fake_index = {
        "spells/zebra": CardRef(path=Path("data/en/spells/zebra.yaml"), card_type="spells"),
        "spells/apple": CardRef(path=Path("data/en/spells/apple.yaml"), card_type="spells"),
        "spells/mango": CardRef(path=Path("data/en/spells/mango.yaml"), card_type="spells"),
    }
    with patch("dnd_cards.cli.scan_cards", return_value=fake_index):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().splitlines()
    assert lines == ["apple [spells]", "mango [spells]", "zebra [spells]"]
```

**Note on `test_list_missing_data_dir_returns_empty`:** Patching `dnd_cards.cli.Path` replaces the entire `Path` class in the cli module, which works but affects all `Path()` calls in that invocation. An alternative approach is to use a `tmp_path` that is a real directory but pass its path as `DEFAULT_DATA_DIR`. The cleanest approach is to patch `dnd_cards.cli.DEFAULT_DATA_DIR`:

```python
def test_list_missing_data_dir_returns_empty(runner: CliRunner, tmp_path: Path) -> None:
    nonexistent = str(tmp_path / "no-such-dir")
    with patch("dnd_cards.cli.DEFAULT_DATA_DIR", nonexistent):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output.strip() == ""
```

Use the `DEFAULT_DATA_DIR` patch approach — it's cleaner and doesn't interfere with other `Path()` calls.

### Existing `test_cli.py` Structure

The existing file imports and fixtures look like:

```python
"""Tests for CLI entry point."""
from pathlib import Path
from unittest.mock import patch
import pytest
from typer.testing import CliRunner
from dnd_cards.cli import app

@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
```

Check `tests/test_cli.py` before adding tests — the `runner` fixture and `Path` import may already be present. Add imports for `CardRef` from `dnd_cards.scanner`.

### Architecture Constraints

- **Patch `dnd_cards.cli.scan_cards`** (where it's used), not `dnd_cards.scanner.scan_cards`
- **Patch `dnd_cards.cli.DEFAULT_DATA_DIR`** (string constant) for missing-dir test
- **No YAML parsing** in list command — scanner is path-only
- **Absolute imports** — `from dnd_cards.scanner import CardRef` (ruff TID252)
- **`pathlib.Path` everywhere** — `Path(DEFAULT_DATA_DIR)` not string

### Regression Safeguard

All 24 existing tests must remain green. Only `cli.py` and `test_cli.py` are modified.

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 24 (passing)

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: Unfiltered `dnd-cards list` shows all cards as `{stem} [{card_type}]` lines, sorted alphabetically, exit 0
- ✅ AC2: `--type spells` restricts output to matching card_type only
- ✅ AC3: No-match filter returns empty stdout, exit 0
- ✅ AC4: Missing `data/` directory returns empty stdout, exit 0 (is_dir guard)
- ✅ AC5: Output sorted alphabetically by stem via `sorted()` on (stem, card_type) tuples
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 29/29 passed (5 new + 24 regressions all green)

### File List

- `src/dnd_cards/cli.py`
- `tests/test_cli.py`

### Change Log

- 2026-04-11: Implemented `_list_cards_impl()` with `scan_cards` + sort + type filter; 5 list tests added. All ACs satisfied.

### Review Findings

- [x] [Review][Patch] No test covering `scan_cards` raising an exception from the `list` command — added `test_list_scan_error_exits_2` verifying exit code 2 [tests/test_cli.py] — fixed
- [x] [Review][Defer] `DEFAULT_DATA_DIR` relative path resolves relative to CWD — deferred, pre-existing design decision, tool is expected to run from project root
- [x] [Review][Defer] `--type` filter is case-sensitive with no normalisation — deferred, pre-existing, types are directory names (case-sensitive on most filesystems)

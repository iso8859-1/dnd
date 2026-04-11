---
story_id: "1.2"
story_key: "1-2-error-hierarchy-and-exit-code-infrastructure"
epic: "Epic 1: Foundation & Card Data"
status: "done"
created: "2026-04-11"
---

# Story 1.2: Error Hierarchy & Exit Code Infrastructure

## Story

As a developer,
I want the complete `DndCardsError` exception hierarchy and CLI error handling in place,
so that all subsequent stories can raise typed errors and have them correctly routed to stderr with the right exit code.

---

## Acceptance Criteria

**AC1 — Error hierarchy already complete (verify, no changes needed):**
- **Given** `errors.py` is imported
- **Then** `YamlParseError`, `ValidationError`, `CardNotFoundError`, `GenerationError` are all subclasses of `DndCardsError`

**AC2 — Exit code routing in `cli.py`:**
- **Given** this exit code table is implemented in `cli.py`:

| Exception | Exit code |
|---|---|
| `YamlParseError` | 1 |
| `ValidationError` | 1 |
| `CardNotFoundError` | 1 |
| `GenerationError` | 2 |
| Any other `Exception` | 2 |

- **When** any of these exceptions is raised from a domain module
- **Then** the exception message is written to **stderr** (not stdout)
- **And** the process exits with the corresponding code above

**AC3 — Unexpected exception handling:**
- **Given** an unexpected exception (not a `DndCardsError` subclass) propagates to the CLI
- **When** it reaches the catch boundary in `cli.py`
- **Then** the full traceback is written to **stderr**
- **And** the process exits with code 2

**AC4 — Successful command exits 0:**
- **Given** a successful command completes
- **When** it exits
- **Then** the process exits with code 0

---

## Tasks / Subtasks

- [x] Task 1: Update `cli.py` with error routing (AC: 2, 3, 4)
  - [x] Add imports: `traceback`, `NoReturn`, `YamlParseError`, `ValidationError`, `CardNotFoundError`, `GenerationError`
  - [x] Implement `_handle_dnd_error(exc: BaseException) -> NoReturn`
  - [x] Refactor `generate`, `validate`, `list_cards` to use `_generate_impl`, `_validate_impl`, `_list_cards_impl` with error wrapping
- [x] Task 2: Add error routing tests to `test_cli.py` (AC: 2, 3)
  - [x] Test each `DndCardsError` subclass routes to correct exit code
  - [x] Test unexpected exception exits 2 with traceback in output
  - [x] Confirm existing tests still pass (test_help_shows_subcommands, test_version)
- [x] Task 3: Run full validation suite (AC: all)
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions)

---

## Dev Notes

### What Is Already Done — DO NOT Touch These

**`errors.py` is complete from Story 1.1.** AC1 is already satisfied. The hierarchy:
```python
class DndCardsError(Exception): ...
class YamlParseError(DndCardsError): ...
class ValidationError(DndCardsError): ...
class CardNotFoundError(DndCardsError): ...
class GenerationError(DndCardsError): ...
```
Do NOT modify `errors.py`. Do NOT modify any other module except `cli.py`. `test_errors.py` already has `test_error_hierarchy()` — leave it as-is.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/cli.py` | Add imports, `_handle_dnd_error`, refactor 3 commands |
| `tests/test_cli.py` | Add error routing tests |

### Exact Implementation Pattern for `cli.py`

**New imports to add:**
```python
import traceback
from typing import NoReturn, Optional

from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
```

Remove the `DndCardsError` import if not explicitly needed — ruff F401 will flag unused imports.

**Add `_handle_dnd_error` function (before the `@app.callback()`):**
```python
def _handle_dnd_error(exc: BaseException) -> NoReturn:
    """Route exception to stderr + raise typer.Exit with correct code."""
    if isinstance(exc, (YamlParseError, ValidationError, CardNotFoundError)):
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    if isinstance(exc, GenerationError):
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    # Unexpected exception — full traceback to stderr
    typer.echo(traceback.format_exc(), err=True)
    raise typer.Exit(2)
```

`-> NoReturn` is correct: function always raises `typer.Exit`. mypy --strict accepts this.

**Refactor each subcommand** to delegate to a `_xxx_impl` function and wrap with error handling:

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


@app.command()
def validate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
) -> None:
    """Validate a deck profile without generating a PDF."""
    try:
        _validate_impl(deck)
    except Exception as exc:
        _handle_dnd_error(exc)


def _validate_impl(deck: str) -> None:
    """Implementation in Story 3.2."""
    raise NotImplementedError


@app.command(name="list")
def list_cards(
    type: Optional[str] = typer.Option(None, "--type", help="Filter by card type."),
) -> None:
    """List available cards in the data store."""
    try:
        _list_cards_impl(type)
    except Exception as exc:
        _handle_dnd_error(exc)


def _list_cards_impl(type: Optional[str]) -> None:
    """Implementation in Story 1.5."""
    raise NotImplementedError
```

**Important:** `_generate_impl`, `_validate_impl`, `_list_cards_impl` are private (underscore prefix). Do NOT add them to `__all__`. Keep `__all__ = ["app"]`.

**`register_fonts()` call stays in `main()` callback** — do not move it. The callback runs before any subcommand.

### traceback.format_exc() — Why This Works

`traceback.format_exc()` captures the active exception on the current thread stack. When `_handle_dnd_error(exc)` is called from within `except Exception as exc:`, the exception is still active, so `format_exc()` correctly captures the full traceback. This is standard Python behavior.

### mypy --strict Compliance Notes

- `_handle_dnd_error() -> NoReturn` — valid, function always raises `typer.Exit`
- `_generate_impl(deck: str) -> None` with `raise NotImplementedError` — valid, `raise` is compatible with any return type
- `except Exception as exc: _handle_dnd_error(exc)` — `exc` is `Exception` (subclass of `BaseException`), so passing to `BaseException` param is fine
- `Optional` and `NoReturn` must be imported from `typing`

### Testing Pattern — Using `unittest.mock.patch`

The `_generate_impl`, `_validate_impl`, `_list_cards_impl` functions exist specifically to enable test injection. Patch them to raise specific errors:

```python
from unittest.mock import patch
from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
from typer.testing import CliRunner
from dnd_cards.cli import app

runner = CliRunner()


def test_generate_yaml_parse_error_exits_1() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=YamlParseError("bad.yaml: YAML syntax error at line 1: ..."),
    ):
        result = runner.invoke(app, ["generate", "--deck", "bad.yaml"])
    assert result.exit_code == 1
    assert "bad.yaml" in result.output  # CliRunner mixes stderr into output by default


def test_generate_unexpected_error_exits_2() -> None:
    with patch(
        "dnd_cards.cli._generate_impl",
        side_effect=RuntimeError("something broke"),
    ):
        result = runner.invoke(app, ["generate", "--deck", "test.yaml"])
    assert result.exit_code == 2
    assert "RuntimeError" in result.output  # traceback includes class name
```

`CliRunner()` mixes stderr into `result.output` by default (`mix_stderr=True`). This makes it easy to assert both message content AND exit code in one result.

### Required Tests for Story 1.2

At minimum, add these to `tests/test_cli.py`:

| Test | Exception | Expected exit code |
|---|---|---|
| `test_generate_yaml_parse_error_exits_1` | `YamlParseError` | 1 |
| `test_generate_validation_error_exits_1` | `ValidationError` | 1 |
| `test_generate_card_not_found_error_exits_1` | `CardNotFoundError` | 1 |
| `test_generate_generation_error_exits_2` | `GenerationError` | 2 |
| `test_generate_unexpected_error_exits_2` | `RuntimeError` | 2 |
| `test_unexpected_error_writes_traceback` | `RuntimeError` | traceback in output |

Test through `generate` command (most straightforward to patch). You don't need to also test via `validate` and `list_cards` — the error routing code is shared.

### Architecture Constraints (Mandatory)

- **Domain modules raise, never print, never `sys.exit()`** — `cli.py` is the ONLY catch boundary
- **Errors → stderr**: use `typer.echo(..., err=True)` — never `typer.echo(...)` for error messages
- **Absolute imports only**: `from dnd_cards.errors import ...` (ruff TID252 enforced)
- **`__all__`**: must remain `["app"]` in cli.py — private helpers excluded

### Regression Safeguard

These existing tests from Story 1.1 MUST still pass after your changes:
- `test_help_shows_subcommands` — `dnd-cards --help` shows `generate`, `validate`, `list`
- `test_version` — `dnd-cards --version` returns `dnd-cards 0.1.0`
- `test_error_hierarchy` (in test_errors.py) — unchanged

Note: `test_help_shows_subcommands` and `test_version` invoke the real CLI without triggering domain calls, so the new error wrapping has no impact.

### Story Scope Boundaries

**IN scope:**
- `cli.py` error routing (`_handle_dnd_error`, try/except wrappers, `_xxx_impl` stubs)
- `test_cli.py` error routing tests

**OUT of scope:**
- Actual command implementations (those are Stories 2.4, 3.2, 1.5)
- Any changes to `errors.py`, `models.py`, `config.py`, `loader.py`, `scanner.py`, `renderer.py`, `composer.py`
- Error message FORMAT (e.g. `"{file}: YAML syntax error at line {n}"`) — that's enforced in loader.py (Stories 1.3, 2.1)

### Project Context

- **Installed stack:** Python 3.11.9, typer 0.24.1, click 8.3.2, mypy 1.20.0, ruff 0.15.10, pytest 9.0.3
- **Run tests:** `uv run pytest -v`
- **Run linting:** `uv run ruff check src/`
- **Run type check:** `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: `errors.py` hierarchy verified — unchanged from Story 1.1, all 4 subclasses confirmed subclasses of `DndCardsError`
- ✅ AC2: Exit code routing in `cli.py` — `_handle_dnd_error()` maps YamlParseError/ValidationError/CardNotFoundError→1, GenerationError→2
- ✅ AC3: Unexpected exceptions write `traceback.format_exc()` to stderr + exit 2 (tested with `RuntimeError`)
- ✅ AC4: Successful commands exit 0 (verified via `test_help_shows_subcommands`, `test_version`)
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 10 passed (6 new error routing tests + 4 regressions all green)
- Note: `_generate_impl`, `_validate_impl`, `_list_cards_impl` private stubs added as testability hooks for future stories

### File List

- `src/dnd_cards/cli.py`
- `tests/test_cli.py`

### Change Log

- 2026-04-11: Added `_handle_dnd_error()` error routing, `_xxx_impl` stubs, 6 error routing tests. All ACs satisfied.

### Review Findings

- [x] [Review][Patch] `test_error_hierarchy` tested only `issubclass`; added `test_error_instantiation_and_message` [tests/test_errors.py] — fixed
- [x] [Review][Defer] Error classes carry no structured fields (path, line, field) despite docstring promises — deferred, pre-existing, future enhancement
- [x] [Review][Defer] `_generate_impl`/`_validate_impl` accept `str` not `Path` — deferred, pre-existing, Stories 2.4/3.2 scope
- [x] [Review][Defer] `DndCardsError` not re-exported from package `__init__.py` — deferred, pre-existing, minor public API gap

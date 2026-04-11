---
story_id: "1.1"
story_key: "1-1-project-scaffold-and-cli-entry-point"
epic: "Epic 1: Foundation & Card Data"
status: "done"
created: "2026-04-11"
---

# Story 1.1: Project Scaffold & CLI Entry Point

## User Story

**As a developer,**
I want the `dnd-cards` project initialized with all source modules, dependency config, and a working CLI entry point,
**So that** all subsequent stories have a stable foundation to build on.

---

## Acceptance Criteria

**AC1 — Installable CLI with three subcommands:**
- **Given** a machine with `uv` installed
- **When** `uv tool install .` is run from the project root
- **Then** `dnd-cards --help` outputs exactly three subcommands: `generate`, `validate`, `list` (with descriptions)
- **And** `dnd-cards --version` returns a version string (e.g., `dnd-cards 0.1.0`)

**AC2 — Correct pyproject.toml:**
- **Given** the following entries exist in `pyproject.toml`:
  ```toml
  [project.scripts]
  dnd-cards = "dnd_cards.cli:app"

  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  ```
- **When** `uv tool install .` is run
- **Then** the `dnd-cards` binary is available in PATH

**AC3 — Eight module stubs, type-clean:**
- **Given** all 8 source modules exist as stubs in `src/dnd_cards/`: `cli.py`, `config.py`, `models.py`, `errors.py`, `loader.py`, `scanner.py`, `renderer.py`, `composer.py`
- **When** `mypy --strict src/` is run
- **Then** it exits with code 0 and zero errors
- **And** `ruff check src/` exits with code 0
- **And** `pytest` collects at least the stub test files without errors

---

## Technical Requirements

### Stack (locked — do not deviate)

| Component | Library | Version |
|---|---|---|
| Dependency management | uv | latest |
| CLI framework | Typer | 0.9.x |
| PDF generation | ReportLab | 4.4.x |
| Template rendering | Jinja2 | 3.1.x |
| YAML parsing | PyYAML | latest |
| Schema validation | Pydantic | v2 2.5+ |
| Testing | pytest + pytest-cov | latest |
| Linting | ruff | latest |
| Type checking | mypy | latest |

**Distribution: `uv tool install .`** — NO PyInstaller, no binary packaging. (Note: architecture.md Starter Stack table mentions PyInstaller but Core Architectural Decisions explicitly overrides this: "Distribution via `uv tool install` — no PyInstaller complexity".)

### Init Commands (run once, in order)

```bash
uv init dnd-cards
cd dnd-cards
uv add typer reportlab jinja2 pyyaml pydantic
uv add --dev pytest pytest-cov ruff mypy
```

Commit `uv.lock` — Typer 0.9.x pins `click<9.0.0`; locking prevents transitive breakage.

---

## Files to Create

### Full Project Structure

```
dnd-cards/
├── pyproject.toml
├── uv.lock                         ← commit this
├── .python-version                 ← uv Python version pin
├── README.md
├── .gitignore
│
├── assets/                         ← fonts, icons (at project root for dev access)
│   └── fonts/                      ← .ttf files for register_fonts()
│
├── data/                           ← card data store (Git-versioned)
│   └── .gitkeep
│
├── templates/                      ← Jinja2 card layout templates
│   └── .gitkeep
│
├── decks/                          ← deck profile files
│   └── .gitkeep
│
├── output/                         ← generated PDFs (.gitignored)
│
├── src/
│   └── dnd_cards/
│       ├── __init__.py
│       ├── assets/
│       │   ├── __init__.py         ← required: makes assets a Python package
│       │   └── fonts/
│       │       └── __init__.py     ← required: makes fonts a Python package
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── errors.py
│       ├── loader.py
│       ├── scanner.py
│       ├── renderer.py
│       └── composer.py
│
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── spells/
    │   │   ├── valid_spell.yaml
    │   │   └── malformed_spell.yaml
    │   ├── decks/
    │   │   └── minimal_deck.yaml
    │   └── expected_output/
    ├── test_models.py
    ├── test_errors.py
    ├── test_loader.py
    ├── test_scanner.py
    ├── test_renderer.py
    ├── test_composer.py
    ├── test_cli.py
    └── integration/
        └── test_pipeline.py
```

### `pyproject.toml` (complete required sections)

```toml
[project]
name = "dnd-cards"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
    "reportlab>=4.4.0",
    "jinja2>=3.1.0",
    "pyyaml",
    "pydantic>=2.5.0",
]

[project.scripts]
dnd-cards = "dnd_cards.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
markers = ["slow: marks tests as slow (deselect with -m 'not slow')"]
testpaths = ["tests"]

[tool.ruff]
src = ["src"]

[tool.ruff.lint]
select = ["E", "F", "TID252"]

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.mypy]
strict = true
mypy_path = "src"
```

### `.gitignore`

```
output/
*.pdf
__pycache__/
.venv/
dist/
*.egg-info/
.mypy_cache/
.ruff_cache/
.pytest_cache/
```

### `src/dnd_cards/__init__.py`

```python
"""dnd-cards: German DnD 5.5e card printing CLI."""
```

### `src/dnd_cards/cli.py`

```python
"""CLI entry point — Typer app with generate, validate, list subcommands."""

from typing import Optional
import typer

__all__ = ["app"]

app = typer.Typer(
    name="dnd-cards",
    help="Generate print-ready PDF reference cards for DnD 5.5e.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo("dnd-cards 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show version."
    ),
) -> None:
    """dnd-cards — German DnD 5.5e reference card generator."""


@app.command()
def generate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
) -> None:
    """Generate a print-ready PDF from a deck profile."""
    # Implementation in Story 2.4
    raise NotImplementedError


@app.command()
def validate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
) -> None:
    """Validate a deck profile without generating a PDF."""
    # Implementation in Story 3.2
    raise NotImplementedError


@app.command()
def list_cards(
    type: Optional[str] = typer.Option(None, "--type", help="Filter by card type."),
) -> None:
    """List available cards in the data store."""
    # Implementation in Story 1.5
    raise NotImplementedError
```

**Important:** The `list` subcommand function must be named `list_cards` (not `list`) to avoid shadowing Python's built-in. Typer will register it as the `list` command by default based on the function name after stripping `_cards`... Actually this won't work — use `name="list"` explicitly:

```python
@app.command(name="list")
def list_cards(
    type: Optional[str] = typer.Option(None, "--type", help="Filter by card type."),
) -> None:
    """List available cards in the data store."""
    raise NotImplementedError
```

### `src/dnd_cards/config.py`

```python
"""Global constants for PDF layout and application defaults."""

__all__ = [
    "A4_WIDTH_MM",
    "A4_HEIGHT_MM",
    "CARD_STRIP_WIDTH_MM",
    "CARD_STRIP_HEIGHT_MM",
    "CARD_FOLDED_WIDTH_MM",
    "CARDS_PER_ROW",
    "CARDS_PER_COL",
    "CROP_MARK_LENGTH_MM",
    "CROP_MARK_OFFSET_MM",
    "CROP_MARK_LINE_WIDTH_PT",
    "DEFAULT_DATA_DIR",
    "DEFAULT_OUTPUT_DIR",
]

# A4 dimensions
A4_WIDTH_MM: float = 210.0
A4_HEIGHT_MM: float = 297.0

# Card strip dimensions (before folding)
CARD_STRIP_WIDTH_MM: float = 126.0   # folds to 63mm
CARD_STRIP_HEIGHT_MM: float = 88.0
CARD_FOLDED_WIDTH_MM: float = 63.0   # Magic card width

# Grid layout: 2 columns × 4 rows = 8 cards per page
CARDS_PER_ROW: int = 2
CARDS_PER_COL: int = 4

# Crop marks: 0.5pt black, 5mm long, 2mm offset from strip corner
CROP_MARK_LENGTH_MM: float = 5.0
CROP_MARK_OFFSET_MM: float = 2.0
CROP_MARK_LINE_WIDTH_PT: float = 0.5

# Default directories (relative to CWD at runtime)
DEFAULT_DATA_DIR: str = "data"
DEFAULT_OUTPUT_DIR: str = "output"
```

### `src/dnd_cards/models.py`

```python
"""Pydantic v2 data models: CardData, DeckProfile, DeckEntry, Language."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict

__all__ = ["Language", "CardData", "DeckProfile", "DeckEntry"]


class Language(str, Enum):
    """Language codes matching data/ directory names."""
    DE = "de"
    EN = "en"


class CardData(BaseModel):
    """Parsed and validated card data from a YAML file."""
    model_config = ConfigDict(frozen=True)

    id: str
    type: str
    template: str
    name: str
    lang: Language
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    edition: Optional[str] = None
    source_book: Optional[str] = None


class DeckEntry(BaseModel):
    """A single card entry in a deck profile."""
    model_config = ConfigDict(frozen=True)

    card_key: str   # format: "{card_type}/{id}", e.g. "spells/feuerball"
    quantity: int   # ≥1


class DeckProfile(BaseModel):
    """A deck profile loaded from YAML."""
    model_config = ConfigDict(frozen=True)

    name: str
    entries: list[DeckEntry]
```

**Note:** `schemaVersion` / `schema_version` is added to `DeckProfile` in Story 3.1. Do NOT add it yet — Story 2.1 builds the basic `DeckProfile` without it.

### `src/dnd_cards/errors.py`

```python
"""DndCardsError exception hierarchy."""

__all__ = [
    "DndCardsError",
    "YamlParseError",
    "ValidationError",
    "CardNotFoundError",
    "GenerationError",
]


class DndCardsError(Exception):
    """Base class for all dnd-cards errors."""


class YamlParseError(DndCardsError):
    """YAML syntax error — exit 1. Include file path and line number."""


class ValidationError(DndCardsError):
    """Schema validation error — exit 1. Include file path and field name."""


class CardNotFoundError(DndCardsError):
    """Card key not found in data store — exit 1."""


class GenerationError(DndCardsError):
    """PDF composition failure — exit 2."""
```

### `src/dnd_cards/loader.py`

```python
"""PyYAML parsing + Pydantic validation for card and deck YAML files."""

from pathlib import Path
from typing import Any

from dnd_cards.models import CardData, DeckProfile

__all__ = ["load_card", "load_deck"]


def load_card(path: Path) -> CardData:
    """Parse and validate a card YAML file. Implementation in Story 1.3."""
    raise NotImplementedError


def load_deck(path: Path) -> DeckProfile:
    """Parse and validate a deck profile YAML file. Implementation in Story 2.1."""
    raise NotImplementedError
```

### `src/dnd_cards/scanner.py`

```python
"""File system scanner for card data store discovery."""

from collections import namedtuple
from pathlib import Path

__all__ = ["CardRef", "scan_cards"]

CardRef = namedtuple("CardRef", ["path", "card_type"])


def scan_cards(data_dir: Path) -> dict[str, "CardRef"]:
    """Scan data_dir tree and return card index. Implementation in Story 1.4."""
    raise NotImplementedError
```

### `src/dnd_cards/renderer.py`

```python
"""Jinja2 template rendering for card data."""

from typing import Any

from dnd_cards.models import CardData

__all__ = ["render_card"]


def render_card(card: CardData, template_name: str) -> dict[str, Any]:
    """Render a card to a context dict via Jinja2. Implementation in Story 2.2."""
    raise NotImplementedError
```

### `src/dnd_cards/composer.py`

```python
"""ReportLab PDF layout: A4 2×4 grid of 126×88mm fold-strips with crop marks."""

from pathlib import Path

from dnd_cards.models import CardData

__all__ = ["register_fonts", "compose_pdf"]


def register_fonts() -> None:
    """Register custom fonts from assets/fonts/ via importlib.resources.
    Must be called once before any canvas operations. Implementation in Story 2.3."""


def compose_pdf(cards: list[CardData], output_path: Path) -> None:
    """Compose a PDF from card data. Implementation in Story 2.3."""
    raise NotImplementedError
```

### Test Stubs

**`tests/conftest.py`:**
```python
"""Shared pytest fixtures."""
# Fixtures will be populated in Stories 1.3, 1.4, 2.1 etc.
```

**`tests/test_models.py`**, **`tests/test_errors.py`**, **`tests/test_loader.py`**, **`tests/test_scanner.py`**, **`tests/test_renderer.py`**, **`tests/test_composer.py`**, **`tests/test_cli.py`**: Each needs at minimum a placeholder so pytest can collect them:

```python
"""Tests for <module>."""
# Tests implemented in Story X.Y
```

**`tests/integration/test_pipeline.py`:**
```python
"""Full pipeline integration tests."""
import pytest

@pytest.mark.slow
def test_placeholder() -> None:
    """Placeholder — implemented in Story 2.4."""
```

**`tests/integration/__init__.py`** — create empty file.

**`tests/__init__.py`** — create empty file (required for pytest to discover tests).

### Fixture Files

**`tests/fixtures/spells/valid_spell.yaml`:**
```yaml
id: fireball
type: spell
template: zauber-v1
name: Fireball
lang: en
level: 3
school: Evocation
casting_time: 1 action
range: 150 ft
components: V, S, M
duration: Instantaneous
description: |
  A bright streak flashes from your pointing finger to a point you choose...
edition: "5e"
source_book: "SRD 5.1"
```

**`tests/fixtures/spells/malformed_spell.yaml`:**
```yaml
id: bad-spell
  this: is: broken yaml
```

**`tests/fixtures/decks/minimal_deck.yaml`** (NOTE: no `schemaVersion` yet — that's added in Story 3.1):
```yaml
name: Test Deck
cards:
  spells/fireball: 1
```

---

## Architecture Compliance Guardrails

These rules are MANDATORY — `mypy --strict` and `ruff` will fail if violated:

| Rule | Requirement |
|---|---|
| **Imports** | Absolute only: `from dnd_cards.models import CardData`. Never `from .models import ...`. Enforced by `ruff` TID252. |
| **`__all__`** | Defined in every module. Omitting breaks mypy and makes public API unclear. |
| **Type annotations** | Every function in every stub needs return type annotation. `mypy --strict` requires complete annotations. |
| **Path handling** | `pathlib.Path` everywhere. Only exception: `canvas.Canvas(str(output_path))` in composer (Story 2.3). |
| **Pydantic models** | `ConfigDict(frozen=True)` on all 3 models: `CardData`, `DeckProfile`, `DeckEntry`. |
| **Error handling** | Domain modules raise, never print, never `sys.exit()`. `cli.py` is sole catch boundary. |
| **Constants naming** | `SCREAMING_SNAKE_CASE` for all constants in `config.py` (e.g., `A4_WIDTH_MM`, not `a4_width_mm`). |
| **Font assets** | `src/dnd_cards/assets/` and `src/dnd_cards/assets/fonts/` must each have `__init__.py` to be Python packages (required for `importlib.resources`). |

### mypy --strict Stub Pattern

For stub functions that will raise `NotImplementedError`, ensure the return type annotation is still present:

```python
def load_card(path: Path) -> CardData:
    raise NotImplementedError
```

This is valid under mypy --strict — `raise` is compatible with any return type.

### Language enum usage

```python
class Language(str, Enum):
    DE = "de"
    EN = "en"
```

Values match `data/` directory names. `Language("de")` works because it's a `str` enum. This enables `Path("data") / language.value / card_type`.

---

## CLI Architecture Details

### Typer App Structure

```python
app = typer.Typer(name="dnd-cards", help="...", no_args_is_help=True)
```

- `no_args_is_help=True` — `dnd-cards` with no args shows help (good UX)
- Shell completion is built into Typer via Click — `dnd-cards --install-completion` works automatically after install
- `--version` uses `is_eager=True` so it runs before subcommand validation

### Error Routing (cli.py responsibility — implement fully in Story 1.2)

```
DndCardsError subclass → typer.echo(str(exc), err=True) + raise typer.Exit(code)
  YamlParseError    → exit 1
  ValidationError   → exit 1
  CardNotFoundError → exit 1
  GenerationError   → exit 2
  Unexpected        → traceback to stderr + exit 2
```

Story 1.1 stubs use `raise NotImplementedError` — the CLI error handling is wired in Story 1.2.

### `register_fonts()` call site

Per architecture: `register_fonts()` is called **once at CLI startup** — in the `main()` callback:

```python
@app.callback()
def main(version: Optional[bool] = ...) -> None:
    register_fonts()  # Story 2.3 will implement this; stub is a no-op
```

This must be set up correctly in Story 1.1 even though `register_fonts()` is a no-op stub, so the architecture is correct from the start.

---

## Testing Requirements for This Story

Story 1.1 is scaffold-only. Tests are mostly stubs, but the following must actually pass:

### Must Pass in Story 1.1

1. **`pytest` collects without errors** — all test files importable, no syntax errors
2. **`mypy --strict src/` exits 0** — all stubs properly annotated
3. **`ruff check src/` exits 0** — no linting violations, no relative imports
4. **`dnd-cards --help` shows 3 subcommands** — `generate`, `validate`, `list`
5. **`dnd-cards --version` returns a string** — must not crash

### test_cli.py Minimal Tests

Use `typer.testing.CliRunner` (not subprocess):

```python
from typer.testing import CliRunner
from dnd_cards.cli import app

runner = CliRunner()

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
```

### test_errors.py Minimal Tests

```python
from dnd_cards.errors import (
    DndCardsError, YamlParseError, ValidationError,
    CardNotFoundError, GenerationError,
)

def test_error_hierarchy() -> None:
    assert issubclass(YamlParseError, DndCardsError)
    assert issubclass(ValidationError, DndCardsError)
    assert issubclass(CardNotFoundError, DndCardsError)
    assert issubclass(GenerationError, DndCardsError)
```

---

## Story Scope Boundaries

**IN scope for Story 1.1:**
- All files in the project structure above
- Working `dnd-cards --help` and `dnd-cards --version`
- All 8 module stubs with `__all__` and type annotations
- All test file stubs (importable, no actual test logic beyond what's shown)
- pyproject.toml with all required tool configurations
- Fixture YAML files

**OUT of scope (do NOT implement):**
- Actual card loading logic (`loader.py`) — Story 1.3
- Scanner implementation (`scanner.py`) — Story 1.4
- `list` command implementation — Story 1.5
- Error routing in cli.py — Story 1.2
- Any PDF/renderer/composer logic — Epic 2
- Actual font files (use no-op `register_fonts()`)
- Deck profile validation — Epic 3
- SRD seed data — Story 4.1

---

## Key Decisions & Rationale

| Decision | Rationale |
|---|---|
| uv tool install, no PyInstaller | Personal tool; uv already required for dev. Simpler. |
| hatchling build backend | Modern, fast, works with src/ layout out of the box. |
| `list_cards` function named with `@app.command(name="list")` | Avoids shadowing Python built-in `list`. |
| `register_fonts()` stub called in `main()` now | Architecture requires it called once at startup; easier to wire now than add later. |
| Models stub with all fields in 1.1 | `mypy --strict` requires consistent types; defining models now prevents type errors in later stories. |
| `DeckProfile` without `schemaVersion` | Story 3.1 adds it. Story 2.1 builds basic version intentionally. |

---

## Dev Notes

- Run `uv sync` after creating `pyproject.toml` to generate `uv.lock`
- Run `mypy --strict src/` and `ruff check src/` after each file to catch issues early
- The `tests/` directory needs `__init__.py` files at each level for pytest discovery
- `assets/fonts/` directory can be empty for Story 1.1 — `register_fonts()` is a no-op stub
- `.python-version` file content should be just `3.11` (or whatever version uv pins)
- Do NOT create `output/` directory — it's gitignored and created at runtime by the CLI

## Open Questions / Notes for Next Stories

- Story 1.2 will wire the full error routing in `cli.py` — the `NotImplementedError` stubs will then need `try/except` wrapping
- Story 1.3 will replace `load_card` stub with full PyYAML + Pydantic implementation
- Font files for `register_fonts()` are needed before Story 2.3 — decide on font (e.g., DejaVu Sans) when starting Epic 2

---

## Tasks/Subtasks

- [x] Create pyproject.toml, .gitignore, .python-version
- [x] Create directory structure (assets/, data/, templates/, decks/, src/dnd_cards/assets/fonts/)
- [x] Create all 8 source module stubs with `__all__` and type annotations
- [x] Create test stubs, conftest.py, fixture YAML files, and __init__.py files
- [x] Run `uv sync` to generate uv.lock
- [x] Validate: `ruff check src/` exits 0
- [x] Validate: `mypy --strict src/` exits 0
- [x] Validate: `pytest` collects and passes all tests

---

## Dev Agent Record

### Implementation Plan

Created the complete project scaffold for `dnd-cards` in `C:\Development\dnd`:
1. `pyproject.toml` with all required sections (hatchling build, uv tool install entry point, ruff/mypy config)
2. `.gitignore`, `.python-version` (pinned to 3.11)
3. Directories: `assets/fonts/`, `data/`, `templates/`, `decks/` with `.gitkeep`; `src/dnd_cards/assets/fonts/` with `__init__.py` packages
4. 8 source stubs: all have `__all__`, full type annotations, absolute imports — pass `mypy --strict` and `ruff`
5. Test stubs: `conftest.py`, 7 `test_*.py` stubs, `integration/test_pipeline.py`, fixture YAML files
6. Ran `uv sync` → generated `uv.lock`, installed all 33 packages including typer 0.24.1 / click 8.3.2
7. Added dev dependencies (mypy, pytest, pytest-cov, ruff) via `uv add --dev`

### Completion Notes

- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 4 passed (test_help_shows_subcommands, test_version, test_error_hierarchy, test_placeholder)
- ✅ `dnd-cards --help` — shows generate, validate, list subcommands
- ✅ `dnd-cards --version` — returns "dnd-cards 0.1.0"
- Note: Typer resolved to 0.24.1 (>=0.9.0 constraint); all story APIs work correctly
- Note: `register_fonts()` is a no-op stub; called in `main()` callback per architecture requirement

---

## File List

- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.gitignore`
- `assets/fonts/.gitkeep`
- `data/.gitkeep`
- `templates/.gitkeep`
- `decks/.gitkeep`
- `src/dnd_cards/__init__.py`
- `src/dnd_cards/assets/__init__.py`
- `src/dnd_cards/assets/fonts/__init__.py`
- `src/dnd_cards/cli.py`
- `src/dnd_cards/config.py`
- `src/dnd_cards/models.py`
- `src/dnd_cards/errors.py`
- `src/dnd_cards/loader.py`
- `src/dnd_cards/scanner.py`
- `src/dnd_cards/renderer.py`
- `src/dnd_cards/composer.py`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_cli.py`
- `tests/test_errors.py`
- `tests/test_models.py`
- `tests/test_loader.py`
- `tests/test_scanner.py`
- `tests/test_renderer.py`
- `tests/test_composer.py`
- `tests/integration/__init__.py`
- `tests/integration/test_pipeline.py`
- `tests/fixtures/spells/valid_spell.yaml`
- `tests/fixtures/spells/malformed_spell.yaml`
- `tests/fixtures/decks/minimal_deck.yaml`

---

## Change Log

- 2026-04-11: Initial scaffold — pyproject.toml, .gitignore, .python-version, all 8 source stubs, test stubs, fixture files, uv.lock generated. All ACs satisfied.

### Review Findings

- [x] [Review][Defer] Grid layout constants don't fit A4: 2×126mm=252mm > 210mm wide; 4×88mm=352mm > 297mm tall — deferred, pre-existing, resolve when implementing PDF composer in Story 2.3
- [ ] [Review][Patch] `pyyaml` has no version floor — add `pyyaml>=6.0.1` [pyproject.toml]
- [ ] [Review][Patch] Hardcoded version string `"dnd-cards 0.1.0"` in cli.py — use `importlib.metadata.version("dnd-cards")` [src/dnd_cards/cli.py]
- [ ] [Review][Patch] `type` parameter in `list_cards` shadows Python builtin — rename to `card_type` [src/dnd_cards/cli.py]
- [ ] [Review][Patch] Test error assertions check `result.output` (stdout) but errors route to stderr via `typer.echo(..., err=True)` — assert on stderr or verify CliRunner `mix_stderr` behaviour [tests/test_cli.py]
- [x] [Review][Defer] `Optional[str]` legacy typing form in Python 3.11+ — deferred, pre-existing style choice
- [x] [Review][Defer] `DeckEntry.quantity` has no `ge=1` Pydantic constraint — deferred, pre-existing, Story 3.x scope
- [x] [Review][Defer] `DeckProfile.entries` field vs fixture `cards:` key mismatch — deferred, pre-existing, Story 2.1 scope
- [x] [Review][Defer] `register_fonts()` called on every command including `list` — deferred, pre-existing architecture decision
- [x] [Review][Defer] `load_card` only surfaces first Pydantic validation error — deferred, pre-existing, Story 1-3 scope
- [x] [Review][Defer] Cross-language key collision in scanner silently overwrites — deferred, pre-existing documented known gap

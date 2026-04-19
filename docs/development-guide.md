# dnd-cards — Development Guide

**Generated:** 2026-04-12

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package and project manager)
- Python 3.11+ (uv manages this via `.python-version`)

---

## Initial Setup

```bash
# Clone the repo
git clone <repo-url>
cd dnd-cards

# Install all dependencies (creates .venv automatically)
uv sync

# Install the CLI into your PATH
uv tool install .
```

---

## Running the CLI

```bash
# List all available cards
dnd-cards list

# List only spells
dnd-cards list --type spells

# Generate a PDF from a deck profile
dnd-cards generate --deck decks/example.yaml

# Generate with a custom output directory
dnd-cards generate --deck decks/example.yaml --output-dir /tmp/output

# Open the interactive TUI deck builder
dnd-cards tui

# Edit an existing deck in the TUI
dnd-cards tui decks/example.yaml
```

---

## TUI Usage

The `dnd-cards tui` command opens a full-screen terminal deck builder.

| Key | Action |
|---|---|
| **Type** | Filter cards by name (fuzzy/subsequence match) |
| **+** | Add one copy of the highlighted card to deck; clears search |
| **-** | Remove one copy of the highlighted card |
| **F1**–**F4** | Toggle language filter (auto-detected from `data/` directory) |
| **1**–**9** | Toggle card type filter (auto-detected from card type dirs) |
| **Escape** | Clear search input |
| **Ctrl+S** | Save deck YAML to `decks/{name}.yaml` |
| **q** | Quit |

---

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=dnd_cards --cov-report=term-missing

# Run only fast tests (exclude slow integration tests)
uv run pytest -m "not slow"

# Run a specific test file
uv run pytest tests/test_models.py

# Run TUI tests only
uv run pytest tests/test_tui.py
```

### Test structure

| File | What it tests |
|---|---|
| `test_models.py` | Pydantic model validation, Language enum, frozen behaviour |
| `test_errors.py` | Exception class hierarchy |
| `test_loader.py` | `load_card()`, `load_deck()`, YAML error handling |
| `test_scanner.py` | `scan_cards()`, directory traversal |
| `test_renderer.py` | `render_card()`, template validation, context dict |
| `test_composer.py` | `compose_pdf()` with `BytesIO` canvas; drawing helpers |
| `test_cli.py` | CLI subcommands via `typer.testing.CliRunner` |
| `test_tui.py` | TUI via `textual.testing.Pilot` (async, `asyncio_mode=auto`) |
| `integration/test_pipeline.py` | Full CLI → PDF smoke test (marked `slow`) |

---

## Linting and Type Checking

```bash
# Lint with ruff
uv run ruff check src/ tests/

# Auto-fix ruff issues
uv run ruff check --fix src/ tests/

# Type check with mypy (strict)
uv run mypy src/
```

### Enforcement rules

- `TID252` — relative imports are banned; always use `from dnd_cards.module import ...`
- `mypy --strict` — 100% type annotation coverage required
- No exceptions from these rules are expected; any new module must pass both checks

---

## Adding a New Card Type

1. Create a Jinja2 template: `templates/{type}-v{n}.jinja2`
   - The template content is a text representation (used as a presence marker; actual rendering is in `composer.py`)
2. Add YAML card files: `data/{lang}/{rulebook}/{type}/{id}.yaml`
   - Required fields: `id`, `type`, `template`, `name`, `lang`, `description`
   - `type` must match the directory name
   - `template` must match the Jinja2 file stem
3. Add color/icon in `composer.py`:
   - Add entry to `_CARD_COLORS` dict
   - Add branch in `_draw_back_icon()` if a custom icon is needed
   - Add branch in `_draw_strip()` if the front face layout differs from the generic layout

No changes to `scanner.py`, `loader.py`, `models.py`, or `cli.py` are needed.

---

## Adding Card Data via Scripts

```bash
# Import talents and rules from SRD YAML source files into data/
uv run python scripts/import_srd_data.py

# Convert raw SRD spells YAML into per-card files
uv run python scripts/convert_srd_spells.py
```

---

## Deck Profile YAML Format

```yaml
name: My Deck
cards:
  spells/feuerball: 2      # {card_type}/{id}: quantity
  spells/blitz: 1
  talents/ringer: 3
  rules/abenteuer: 1
```

- Keys are `{card_type}/{stem}` matching the directory structure under `data/`
- Quantities must be positive integers

---

## Project Configuration

All project configuration is in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"          # required for Textual pilot tests
markers = ["slow: ..."]

[tool.ruff.lint]
select = ["E", "F", "TID252"]  # TID252 = ban relative imports

[tool.mypy]
strict = true
mypy_path = "src"

[[tool.mypy.overrides]]
module = ["reportlab.*", "textual.*"]
ignore_missing_imports = true  # no type stubs for these libraries
```

---

## Dependency Management

```bash
# Add a production dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>

# Update lockfile after pyproject.toml edits
uv lock

# Sync environment with lockfile
uv sync
```

The `uv.lock` file is committed to prevent version drift (Typer 0.9.x pins `click<9.0.0`).

---

## Distribution

```bash
# Install as a uv tool (makes dnd-cards available in PATH)
uv tool install .

# Uninstall
uv tool uninstall dnd-cards
```

No binary packaging (PyInstaller) is planned; `uv tool install` is the supported deployment model.

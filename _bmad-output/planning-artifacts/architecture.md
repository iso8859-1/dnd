---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
status: 'complete'
completedAt: '2026-04-10'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md']
workflowType: 'architecture'
project_name: 'dnd'
user_name: 'Tobias'
date: '2026-04-10'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:** 32 FRs across 7 capability areas — card data management, deck profile management, PDF generation, validation & error handling, card discovery, template system, CLI interface & shell integration, language & content support.

**Non-Functional Requirements driving decisions:**
- PDF generation <10s for 10-20 cards on a standard desktop
- `validate` <2s, `list` <1s
- No silent failures — all errors explicit with file path and line number
- New card type = new template file + YAML schema, zero generator code changes
- Deck profile format stable from v1 (breaking changes require explicit versioning)
- Cross-platform: Windows, macOS, Linux

**Scale & Complexity:**
- Primary domain: CLI tool + document generation
- Complexity level: Medium (precise PDF geometry, template-data decoupling, cross-platform portability)
- Estimated architectural components: ~6 (CLI parser, YAML loader/validator, file system scanner, template renderer, PDF composer, shell completion)

### Language & Runtime Decision

**Python + ReportLab** — selected based on:
- ReportLab provides mm-precise PDF geometry with no external browser dependency
- ~50–200ms per card render (well within the <10s constraint for 10-20 cards)
- Mature YAML ecosystem (`pyyaml`, `jsonschema`/`pydantic`)
- Strong cross-platform packaging (`PyInstaller` for single executable)
- Node.js/Puppeteer rejected: Chromium baseline 800ms+/page is too close to the 10s limit

### Technical Constraints & Dependencies

- **PDF library:** ReportLab (mm-precise, no external process, mature)
- **PDF library chosen first** — template engine selection follows from this
- **No network, no server, no auth** — pure local file I/O
- **File paths:** `pathlib.Path` everywhere — no string concatenation
- **Schema versioning:** `schemaVersion: 1` field in deck YAML from v1 to enable future migration

### Cross-Cutting Concerns Identified

1. **YAML validation** — strict schema validation with named errors (field, expected type, actual value, file path, line number) for both card data and deck profiles
2. **File system discovery** — runtime scanning of `data/{lang}/{type}/` tree; no hard-coded card references
3. **Template rendering pipeline** — file-based templates only (no embedded YAML strings); template discovery via directory scan
4. **PDF geometry precision** — reference PDF comparison tests per template needed for cross-platform regression
5. **Cross-platform packaging** — shell completion registration differs per OS/shell; single executable via PyInstaller

## Starter Stack

### Accepted Stack

| Component | Library | Notes |
|---|---|---|
| Dependency management | uv | Fast, deterministic, lockfile committed |
| CLI framework | Typer 0.9.x | Shell completion via Click; lock full dep tree on first `uv lock` |
| PDF generation | ReportLab 4.4.x | mm-precise geometry; `.spec` file required for PyInstaller (font hiddenimports) |
| Template rendering | Jinja2 3.1.x | File-based templates; must be bundled via `--add-data` in PyInstaller build |
| YAML parsing | PyYAML | Sufficient for read-only YAML; syntax errors include `problem_mark` line/col |
| Schema validation | Pydantic v2 2.5 | `Model.model_validate(dict)` directly from PyYAML output — no bridge library |
| Testing | pytest + pytest-cov | Coverage gating from first test run |
| Packaging | PyInstaller | `--onefile` acceptable for personal tool; requires explicit `.spec` for ReportLab |

### Rejected / Dropped

- `pydantic-yaml` — unmaintained wrapper; Pydantic's `model_validate()` on a plain dict is sufficient
- `ruamel.yaml` — round-trip and YAML 1.2 compliance not needed; PyYAML is simpler with no namespace package issues

### Init Command

```bash
uv init dnd-cards
cd dnd-cards
uv add typer reportlab jinja2 pyyaml pydantic
uv add --dev pytest pyinstaller pytest-cov
```

### Key Implementation Notes

- Commit `uv.lock` — Typer 0.9.x pins `click<9.0.0`; lock prevents transitive breakage
- ReportLab canvas injected as parameter in renderer (enables `BytesIO` in unit tests, no disk I/O)
- Jinja2 templates loaded from disk → must be bundled via `--add-data` in PyInstaller `.spec`
- Python's `logging` module configured at startup — structured output for layout debugging

## Implementation Patterns & Consistency Rules

### Naming Patterns

**YAML field names:** `snake_case` — maps directly to Python identifiers; no Pydantic alias boilerplate
- Examples: `card_type`, `schema_version`, `source_book`, `casting_time`

**YAML file names:** `kebab-case` — matches deck profile card ID references
- Examples: `feuerball.yaml`, `magisches-geschoss.yaml`, `heilung-von-wunden.yaml`

**Python code:** PEP 8 throughout
- Functions, variables, modules: `snake_case`
- Pydantic models, exception classes: `PascalCase`
- Module-level constants: `SCREAMING_SNAKE_CASE` (e.g., `A4_WIDTH_MM`, `CARD_STRIP_HEIGHT_MM`, `DEFAULT_FONT_SIZE`)

### Structure Patterns

**Test location:** `tests/` at project root, mirroring `src/dnd_cards/`
```
tests/
  conftest.py         # shared fixtures: sample CardData, DeckProfile, tmp YAML paths
  test_loader.py
  test_scanner.py
  test_renderer.py
  test_composer.py
  test_cli.py
```

**Module coupling:** Thin `cli.py` — argument parsing, user feedback, exit codes only. Each subcommand delegates to one orchestration call into domain modules. No business logic in `cli.py`.

**Imports:** Absolute only — `from dnd_cards.models import CardData`. Enforced via `ruff` rule `TID252`.

**`__all__`:** Defined in each module — makes public API surfaces explicit, aids mocking in tests.

### Process Patterns

**Error handling contract:**
- Domain modules raise typed `DndCardsError` subclasses — never print, never call `sys.exit`
- `cli.py` is the single catch boundary — translates exceptions to `typer.echo(..., err=True)` + `raise typer.Exit(code)`
- Unexpected exceptions re-raised with traceback to stderr → exit 2

**Path handling:**
- `pathlib.Path` everywhere in application code
- Exception: `canvas.Canvas()` call site in `composer.py` — wrap with `str()` at that boundary only

**Pydantic models:** `model_config = ConfigDict(frozen=True)` for all data models loaded from YAML (`CardData`, `DeckProfile`, `DeckEntry`) — immutable after load

### Tooling & Enforcement

| Tool | Purpose |
|---|---|
| `ruff` | Linting + import enforcement (`TID252` bans relative imports) |
| `mypy --strict` | Type checking — 100% annotation coverage required |
| `pytest-cov` | Coverage gating from first test run |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Distribution via `uv tool install` — no PyInstaller packaging
- Flat module structure: `cli.py`, `loader.py`, `scanner.py`, `renderer.py`, `composer.py`, `models.py`, `errors.py`
- Exception hierarchy: `DndCardsError` base with 4 subclasses mapped to exit codes

**Deferred Decisions (Post-MVP):**
- Shell completion registration — Typer provides this automatically; OS-specific registration deferred until first real install
- PyInstaller binary — deferred indefinitely; `uv tool install` is sufficient for personal use

### Distribution & Packaging

- **`uv tool install .`** — installs `dnd-cards` into PATH via uv toolchain
- No binary packaging; no PyInstaller complexity
- User requirement: uv installed (already used for development)
- `uv.lock` committed — prevents Typer/Click version drift

### Module Architecture

```
src/dnd_cards/
  __init__.py
  cli.py        # Typer app + subcommands (generate, validate, list)
  loader.py     # PyYAML parsing + Pydantic validation
  scanner.py    # data/ folder discovery, card index building
  renderer.py   # Jinja2 template rendering (canvas injected as param)
  composer.py   # ReportLab PDF layout (A4, 2×4 grid, crop marks)
  models.py     # Pydantic models: CardData, DeckProfile, DeckEntry
  errors.py     # DndCardsError hierarchy
```

### Error Handling

```python
class DndCardsError(Exception): pass
class YamlParseError(DndCardsError): pass     # exit 1 — file + line from PyYAML problem_mark
class ValidationError(DndCardsError): pass    # exit 1 — file + field from Pydantic
class CardNotFoundError(DndCardsError): pass  # exit 1 — deck file + missing ID
class GenerationError(DndCardsError): pass    # exit 2 — PDF composition failure
```

- Internal modules raise, never print
- CLI layer owns all user-facing output — errors → stderr, success → stdout
- Unexpected exceptions → exit 2 + traceback to stderr

### Data Architecture

- **No database** — plain YAML files, Git-versioned
- **Card discovery:** runtime scan of `data/{lang}/{type}/{id}.yaml`; builds `dict[str, Path]` index per run
- **No caching** — dataset is small (<1s list requirement met by direct scan)
- **Deck profile:** `schemaVersion: 1` field from v1; breaking changes require explicit version bump

### Logging

- Python `logging` module configured at CLI startup
- `WARNING`+ to stderr by default; `--verbose` flag enables `DEBUG`
- No external logging library

## Project Structure & Boundaries

### Complete Project Directory Structure

```
dnd-cards/
├── pyproject.toml              # project config, scripts, ruff + mypy settings
├── uv.lock                     # committed — pins Typer/Click versions
├── .python-version             # uv Python version pin
├── README.md
├── .gitignore                  # output/, *.pdf, __pycache__/, .venv/, dist/
│
├── assets/                     # fonts, icons, static resources for PDF rendering
│   └── fonts/                  # .ttf files registered via register_fonts() at startup
│
├── data/                       # FR1-5, FR22-23, FR31 — card data store (Git-versioned)
│   ├── en/
│   │   └── spells/
│   │       ├── fireball.yaml
│   │       └── magic-missile.yaml
│   └── de/
│       └── spells/
│           └── feuerball.yaml
│
├── templates/                  # FR24-26 — Jinja2 card layout templates
│   └── zauber-v1.jinja2
│
├── decks/                      # FR6-9 — deck profile files
│   └── example-deck.yaml
│
├── output/                     # generated PDFs — .gitignored
│
├── src/
│   └── dnd_cards/
│       ├── __init__.py
│       ├── cli.py              # FR27-30 — Typer app, subcommands, shell completion
│       ├── config.py           # global constants: A4_WIDTH_MM, CARD_STRIP_HEIGHT_MM, defaults
│       ├── models.py           # FR1-9 — CardData, DeckProfile, DeckEntry, Language enum (frozen)
│       ├── errors.py           # FR18-21 — DndCardsError hierarchy
│       ├── loader.py           # FR1-4, FR17-19 — PyYAML parse + Pydantic validate
│       ├── scanner.py          # FR2, FR5, FR22-23 — data/ tree scan, card index (paths only)
│       ├── renderer.py         # FR15, FR24-26 — Jinja2 template rendering (autoescape=False)
│       └── composer.py         # FR10-14, FR16 — ReportLab PDF, register_fonts(), try/finally
│
└── tests/
    ├── conftest.py             # shared fixtures: CardData, DeckProfile, tmp paths
    ├── fixtures/
    │   ├── spells/
    │   │   ├── valid_spell.yaml
    │   │   └── malformed_spell.yaml
    │   ├── decks/
    │   │   └── minimal_deck.yaml
    │   └── expected_output/    # baseline PDFs for regression testing
    ├── test_models.py          # Pydantic v2 validators, Language enum, frozen model behavior
    ├── test_errors.py          # DndCardsError hierarchy
    ├── test_loader.py
    ├── test_scanner.py
    ├── test_renderer.py
    ├── test_composer.py        # canvas injected as BytesIO; register_fonts() mocked
    ├── test_cli.py             # typer.testing.CliRunner tests
    └── integration/
        └── test_pipeline.py   # full cli→pdf smoke test (marked slow)
```

### `pyproject.toml` Required Sections

```toml
[project.scripts]
dnd-cards = "dnd_cards.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
markers = ["slow: marks tests as slow (deselect with -m 'not slow')"]
```

### Architectural Boundaries

| Boundary | Contract |
|---|---|
| CLI ↔ domain | `cli.py` is sole catch boundary; domain never prints or exits |
| Scanner ↔ Loader | Scanner returns `dict[str, Path]` only — no YAML parsing |
| YAML ↔ Models | `loader.py`: PyYAML dict → `model_validate()` → frozen Pydantic model |
| Templates ↔ Renderer | Jinja2 env rooted at `templates/`; `autoescape=False` |
| Composer ↔ Canvas | Canvas injected as parameter; `.save()` in `try/finally`; `str(path)` at call site |
| Fonts ↔ ReportLab | `register_fonts()` in `composer.py`, called once at CLI startup; global state isolated |

### Data Flow

```
dnd-cards generate --deck decks/lena-stufe5.yaml [--output-dir output/]
        │
        ▼
   cli.py          parse args → catch DndCardsError → stderr + typer.Exit(code)
        │
        ▼
   scanner.py      scan data/ → dict[id, Path]  (Language enum for locale)
        │
        ▼
   loader.py       deck YAML → DeckProfile → resolve IDs → list[CardData]
        │
        ▼
   renderer.py     Jinja2 template per card → rendered context dicts
        │
        ▼
   composer.py     ReportLab → A4 PDF, 2×4 grid, 126×88mm strips, crop marks
        │
        ▼
   stdout: output/lena-stufe5.pdf
```

### FR → Module Mapping

| FRs | Module |
|---|---|
| FR1–5 (card data management) | `models.py`, `loader.py`, `scanner.py` |
| FR6–9 (deck profiles) | `models.py`, `loader.py` |
| FR10–16 (PDF generation) | `composer.py`, `renderer.py` |
| FR17–21 (validation & errors) | `loader.py`, `scanner.py`, `errors.py`, `cli.py` |
| FR22–23 (card discovery) | `scanner.py`, `cli.py` |
| FR24–26 (template system) | `renderer.py`, `templates/` |
| FR27–30 (CLI & shell integration) | `cli.py` |
| FR31–32 (language & content) | `scanner.py`, `models.py` (`Language` enum), `data/` |

## Architecture Validation

### Coherence Validation

All technology choices compatible. Clean pipeline: PyYAML → Pydantic v2 → Jinja2 → ReportLab. No circular dependencies possible in defined data flow. Typer/Click versions locked via `uv.lock`. `frozen=True` models match read-only YAML use. `autoescape=False` matches PDF (not HTML) output. `pathlib.Path` + `str()` at ReportLab boundary is explicit and testable.

### Requirements Coverage

All 32 FRs mapped to modules (see FR → Module Mapping above). All NFRs addressed:
- `<10s PDF`: ~50–200ms/card × 20 = ~4s max via ReportLab in-process
- `<2s validate`, `<1s list`: direct scan, no parsing overhead
- No silent failures: `DndCardsError` hierarchy + single catch boundary in `cli.py`
- New card type = new template + YAML schema only, zero generator changes
- Deck profile stability: `schemaVersion: 1` from v1
- Cross-platform: pure Python, no native deps, `pathlib.Path` everywhere

### Contract Specifications (resolved before implementation)

**Renderer/Composer interface:**
```python
# renderer.py
def render_card(card: CardData, template_name: str) -> dict[str, Any]: ...

# composer.py
def compose_pdf(cards: list[CardData], output_path: Path) -> None:
    # calls render_card() per card; canvas.save() in try/finally
```

**Output mode:** One combined PDF per deck profile. Filename derived from deck filename (`lena-stufe5.yaml` → `lena-stufe5.pdf`). Default output dir: `output/`.

**Scanner return type:**
```python
def scan_cards(data_dir: Path) -> dict[str, Path]:
    # key = card id (file stem, e.g. "feuerball"), value = Path to .yaml
```

**Error mapping:**

| Exception | Raised by | Exit code | Message format |
|---|---|---|---|
| `YamlParseError` | `loader.py` | 1 | `{file}: YAML syntax error at line {line}: {msg}` |
| `ValidationError` | `loader.py` | 1 | `{file}: field '{field}' {msg}` |
| `CardNotFoundError` | `loader.py` | 1 | `Card not found: {id} (deck: {deck_file}, line {line})` |
| `GenerationError` | `composer.py` | 2 | `PDF generation failed: {msg}` |

**`Language` enum:**
```python
class Language(str, Enum):
    DE = "de"
    EN = "en"
# Values match data/ directory names; str enum enables Path / language.value
```

**Font location:** Bundled in package at `src/dnd_cards/assets/fonts/`. Loaded via `importlib.resources`:
```python
from importlib.resources import files
def register_fonts() -> None:
    fonts_path = files("dnd_cards.assets.fonts")
```
`src/dnd_cards/assets/` is a Python package (requires `__init__.py`).

**Template filename convention:** `{type}-v{n}.jinja2` (e.g. `zauber-v1.jinja2`). Card YAML stores `template: zauber-v1`; renderer appends `.jinja2` on lookup.

**`CardNotFoundError` trigger:** Raised in `loader.py` when a deck profile card ID is not present in the scanner index. Missing `.yaml` file manifests as a missing key — same error, same message.

**`list` subcommand output format:** One card ID per line with type tag:
```
feuerball [spell]
fireball [spell]
```
Sort order: alphabetical by ID. Output to stdout.

### Architecture Completeness Checklist

- [x] Project context and requirements analyzed
- [x] Language & runtime decided (Python + ReportLab)
- [x] Full technology stack specified and locked
- [x] Module structure defined (8 modules, flat layout)
- [x] Error handling contract complete with raise sites and exit codes
- [x] Data architecture defined (file-based, no DB, no cache)
- [x] Implementation patterns defined (naming, structure, tooling)
- [x] Complete project tree with all files
- [x] Architectural boundaries and data flow documented
- [x] All 32 FRs mapped to modules
- [x] All NFRs architecturally addressed
- [x] All module interfaces pinned (signatures, return types)
- [x] Cross-platform concerns addressed (fonts, pathlib, Language enum)

**Overall status: READY FOR IMPLEMENTATION**

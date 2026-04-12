---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: 'complete'
completedAt: '2026-04-11'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# dnd - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for dnd-cards, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: User can define a card by creating a YAML file with type-specific fields
FR2: User can organize card data files in a folder hierarchy by language and card type (`data/{lang}/{type}/{id}.yaml`)
FR3: User can reference a named template within a card YAML file
FR4: User can include edition and source metadata fields in a card YAML file
FR5: User can add a new card to the data store without modifying any other file
FR6: User can define a print selection by creating a deck profile YAML file listing card IDs
FR7: User can specify print quantity per card ID in a deck profile
FR8: User can create multiple named deck profiles for different characters or purposes
FR9: User can update a deck profile by editing its YAML file
FR10: User can generate a print-ready PDF from a deck profile via a CLI command
FR11: System renders each card as a fold-strip (176×63mm landscape) on the output page; fold at 88mm mid-point produces a 63×88mm Magic-card-sized reference card
FR12: System arranges card strips in a 1×4 grid per A4 page (4 cards per page)
FR13: System includes plotter-ready crop marks on each card strip
FR14: System produces PDF output at 100% scale, requiring no printer scaling adjustment
FR15: System applies the template referenced in each card's YAML when rendering that card
FR16: System writes the generated PDF path to stdout on successful generation
FR17: User can validate a deck profile against available card data without generating a PDF
FR18: System reports each missing card ID with the deck file path and the missing ID
FR19: System reports malformed YAML with the affected file path and line number
FR20: System exits with distinct exit codes: 0 (success), 1 (validation error), 2 (generation error)
FR21: System writes all error messages to stderr, never to stdout
FR22: User can list all available cards in the data store
FR23: User can filter the card list by card type
FR24: User can define a card layout by creating a template file
FR25: User can assign different templates to different card types
FR26: User can modify card appearance by editing a template file without changing card data files or generator code
FR27: User can invoke PDF generation via `dnd-cards generate --deck <path>`
FR28: User can invoke validation via `dnd-cards validate --deck <path>`
FR29: User can list available cards via `dnd-cards list [--type <type>]`
FR30: User can use shell tab-completion for subcommands and `--deck` file path arguments
FR31: User can maintain card data in multiple languages within the same data store
FR32: System generates a PDF using only the cards referenced in the deck profile — no "print all" mode

### NonFunctional Requirements

NFR1: PDF generation for a typical deck (10–20 cards) completes in under 10 seconds on a standard desktop machine
NFR2: `validate` completes in under 2 seconds for any deck profile
NFR3: `list` returns results in under 1 second regardless of data store size
NFR4: Generation either succeeds fully or fails with a clear error — no silent partial or corrupted PDF output
NFR5: Card data and deck profile files are plain text YAML — human-readable, diff-friendly, and recoverable without tooling
NFR6: Adding a new card type requires no changes to the generator code — only a new template file and YAML schema
NFR7: The deck profile format must remain stable from v1; schema changes that break existing deck files require explicit versioning
NFR8: The tool runs on Windows, macOS, and Linux without platform-specific configuration
NFR9: Generated PDFs render identically across standard PDF viewers and A4 printers

### Additional Requirements

- AR1: Project initialized with `uv init dnd-cards`; `uv.lock` committed; distributed via `uv tool install .`
- AR2: Module structure: `cli.py`, `config.py`, `models.py`, `errors.py`, `loader.py`, `scanner.py`, `renderer.py`, `composer.py` in `src/dnd_cards/`
- AR3: Frozen Pydantic v2 models (`ConfigDict(frozen=True)`) for `CardData`, `DeckProfile`, `DeckEntry`
- AR4: `Language` enum (`DE="de"`, `EN="en"`) in `models.py`; values match `data/` directory names
- AR5: `scan_cards(data_dir: Path) -> dict[str, Path]` — scanner returns paths only, no YAML parsing
- AR6: `render_card(card: CardData, template_name: str) -> dict[str, Any]` — renderer returns context dict only
- AR7: `compose_pdf(cards: list[CardData], output_path: Path) -> None` — one combined PDF; `canvas.Canvas()` wrapped with `str()`; `.save()` in `try/finally`
- AR8: `DndCardsError` hierarchy: `YamlParseError` (exit 1), `ValidationError` (exit 1), `CardNotFoundError` (exit 1), `GenerationError` (exit 2); `cli.py` is sole catch boundary
- AR9: Font files bundled in `src/dnd_cards/assets/fonts/` via `importlib.resources`; `register_fonts()` called once at CLI startup
- AR10: Jinja2 `Environment(autoescape=False)`; templates rooted at `templates/`; convention `{type}-v{n}.jinja2`
- AR11: `ruff` (TID252, no relative imports) + `mypy --strict` enforced
- AR12: `schemaVersion: 1` field in deck YAML from v1
- AR13: `list` subcommand output: one `{id} [{type}]` per line, alphabetical, to stdout
- AR14: `tests/conftest.py` with shared fixtures; `tests/fixtures/` with valid/malformed YAML samples; `tests/integration/test_pipeline.py` slow-marked

### UX Design Requirements

N/A — CLI tool, no UI design document.

### FR Coverage Map

| FR | Epic | Note |
|---|---|---|
| FR1–5 | Epic 1 | Card YAML schema + file-drop data store |
| FR6–7 | Epics 2+3 | Basic in E2 (IDs+qty); full schema+version in E3 |
| FR8–9 | Epic 3 | Multiple profiles, edit workflow |
| FR10–16 | Epic 2 | Full PDF pipeline — layout, crop marks, stdout path |
| FR17–19 | Epic 3 | validate command, error messages with file+line |
| FR20–21 | Epics 1+3 | Exit code infra in E1; fully exercised in E3 |
| FR22–23 | Epic 1 | list + --type filter |
| FR24–26 | Epic 2 | Template system, per-type templates, edit-to-change |
| FR27 | Epic 2 | generate command (full) |
| FR28 | Epic 3 | validate command (full) |
| FR29 | Epic 1 | list command (full) |
| FR30 | Epics 1+4 | Typer built-in in E1; verified cross-shell in E4 |
| FR31 | Epics 1+4 | Multi-language structure in E1; SRD seed data in E4 |
| FR32 | Epics 2+3 | Deck-only generation enforced from E2 |

## Epic List

### Epic 1: Foundation & Card Data
Users can install `dnd-cards` and run `dnd-cards list` to see available cards. Complete project scaffold, card YAML schema, scanner, and discovery command fully operational.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR20 (infrastructure), FR21 (infrastructure), FR22, FR23, FR29, FR30, FR31
**ARs covered:** AR1–AR14

### Epic 2: Core PDF Generation
Users can generate a print-ready A4 PDF from a deck YAML file with `dnd-cards generate --deck <path>`. Cards render using the zauber-v1 Jinja2 template in fold-strip layout with crop marks. MVP gate reachable here.
**FRs covered:** FR6, FR7 (basic), FR10, FR11, FR12, FR13, FR14, FR15, FR16, FR24, FR25, FR26, FR27, FR32

### Epic 3: Deck Profiles & Validation
Users can validate deck profiles with `dnd-cards validate --deck <path>` and get clear, actionable error messages. Full deck profile features with bulletproof error handling.
**FRs covered:** FR6–9 (full), FR17, FR18, FR19, FR20 (full), FR21 (full), FR28, FR32 (full)

### Epic 4: Seed Data & Polish
English SRD spell data ships as reference content. Shell completion verified. Tool is production-ready for regular session prep.
**FRs covered:** FR30 (refined), FR31 (seed data), NFR cross-platform and PDF render verification

---

## Epic 1: Foundation & Card Data

Users can install `dnd-cards` and run `dnd-cards list` to see available cards. Complete project scaffold, card YAML schema, scanner, and discovery command fully operational.

### Story 1.1: Project Scaffold & CLI Entry Point

As a developer,
I want the `dnd-cards` project initialized with all source modules, dependency config, and a working CLI entry point,
So that all subsequent stories have a stable foundation to build on.

**Acceptance Criteria:**

**Given** a machine with uv installed
**When** `uv tool install .` is run from the project root
**Then** `dnd-cards --help` outputs exactly three subcommands: `generate`, `validate`, and `list` with their descriptions
**And** `dnd-cards --version` returns a version string

**Given** the `pyproject.toml` contains:
```toml
[project.scripts]
dnd-cards = "dnd_cards.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```
**When** `uv tool install .` is run
**Then** the `dnd-cards` binary is available in PATH

**Given** all 8 source modules exist as stubs: `cli.py`, `config.py`, `models.py`, `errors.py`, `loader.py`, `scanner.py`, `renderer.py`, `composer.py`
**When** `mypy --strict src/` is run
**Then** it exits with code 0 and zero errors
**And** `ruff check src/` exits with code 0
**And** `pytest` collects at least the stub test files without errors

### Story 1.2: Error Hierarchy & Exit Code Infrastructure

As a developer,
I want the complete `DndCardsError` exception hierarchy and CLI error handling in place,
So that all subsequent stories can raise typed errors and have them correctly routed to stderr with the right exit code.

**Acceptance Criteria:**

**Given** the `errors.py` module
**When** imported
**Then** `YamlParseError`, `ValidationError`, `CardNotFoundError`, and `GenerationError` are all subclasses of `DndCardsError`

**Given** this exit code table is implemented in `cli.py`:
| Exception | Exit code |
|---|---|
| `YamlParseError` | 1 |
| `ValidationError` | 1 |
| `CardNotFoundError` | 1 |
| `GenerationError` | 2 |
| Any other exception | 2 |

**When** any of these exceptions is raised from a domain module
**Then** the exception message is written to **stderr** (not stdout)
**And** the process exits with the corresponding code above

**Given** an unexpected exception (not a `DndCardsError` subclass) propagates to the CLI
**When** it reaches the catch boundary in `cli.py`
**Then** the full traceback is written to **stderr**
**And** the process exits with code 2

**Given** a successful command completes
**When** it exits
**Then** the process exits with code 0

### Story 1.3: Card Data Models & YAML Schema

As Tobias,
I want a well-defined YAML schema for spell cards with Pydantic validation,
So that I know exactly how to structure my card data files and get clear errors if I make a mistake.

**Acceptance Criteria:**

**Given** a valid spell card YAML file with this exact schema:
```yaml
id: feuerball
type: spell
template: zauber-v1
name: Feuerball
lang: de
level: 3
school: Verwandlung
casting_time: 1 Aktion
range: 45 m
components: V, S, M
duration: Sofort
description: |
  Ein heller Streifen...
edition: "5.5e"           # optional
source_book: Spielerhandbuch  # optional
```
**When** `loader.load_card(path)` is called
**Then** it returns a frozen `CardData` instance with all fields populated
**And** `card.lang` is `Language.DE`
**And** the model raises `TypeError` if any field is mutated after creation

**Given** a YAML file missing a required field (e.g., `level`)
**When** `loader.load_card(path)` is called
**Then** a `ValidationError` is raised with a message that includes the file path and the missing field name

**Given** a YAML file with invalid YAML syntax
**When** `loader.load_card(path)` is called
**Then** a `YamlParseError` is raised
**And** the message includes the file path and line number (from PyYAML's `MarkedYAMLError.problem_mark`)

**Given** `tests/fixtures/spells/valid_spell.yaml` matches the schema above
**When** loaded by `test_loader.py`
**Then** all field assertions pass

**`CardData` field specification:**

| Field | Type | Required |
|---|---|---|
| `id` | `str` | yes |
| `type` | `str` | yes |
| `template` | `str` | yes |
| `name` | `str` | yes |
| `lang` | `Language` | yes |
| `level` | `int` | yes |
| `school` | `str` | yes |
| `casting_time` | `str` | yes |
| `range` | `str` | yes |
| `components` | `str` | yes |
| `duration` | `str` | yes |
| `description` | `str` | yes |
| `edition` | `str \| None` | no |
| `source_book` | `str \| None` | no |

**`Language` enum values:** `DE = "de"`, `EN = "en"` (str enum, values match `data/` directory names)

### Story 1.4: Card Scanner & Data Store Discovery

As Tobias,
I want the tool to automatically discover all card YAML files in the `data/` folder tree,
So that I never have to register or index cards manually — dropping a file is enough.

**Acceptance Criteria:**

**Given** card files at `data/en/spells/fireball.yaml` and `data/de/spells/feuerball.yaml`
**When** `scanner.scan_cards(data_dir)` is called
**Then** it returns a `dict[str, CardRef]` where:
- keys are type-prefixed: `"spells/fireball"`, `"spells/feuerball"` (format: `"{card_type}/{stem}"`)
- each `CardRef` is a namedtuple `CardRef(path: Path, card_type: str)`
- `card_type` is the directory name one level above the file (e.g., `"spells"`)
- no YAML files are read — type is derived from directory path only
- return dict makes no ordering guarantee; callers must sort if order matters

**Given** `.yaml` is the only accepted extension (`.yml` files are ignored)
**When** a `.yml` file exists in `data/`
**Then** it is not included in the result

**Given** the `data/` directory is empty
**When** `scanner.scan_cards(data_dir)` is called
**Then** it returns an empty dict with no error

**Given** `data/de/conditions/vergiftet.yaml` and `data/de/spells/vergiftet.yaml` both exist
**When** `scanner.scan_cards(data_dir)` is called
**Then** both are included: `"conditions/vergiftet"` and `"spells/vergiftet"` — no collision

### Story 1.5: `list` Subcommand

As Tobias,
I want to run `dnd-cards list` to see all available cards,
So that I know what content is in my data store before building a deck.

**Acceptance Criteria:**

**Given** card files exist in `data/` including spells and conditions
**When** `dnd-cards list` is run
**Then** each card is printed to stdout as `{stem} [{card_type}]`, one per line, sorted alphabetically by stem
**And** nothing is printed to stderr
**And** the process exits with code 0

**Given** cards of types `spells` and `conditions` exist
**When** `dnd-cards list --type spells` is run
**Then** only cards with `card_type="spells"` are printed
**And** the `--type` value is case-sensitive and matched against the directory name (e.g., `spells`, not `Spells`)

**Given** `--type` is given an unrecognised value (e.g., `--type feats`)
**When** the command runs
**Then** no output is produced and the process exits with code 0

**Given** the `data/` folder is empty
**When** `dnd-cards list` is run
**Then** no output is produced and the process exits with code 0

**Given** cards exist but none match the `--type` filter
**When** `dnd-cards list --type conditions` is run against a spells-only data store
**Then** no output is produced and the process exits with code 0

---

## Epic 2: Core PDF Generation

Users can generate a print-ready A4 PDF from a deck YAML file with `dnd-cards generate --deck <path>`. Cards render using the zauber-v1 Jinja2 template in fold-strip layout with crop marks. MVP gate reachable here.

### Story 2.1: Deck Profile Model & Basic Loader

As Tobias,
I want a YAML deck profile format that lists card IDs with quantities,
So that I can specify exactly which cards to print and how many copies of each.

**Acceptance Criteria:**

**Given** a deck profile YAML:
```yaml
name: Lena Stufe 5
cards:
  spells/feuerball: 1
  spells/magisches-geschoss: 2
```
**When** `loader.load_deck(path)` is called
**Then** it returns a frozen `DeckProfile` with `name="Lena Stufe 5"` and `entries` containing 2 `DeckEntry` items
**And** entries preserve `card_key` as a string (no resolution at load time)
**And** `DeckEntry(card_key="spells/magisches-geschoss", quantity=2)` is present

**Given** a malformed deck YAML (syntax error)
**When** `loader.load_deck(path)` is called
**Then** a `YamlParseError` (from `errors.py`) is raised with file path and line number — no new exception class defined

**`DeckProfile` and `DeckEntry` field specification:**

| Model | Field | Type | Required |
|---|---|---|---|
| `DeckProfile` | `name` | `str` | yes |
| `DeckProfile` | `entries` | `list[DeckEntry]` | yes |
| `DeckEntry` | `card_key` | `str` (`"{card_type}/{id}"` format) | yes |
| `DeckEntry` | `quantity` | `int` (≥1) | yes |

Both models use `ConfigDict(frozen=True)`.

### Story 2.2: Jinja2 Template System & Spell Card Renderer

As Tobias,
I want a `zauber-v1.jinja2` template that defines the visual layout of a spell card,
So that card appearance is controlled by a file I can edit without touching any Python code.

**Acceptance Criteria:**

**Given** `templates/zauber-v1.jinja2` exists with placeholders for all `CardData` fields (name, level, school, casting_time, range, components, duration, description)
**When** `renderer.render_card(card: CardData, template_name: str) -> dict[str, Any]` is called
**Then** it returns a context dict containing all card field values as strings
**And** the dict is passed to `compose_pdf()` — no canvas or PDF objects are created in this function

**Given** the Jinja2 `Environment` is configured with `autoescape=False` and loader rooted at `templates/`
**When** a card with German text (umlauts, ß) is rendered
**Then** the context dict preserves those characters without HTML escaping

**Given** a template name that does not exist as `templates/{name}.jinja2`
**When** `renderer.render_card()` is called
**Then** a `GenerationError` is raised with the missing template name

**Note:** `render_card()` is called inside `compose_pdf()` per card — not directly by the CLI.

### Story 2.3: PDF Composer — Layout Engine

As Tobias,
I want each card rendered as a 176×63mm landscape fold-strip on an A4 page in a 1×4 grid with crop marks,
So that I can print, fold, and laminate the output into Magic card-sized reference cards.

**Acceptance Criteria:**

**Given** a list of `CardData` objects passed to `composer.compose_pdf(cards: list[CardData], output_path: Path) -> None`
**When** the function runs
**Then** for each card: `renderer.render_card(card, card.template)` is called to get the context dict
**And** the context is used to draw text onto a 176×63mm landscape strip on the canvas

**Given** up to 4 cards
**When** `compose_pdf()` is called
**Then** a single A4 portrait page (210×297mm) is produced with cards in a 1-column × 4-row grid

**Given** 5 or more cards
**When** `compose_pdf()` is called
**Then** the PDF contains multiple A4 pages (4 cards per page; last page may be partial)

**Given** each card strip on the page
**When** the PDF is rendered
**Then** crop marks appear at all 4 corners of each strip: 0.5pt black lines, 5mm long, offset 2mm from the strip corner
**And** a fold-guide line appears at the vertical centre of the strip (at 88mm) to mark the fold axis

**Given** `compose_pdf()` is called
**When** it executes
**Then** `register_fonts()` is called once before any canvas operations
**And** `canvas.Canvas(str(output_path))` is used (str() wrapper required)
**And** `.save()` is called inside a `try/finally` block

**Given** a `BytesIO` object is passed as `output_path` in tests
**When** `compose_pdf()` runs
**Then** it completes without error — no disk I/O required for unit tests

### Story 2.4: `generate` Subcommand — End to End

As Tobias,
I want to run `dnd-cards generate --deck decks/my-deck.yaml` and get a print-ready PDF,
So that I can go from a deck file to a physical card in one command.

**Acceptance Criteria:**

**Given** a valid deck profile referencing card keys present in `data/`
**When** `dnd-cards generate --deck decks/lena-stufe5.yaml` is run
**Then** the generate command orchestrates: `scan_cards()` → `load_deck()` → resolve keys → `load_card()` per key → expand quantities → `compose_pdf()`
**And** quantity expansion: a `DeckEntry(quantity=2)` produces `[card, card]` before passing to `compose_pdf()`
**And** the PDF is written to `output/lena-stufe5.pdf` (filename = deck file stem + `.pdf`)
**And** the output directory `output/` is created by the CLI if it does not exist
**And** the resolved PDF path is printed to stdout
**And** the process exits with code 0

**Given** `--output-dir /tmp/cards` is specified
**When** the command runs successfully
**Then** the PDF is written to `/tmp/cards/lena-stufe5.pdf`
**And** `/tmp/cards/` is created if it does not exist

**Given** a deck entry references a `card_key` not present in the scanner index
**When** the generate command resolves keys (after `scan_cards()`, before `load_card()`)
**Then** a `CardNotFoundError` is raised with message: `Card not found: {key} (deck: {deck_file})`
**And** the message is written to stderr
**And** the process exits with code 1
**And** no partial PDF is written to disk

**Given** `quantity: 2` for a card entry
**When** the PDF is generated
**Then** that card appears as two separate strips in the output PDF

---

## Epic 3: Deck Profiles & Validation

Users can validate deck profiles with `dnd-cards validate --deck <path>` and get clear, actionable error messages. Full deck profile schema with `schemaVersion`. Bulletproof error reporting.

### Story 3.1: `schemaVersion` & Full Deck Profile Schema

As Tobias,
I want the deck profile format to include a `schemaVersion` field,
So that future format changes can be detected and migrated without silent breakage.

**Acceptance Criteria:**

**Given** a deck profile YAML with `schemaVersion: 1`:
```yaml
schemaVersion: 1
name: Lena Stufe 5
cards:
  spells/feuerball: 1
  spells/magisches-geschoss: 2
```
**When** `loader.load_deck(path)` is called
**Then** it returns a valid `DeckProfile` with `schema_version=1`

**Given** a deck profile YAML missing the `schemaVersion` field
**When** `loader.load_deck(path)` is called
**Then** a `ValidationError` is raised with message: `{file}: field 'schema_version' is required`

**Given** a deck profile YAML with `schemaVersion: 2`
**When** `loader.load_deck(path)` is called
**Then** a `ValidationError` is raised with message: `{file}: field 'schema_version' unsupported value 2 (expected 1)`

**Updated `DeckProfile` field specification:**

| Field | Type | Required |
|---|---|---|
| `schema_version` | `int` (must be 1) | yes |
| `name` | `str` | yes |
| `entries` | `list[DeckEntry]` | yes |

**Note:** `tests/fixtures/decks/minimal_deck.yaml` must be updated to include `schemaVersion: 1`. All existing deck fixture files must include this field or `loader.load_deck()` will raise `ValidationError` in previously passing tests.

### Story 3.2: `validate` Subcommand — Comprehensive Error Reporting

As Tobias,
I want to run `dnd-cards validate --deck <path>` to check a deck profile before printing,
So that I can catch all errors — missing cards, malformed YAML, wrong fields — without wasting time on a failed PDF generation.

**Acceptance Criteria:**

**Given** a valid deck profile with all card keys present in `data/`
**When** `dnd-cards validate --deck decks/lena-stufe5.yaml` is run
**Then** nothing is printed to stdout or stderr
**And** the process exits with code 0

**Given** a deck profile where multiple card keys are missing from the scanner index
**When** `dnd-cards validate` is run
**Then** ALL missing card errors are reported to stderr (not just the first)
**And** each error follows the exact format: `Card not found: {key} (deck: {deck_file})`
**And** the process exits with code 1

**Given** a deck profile YAML with a syntax error
**When** `dnd-cards validate` is run
**Then** the error is written to stderr: `{file}: YAML syntax error at line {line}: {msg}`
**And** validation halts immediately (no card resolution attempted)
**And** the process exits with code 1

**Given** a deck profile with a missing required field (e.g., `name`)
**When** `dnd-cards validate` is run
**Then** the error is written to stderr: `{file}: field '{field}' {msg}`
**And** validation halts immediately
**And** the process exits with code 1

**Given** a deck profile with `schemaVersion: 2`
**When** `dnd-cards validate` is run
**Then** the schema version ValidationError is written to stderr
**And** the process exits with code 1

**Given** a deck profile path that does not exist
**When** `dnd-cards validate --deck nonexistent.yaml` is run
**Then** an error is written to stderr: `Deck file not found: nonexistent.yaml`
**And** the process exits with code 1

**Given** `dnd-cards validate` completes (pass or fail)
**When** it exits
**Then** no PDF is generated and no `output/` directory is created

**Two-phase validation behaviour:**
- **Phase 1 — Parse:** `load_deck(path)` is called. If a `YamlParseError` or `ValidationError` occurs, it is reported immediately and validation halts.
- **Phase 2 — Resolution:** All `DeckEntry` keys are resolved against the scanner index in a single pass. ALL `CardNotFoundError`s are collected and reported together before exiting with code 1.

**Implementation note:** `validate` reuses `scan_cards()` + `load_deck()` + key resolution from Epic 2, stopping before `compose_pdf()`. No new domain logic — only CLI wiring.

---

## Epic 4: Seed Data & Polish

English SRD spell data ships as reference content. Shell completion verified. Tool is production-ready for regular session prep.

### Story 4.1: English SRD Spell Seed Data

As Tobias,
I want a set of English SRD spell cards included in the repository,
So that the tool ships with working reference content and I have test data I can legally distribute.

**Acceptance Criteria:**

**Given** the repository contains at least 5 English SRD spells at `data/en/spells/*.yaml`
**When** `dnd-cards list --type spells` is run
**Then** the SRD spells appear in the output (e.g., `fireball [spells]`, `magic-missile [spells]`)

**Given** each SRD spell YAML file
**When** `loader.load_card(path)` is called on it
**Then** it loads without error — all required fields present, `lang: en`, schema-valid

**Given** a deck profile referencing an SRD spell key (e.g., `spells/fireball`)
**When** `dnd-cards generate --deck decks/example-deck.yaml` is run
**Then** the PDF generates successfully with the SRD spell rendered
**And** the output PDF file exists on disk and is non-zero bytes

**Minimum SRD spells to include:** `fireball`, `magic-missile`, `cure-wounds`, `shield`, `detect-magic` (5 spells covering levels 0–3, multiple schools)

**Note:** All SRD content uses `source_book: "SRD 5.1"` and `edition: "5e"` fields.

### Story 4.2: Shell Completion Verification & `example-deck.yaml`

As Tobias,
I want shell tab-completion working for all subcommands and `--deck` file paths,
So that the CLI feels polished and session prep is fast.

**Acceptance Criteria:**

**Given** `dnd-cards` is installed via `uv tool install .`
**When** Typer's built-in completion setup is used (`dnd-cards --install-completion`)
**Then** tab-completion is available for subcommands (`generate`, `validate`, `list`) in bash, zsh, and fish

**Given** `decks/example-deck.yaml` exists referencing SRD spell keys from Story 4.1:
```yaml
schemaVersion: 1
name: Example Deck
cards:
  spells/fireball: 1
  spells/magic-missile: 2
```
**When** `dnd-cards validate --deck decks/example-deck.yaml` is run
**Then** it exits with code 0

**When** `dnd-cards generate --deck decks/example-deck.yaml` is run
**Then** a PDF is generated successfully, the path is printed to stdout, and the PDF file exists on disk

**Given** the tool is run on Windows (PowerShell/cmd), macOS, and Linux
**When** `dnd-cards --help` is invoked on each platform
**Then** it exits with code 0 and displays the help text correctly

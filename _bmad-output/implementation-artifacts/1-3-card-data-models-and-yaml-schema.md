---
story_id: "1.3"
story_key: "1-3-card-data-models-and-yaml-schema"
epic: "Epic 1: Foundation & Card Data"
status: "done"
created: "2026-04-11"
---

# Story 1.3: Card Data Models & YAML Schema

## Story

As Tobias,
I want a well-defined YAML schema for spell cards with Pydantic validation,
so that I know exactly how to structure my card data files and get clear errors if I make a mistake.

---

## Acceptance Criteria

**AC1 — `load_card` returns a valid frozen `CardData`:**
- **Given** a valid spell card YAML file (e.g. `tests/fixtures/spells/valid_spell.yaml`)
- **When** `loader.load_card(path)` is called
- **Then** it returns a frozen `CardData` instance with all fields populated
- **And** `card.lang` is `Language.EN` (for the `lang: en` fixture)
- **And** the model raises an exception if any field is mutated after creation (see dev note on frozen behavior)

**AC2 — Missing required field raises `ValidationError`:**
- **Given** a YAML file missing a required field (e.g., `level`)
- **When** `loader.load_card(path)` is called
- **Then** `dnd_cards.errors.ValidationError` is raised
- **And** the message includes both the file path and the missing field name

**AC3 — Malformed YAML raises `YamlParseError`:**
- **Given** a YAML file with invalid YAML syntax
- **When** `loader.load_card(path)` is called
- **Then** `dnd_cards.errors.YamlParseError` is raised
- **And** the message includes the file path and line number (from PyYAML's `problem_mark`)

**AC4 — Fixture round-trip:**
- **Given** `tests/fixtures/spells/valid_spell.yaml` is already on disk
- **When** loaded by `test_loader.py`
- **Then** all field assertions pass (id, type, template, name, lang, level, school, etc.)

---

## Tasks / Subtasks

- [x] Task 1: Install `types-PyYAML` dev dependency (AC: all — required for mypy)
  - [x] Run `uv add --dev types-PyYAML`
- [x] Task 2: Implement `loader.load_card()` in `src/dnd_cards/loader.py` (AC: 1, 2, 3)
  - [x] Add `import yaml` and `import pydantic` imports
  - [x] Implement YAML parsing with `yaml.safe_load()`, catch `yaml.MarkedYAMLError`
  - [x] Implement Pydantic validation with `CardData.model_validate()`, catch `pydantic.ValidationError`
  - [x] Map PyYAML exceptions → `YamlParseError` (with path + line number)
  - [x] Map Pydantic exceptions → `dnd_cards.errors.ValidationError` (with path + field name)
- [x] Task 3: Update `tests/conftest.py` with shared fixtures (AC: 4)
  - [x] Add `valid_card_data` fixture returning a `CardData` instance
  - [x] Add `fixture_path` fixture returning the `tests/fixtures/` path
- [x] Task 4: Implement `tests/test_loader.py` (AC: 1, 2, 3, 4)
  - [x] Test `load_card` with `valid_spell.yaml` — assert field values
  - [x] Test `load_card` with missing required field — assert `ValidationError` + message content
  - [x] Test `load_card` with malformed YAML — assert `YamlParseError` + message content
  - [x] Test frozen model mutation raises exception
- [x] Task 5: Optionally add `tests/test_models.py` with `Language` enum and frozen model tests (AC: 1)
- [x] Task 6: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- `src/dnd_cards/models.py` — **COMPLETE**. `CardData`, `DeckProfile`, `DeckEntry`, `Language` all defined with `ConfigDict(frozen=True)`. Do NOT modify.
- `src/dnd_cards/errors.py` — **COMPLETE**. `YamlParseError`, `ValidationError` are ready to raise. Do NOT modify.
- `tests/fixtures/spells/valid_spell.yaml` — exists with `lang: en`, all required fields present.
- `tests/fixtures/spells/malformed_spell.yaml` — exists with broken YAML indentation. Verify it causes `yaml.MarkedYAMLError` (see note below).
- `loader.load_deck()` — stays as stub `raise NotImplementedError`. Story 2.1 implements it.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/loader.py` | Implement `load_card()` |
| `tests/conftest.py` | Add shared fixtures |
| `tests/test_loader.py` | Replace stub with real tests |
| `tests/test_models.py` | Optional: add `Language` enum + frozen model tests |

### Step 1: Install types-PyYAML First

`yaml` has no inline type stubs. Without `types-PyYAML`, `mypy --strict` reports an error on `import yaml`. Run this before implementing:

```bash
uv add --dev types-PyYAML
```

### Exact `loader.py` Implementation

**Critical name collision:** `pydantic.ValidationError` and `dnd_cards.errors.ValidationError` are different classes. Use `import pydantic` (not `from pydantic import ValidationError`) so they stay distinct.

```python
"""PyYAML parsing + Pydantic validation for card and deck YAML files."""

from pathlib import Path

import pydantic
import yaml

from dnd_cards.errors import ValidationError, YamlParseError
from dnd_cards.models import CardData, DeckProfile

__all__ = ["load_card", "load_deck"]


def load_card(path: Path) -> CardData:
    """Parse and validate a card YAML file."""
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.MarkedYAMLError as exc:
        mark = exc.problem_mark
        line_num: int = (mark.line + 1) if mark is not None else 0
        raise YamlParseError(
            f"{path}: YAML syntax error at line {line_num}: {exc.problem}"
        ) from exc
    except yaml.YAMLError as exc:
        raise YamlParseError(f"{path}: YAML error: {exc}") from exc

    try:
        return CardData.model_validate(raw)
    except pydantic.ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        msg = first_error["msg"]
        raise ValidationError(f"{path}: field '{field}' {msg}") from exc


def load_deck(path: Path) -> DeckProfile:
    """Parse and validate a deck profile YAML file. Implementation in Story 2.1."""
    raise NotImplementedError
```

**Notes:**
- `yaml.safe_load()` — always use safe_load, never `yaml.load()`
- `exc.problem_mark.line` is 0-indexed; add 1 for human-readable line numbers
- `mark` can be `None` in rare edge cases — the `if mark is not None` guard is required for mypy --strict
- `yaml.safe_load()` returns `Any` — pass directly to `model_validate()`, no cast needed
- `DeckProfile` import stays (used as return type of `load_deck`)

### Frozen Model Mutation — Pydantic v2 Behavior

**The AC says "raises `TypeError` if any field is mutated"** — this is INCORRECT for Pydantic v2. With `ConfigDict(frozen=True)`:

- Pydantic v2 raises **`pydantic.ValidationError`** (not `TypeError`) when you try to set an attribute
- This is different from Python dataclasses (`FrozenInstanceError`) or v1 (`TypeError`)

Test for `pydantic.ValidationError`, not `TypeError`:

```python
import pydantic
import pytest

def test_card_data_is_frozen(valid_card_data: CardData) -> None:
    with pytest.raises(pydantic.ValidationError):
        valid_card_data.name = "mutated"  # type: ignore[misc]
```

The `# type: ignore[misc]` suppresses mypy's "Cannot assign to a method" error on frozen models.

### Malformed YAML Fixture Verification

`tests/fixtures/spells/malformed_spell.yaml` currently contains:
```yaml
id: bad-spell
  this: is: broken yaml
```

Verify this raises `yaml.MarkedYAMLError`. If it does not (PyYAML may parse it differently), replace the file content with a reliably broken YAML:

```yaml
id: [unclosed bracket
```

This always triggers `yaml.scanner.ScannerError` (a `MarkedYAMLError` subclass) with a valid `problem_mark`.

### Test for Missing Required Field — How to Trigger

Write a temp YAML file missing `level`:

```python
import pytest
from pathlib import Path
from dnd_cards.loader import load_card
from dnd_cards.errors import ValidationError

def test_load_card_missing_field(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        "id: test\ntype: spell\ntemplate: t\nname: Test\nlang: en\n"
        "school: Evoc\ncasting_time: 1a\nrange: 30ft\ncomponents: V\n"
        "duration: 1r\ndescription: desc\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError) as exc_info:
        load_card(bad_yaml)
    assert "level" in str(exc_info.value)
    assert str(bad_yaml) in str(exc_info.value)
```

Use pytest's built-in `tmp_path` fixture — no need to create a permanent fixture file.

### conftest.py Fixtures to Add

```python
"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from dnd_cards.models import CardData, Language


@pytest.fixture
def fixture_path() -> Path:
    """Path to tests/fixtures/ directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_card_data() -> CardData:
    """A valid CardData instance for testing."""
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
        description="A bright streak flashes from your pointing finger...",
        edition="5e",
        source_book="SRD 5.1",
    )
```

### test_loader.py Structure

```python
"""Tests for loader module."""

from pathlib import Path

import pytest

from dnd_cards.errors import ValidationError, YamlParseError
from dnd_cards.loader import load_card
from dnd_cards.models import Language


def test_load_card_valid(fixture_path: Path) -> None:
    card = load_card(fixture_path / "spells" / "valid_spell.yaml")
    assert card.id == "fireball"
    assert card.lang == Language.EN
    assert card.level == 3
    assert card.edition == "5e"
    assert card.source_book == "SRD 5.1"


def test_load_card_missing_field(tmp_path: Path) -> None:
    # YAML with all fields except 'level'
    bad = tmp_path / "no_level.yaml"
    bad.write_text(
        "id: x\ntype: spell\ntemplate: t\nname: X\nlang: en\n"
        "school: S\ncasting_time: 1a\nrange: 10ft\ncomponents: V\n"
        "duration: 1r\ndescription: d\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError) as exc_info:
        load_card(bad)
    assert "level" in str(exc_info.value)
    assert str(bad) in str(exc_info.value)


def test_load_card_malformed_yaml(fixture_path: Path) -> None:
    with pytest.raises(YamlParseError) as exc_info:
        load_card(fixture_path / "spells" / "malformed_spell.yaml")
    err = str(exc_info.value)
    assert "malformed_spell.yaml" in err


def test_load_card_yaml_error_includes_line_number(tmp_path: Path) -> None:
    bad = tmp_path / "bad_syntax.yaml"
    bad.write_text("id: [unclosed bracket\n", encoding="utf-8")
    with pytest.raises(YamlParseError) as exc_info:
        load_card(bad)
    assert "line" in str(exc_info.value)
```

### test_models.py Additions (Task 5)

```python
"""Tests for models module."""

import pydantic
import pytest

from dnd_cards.models import CardData, Language


def test_language_enum_values() -> None:
    assert Language.DE.value == "de"
    assert Language.EN.value == "en"
    assert Language("de") == Language.DE
    assert Language("en") == Language.EN


def test_card_data_frozen(valid_card_data: CardData) -> None:
    with pytest.raises(pydantic.ValidationError):
        valid_card_data.name = "mutated"  # type: ignore[misc]
```

### Architecture Constraints

- **`yaml.safe_load()` only** — never `yaml.load()` (security requirement)
- **Absolute imports** — `from dnd_cards.errors import ...` (ruff TID252)
- **`load_deck()` stays as stub** — `raise NotImplementedError`, Story 2.1 implements it
- **No changes to `errors.py` or `models.py`** — both are complete
- **`DeckProfile` import stays in `loader.py`** — it's the return type of `load_deck`

### Regression Safeguard

All 10 existing tests must remain green after this story:
- `tests/test_cli.py` — 8 tests (2 from 1.1, 6 from 1.2)
- `tests/test_errors.py` — 1 test
- `tests/integration/test_pipeline.py` — 1 test

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Installed:** Python 3.11.9, pydantic 2.12.5, pyyaml 6.0.3, mypy 1.20.0

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: `load_card()` returns frozen `CardData`; all fixture fields assert correctly
- ✅ AC2: Missing field raises `dnd_cards.errors.ValidationError` with path + field name in message
- ✅ AC3: Malformed YAML raises `YamlParseError` with path + "line" in message (confirmed `malformed_spell.yaml` triggers `MarkedYAMLError` at line 2)
- ✅ AC4: `valid_spell.yaml` round-trip: 13 field assertions pass
- ✅ Confirmed: Pydantic v2 `frozen=True` raises `pydantic.ValidationError` on mutation (not TypeError — AC was incorrect)
- ✅ Added bonus test: invalid `lang: fr` value raises `ValidationError` with "lang" in message
- ✅ `types-PyYAML==6.0.12.20260408` installed — mypy --strict now handles `import yaml`
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 18/18 passed (8 new + 10 regressions all green)

### File List

- `src/dnd_cards/loader.py`
- `tests/conftest.py`
- `tests/test_loader.py`
- `tests/test_models.py`

### Change Log

- 2026-04-11: Implemented `load_card()` with PyYAML + Pydantic v2 validation; added conftest fixtures; 8 new tests. All ACs satisfied.

### Review Findings

- [x] [Review][Patch] `load_card` did not guard against `None`/non-dict from `yaml.safe_load` — added `isinstance(raw, dict)` check raising `YamlParseError` [src/dnd_cards/loader.py] — fixed
- [x] [Review][Patch] `test_load_card_valid` missing `description` field assertion — added [tests/test_loader.py] — fixed
- [x] [Review][Patch] Added `test_load_card_empty_yaml` and `test_load_card_non_mapping_yaml` tests [tests/test_loader.py] — fixed
- [x] [Review][Defer] `CardData` structurally spell-specific; no polymorphism for other card types — deferred, pre-existing, future epic scope
- [x] [Review][Defer] `type`/`template` bare str with no controlled vocabulary — deferred, pre-existing, future story scope
- [x] [Review][Defer] `FileNotFoundError`/`OSError` uncaught on missing path — deferred, pre-existing, scanner provides verified paths

---
story_id: "2.1"
story_key: "2-1-deck-profile-model-and-basic-loader"
epic: "Epic 2: Core PDF Generation"
status: "review"
created: "2026-04-12"
---

# Story 2.1: Deck Profile Model & Basic Loader

## Story

As Tobias,
I want a YAML deck profile format that lists card IDs with quantities,
so that I can specify exactly which cards to print and how many copies of each.

---

## Acceptance Criteria

**AC1 — Valid deck profile loads into DeckProfile:**
- **Given** a deck profile YAML:
  ```yaml
  name: Lena Stufe 5
  cards:
    spells/feuerball: 1
    spells/magisches-geschoss: 2
  ```
- **When** `loader.load_deck(path)` is called
- **Then** it returns a frozen `DeckProfile` with `name="Lena Stufe 5"` and `entries` containing 2 `DeckEntry` items
- **And** `DeckEntry(card_key="spells/feuerball", quantity=1)` is present
- **And** `DeckEntry(card_key="spells/magisches-geschoss", quantity=2)` is present
- **And** entries preserve `card_key` as a string (no path resolution at load time)

**AC2 — Malformed YAML raises YamlParseError:**
- **Given** a deck profile YAML with a syntax error
- **When** `loader.load_deck(path)` is called
- **Then** a `YamlParseError` is raised (from `errors.py`) with the file path and line number in the message
- **And** no new exception class is defined

---

## Tasks / Subtasks

- [x] Task 1: Implement `load_deck()` in `loader.py` (AC: 1, 2)
  - [x] Add `DeckProfile`, `DeckEntry` to imports in `loader.py`
  - [x] Reshape YAML `cards` dict → `entries` list before `model_validate()` (see Dev Notes)
  - [x] Mirror `load_card()` error handling: `MarkedYAMLError` → `YamlParseError`, `pydantic.ValidationError` → `ValidationError`
  - [x] Handle empty/non-mapping YAML with `YamlParseError`
- [x] Task 2: Add `load_deck` tests to `tests/test_loader.py` (AC: 1, 2)
  - [x] Test valid deck using `tests/fixtures/decks/minimal_deck.yaml`
  - [x] Test multiple entries with different quantities
  - [x] Test card_key preserved as-is (no resolution)
  - [x] Test malformed YAML raises `YamlParseError` with path and line number
  - [x] Test missing `name` field raises `ValidationError` with path and field name
- [x] Task 3: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions, 33 existing tests green)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- **`src/dnd_cards/models.py`** — `DeckProfile` and `DeckEntry` stubs are already complete and correct:
  ```python
  class DeckEntry(BaseModel):
      model_config = ConfigDict(frozen=True)
      card_key: str   # format: "{card_type}/{id}", e.g. "spells/feuerball"
      quantity: int   # ≥1  (ge=1 constraint deferred to Story 3.x per deferred-work.md)

  class DeckProfile(BaseModel):
      model_config = ConfigDict(frozen=True)
      name: str
      entries: list[DeckEntry]
  ```
  **Do NOT modify `models.py`**. The `ge=1` constraint is explicitly deferred to Story 3.x (see `_bmad-output/implementation-artifacts/deferred-work.md`).

- **`tests/fixtures/decks/minimal_deck.yaml`** — already exists:
  ```yaml
  name: Test Deck
  cards:
    spells/fireball: 1
  ```
  Use this fixture directly in `test_load_deck_valid`.

- **`loader.py`** — `load_deck(path: Path) -> DeckProfile` stub exists, raises `NotImplementedError`. Also has `load_card()` already fully implemented — mirror its pattern exactly.

- **All 33 existing tests pass** — none of them test `load_deck()` yet.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/loader.py` | Replace `load_deck` stub with full implementation |
| `tests/test_loader.py` | Add 5 new `load_deck` tests |

### Critical Implementation Detail: YAML Structure Mismatch

The deck YAML uses a `cards:` dict but `DeckProfile.entries` is a `list[DeckEntry]`. You **cannot** call `DeckProfile.model_validate(raw)` directly — the keys don't align.

**YAML raw parsed dict:**
```python
{'name': 'Lena Stufe 5', 'cards': {'spells/feuerball': 1, 'spells/magisches-geschoss': 2}}
```

**Required reshape before `model_validate()`:**
```python
shaped = {
    "name": raw.get("name"),
    "entries": [
        {"card_key": k, "quantity": v}
        for k, v in (raw.get("cards") or {}).items()
    ],
}
DeckProfile.model_validate(shaped)
```

This is called out explicitly in `deferred-work.md`: *"`DeckProfile.entries` field name doesn't match fixture `cards:` key — YAML alias or field rename needed before `load_deck` is implemented in Story 2.1"*. Use the manual reshape approach (not Pydantic aliases).

### Exact `load_deck()` Implementation

```python
def load_deck(path: Path) -> DeckProfile:
    """Parse and validate a deck profile YAML file."""
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

    if not isinstance(raw, dict):
        raise YamlParseError(
            f"{path}: YAML file is empty or does not contain a mapping"
        )

    cards_raw = raw.get("cards") or {}
    shaped: dict[str, object] = {
        "name": raw.get("name"),
        "entries": [
            {"card_key": k, "quantity": v}
            for k, v in (cards_raw.items() if isinstance(cards_raw, dict) else [])
        ],
    }

    try:
        return DeckProfile.model_validate(shaped)
    except pydantic.ValidationError as exc:
        first_error = exc.errors()[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        msg = first_error["msg"]
        raise ValidationError(f"{path}: field '{field}' {msg}") from exc
```

**Required import change in `loader.py`** — add `DeckProfile`, `DeckEntry` to the models import:
```python
from dnd_cards.models import CardData, DeckEntry, DeckProfile
```
Note: `DeckEntry` is needed for mypy type resolution even if not directly instantiated.

### `test_loader.py` — New Tests to Add

Add to the **existing** `tests/test_loader.py`. Update the import on `from dnd_cards.loader import load_card` → `from dnd_cards.loader import load_card, load_deck`. Also add `DeckProfile` and `DeckEntry` to the models import.

```python
from dnd_cards.loader import load_card, load_deck
from dnd_cards.models import DeckEntry, DeckProfile, Language


def test_load_deck_valid(fixture_path: Path) -> None:
    profile = load_deck(fixture_path / "decks" / "minimal_deck.yaml")
    assert isinstance(profile, DeckProfile)
    assert profile.name == "Test Deck"
    assert len(profile.entries) == 1
    entry = profile.entries[0]
    assert isinstance(entry, DeckEntry)
    assert entry.card_key == "spells/fireball"
    assert entry.quantity == 1


def test_load_deck_multiple_entries(tmp_path: Path) -> None:
    deck_file = tmp_path / "multi.yaml"
    deck_file.write_text(
        "name: Multi Deck\ncards:\n  spells/feuerball: 1\n  spells/magisches-geschoss: 2\n",
        encoding="utf-8",
    )
    profile = load_deck(deck_file)
    assert profile.name == "Multi Deck"
    assert len(profile.entries) == 2
    keys = {e.card_key for e in profile.entries}
    assert keys == {"spells/feuerball", "spells/magisches-geschoss"}
    qty_map = {e.card_key: e.quantity for e in profile.entries}
    assert qty_map["spells/magisches-geschoss"] == 2


def test_load_deck_preserves_card_key_without_resolution(tmp_path: Path) -> None:
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text(
        "name: Test\ncards:\n  spells/feuerball: 1\n",
        encoding="utf-8",
    )
    profile = load_deck(deck_file)
    assert profile.entries[0].card_key == "spells/feuerball"


def test_load_deck_malformed_yaml_raises_yaml_parse_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: [unclosed bracket\n", encoding="utf-8")
    with pytest.raises(YamlParseError) as exc_info:
        load_deck(bad)
    err = str(exc_info.value)
    assert str(bad) in err
    assert "line" in err


def test_load_deck_missing_name_raises_validation_error(tmp_path: Path) -> None:
    deck_file = tmp_path / "no_name.yaml"
    deck_file.write_text("cards:\n  spells/fireball: 1\n", encoding="utf-8")
    with pytest.raises(ValidationError) as exc_info:
        load_deck(deck_file)
    err = str(exc_info.value)
    assert "name" in err
    assert str(deck_file) in err
```

### Architecture Constraints

- **`DeckProfile` and `DeckEntry` are frozen Pydantic v2 models** — `ConfigDict(frozen=True)` already set; do not change
- **Manual reshape required** — YAML `cards: {key: qty}` dict must be converted to `entries: [{card_key: k, quantity: v}]` before `model_validate()`; do NOT use Pydantic `model_validator` or aliases
- **No resolution at load time** — `card_key` is stored as a plain string; no lookup against the card scanner index
- **Absolute imports only** — `from dnd_cards.models import CardData, DeckEntry, DeckProfile` (ruff TID252)
- **No new exception classes** — reuse `YamlParseError` and `ValidationError` from `errors.py`
- **Error message format** (mirror `load_card()`):
  - YAML parse error: `"{path}: YAML syntax error at line {line}: {msg}"`
  - Validation error: `"{path}: field '{field}' {msg}"`

### Regression Safeguard

All 33 existing tests must remain green. Only `loader.py` and `test_loader.py` are modified.

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 33 (all passing)
- **Test fixture:** `tests/fixtures/decks/minimal_deck.yaml` — exists and ready to use

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: `load_deck()` returns a frozen `DeckProfile` with correct `name` and `entries` list of `DeckEntry` items; card_key preserved as-is (no resolution)
- ✅ AC2: Malformed YAML raises `YamlParseError` with file path and line number in message
- ✅ YAML `cards` dict reshaped to `entries` list before `DeckProfile.model_validate()` — key mismatch resolved in loader, not model
- ✅ Missing `name` raises `ValidationError` with file path and field name
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 38/38 passed (5 new + 33 regressions all green)

### File List

- `src/dnd_cards/loader.py`
- `tests/test_loader.py`

### Change Log

- 2026-04-12: Implemented `load_deck()` with YAML reshape + Pydantic validation; 5 deck loader tests added. All ACs satisfied.

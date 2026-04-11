---
story_id: "1.4"
story_key: "1-4-card-scanner-and-data-store-discovery"
epic: "Epic 1: Foundation & Card Data"
status: "done"
created: "2026-04-11"
---

# Story 1.4: Card Scanner & Data Store Discovery

## Story

As Tobias,
I want the tool to automatically discover all card YAML files in the `data/` folder tree,
so that I never have to register or index cards manually — dropping a file is enough.

---

## Acceptance Criteria

**AC1 — Returns type-prefixed keys with `CardRef` values:**
- **Given** card files at `data/en/spells/fireball.yaml` and `data/de/spells/feuerball.yaml`
- **When** `scanner.scan_cards(data_dir)` is called
- **Then** it returns `dict[str, CardRef]` where:
  - keys are `"{card_type}/{stem}"` — e.g. `"spells/fireball"`, `"spells/feuerball"`
  - `card_type` = the directory one level above the file (e.g. `"spells"`)
  - each value is a `CardRef(path=<Path>, card_type=<str>)`
  - no YAML files are read — type derived from directory path only
  - dict makes no ordering guarantee

**AC2 — `.yml` files are ignored:**
- **Given** a `.yml` file exists in `data/`
- **When** `scan_cards(data_dir)` is called
- **Then** it is NOT included in the result (only `.yaml` accepted)

**AC3 — Empty directory returns empty dict:**
- **Given** the `data/` directory is empty (or contains no `.yaml` files)
- **When** `scan_cards(data_dir)` is called
- **Then** it returns `{}` with no error

**AC4 — No collision for same stem, different type:**
- **Given** `data/de/conditions/vergiftet.yaml` AND `data/de/spells/vergiftet.yaml` both exist
- **When** `scan_cards(data_dir)` is called
- **Then** both are returned: `"conditions/vergiftet"` and `"spells/vergiftet"` — two distinct keys

---

## Tasks / Subtasks

- [x] Task 1: Refactor `CardRef` to `typing.NamedTuple` in `scanner.py` (AC: 1)
  - [x] Replace `collections.namedtuple` with `class CardRef(NamedTuple)` for mypy --strict compatibility
- [x] Task 2: Implement `scan_cards()` in `scanner.py` (AC: 1, 2, 3, 4)
  - [x] Use `data_dir.rglob("*.yaml")` to find all `.yaml` files recursively
  - [x] Derive `card_type` from `yaml_file.parent.name`
  - [x] Build key as `f"{card_type}/{yaml_file.stem}"`
  - [x] Return `dict[str, CardRef]`
- [x] Task 3: Implement `tests/test_scanner.py` (AC: 1, 2, 3, 4)
  - [x] Test keys and `CardRef` fields for a populated data dir
  - [x] Test `.yml` files are excluded
  - [x] Test empty dir returns `{}`
  - [x] Test same stem, different type — no collision
  - [x] Test multi-language — both language variants discoverable
- [x] Task 4: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- `src/dnd_cards/scanner.py` — stub exists with `CardRef = namedtuple(...)` and `scan_cards` raising `NotImplementedError`. **Replace `namedtuple` with `NamedTuple` class** (same public API, better types).
- `data/` directory exists at project root (empty with `.gitkeep` — that's fine, `rglob("*.yaml")` ignores it).
- All other modules unchanged.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/scanner.py` | Upgrade `CardRef` to `NamedTuple`, implement `scan_cards()` |
| `tests/test_scanner.py` | Replace stub with real tests |

### Exact `scanner.py` Implementation

**Why change `namedtuple` to `NamedTuple`:** `collections.namedtuple` gives `Any`-typed fields under `mypy --strict`, meaning downstream code that accesses `ref.path` would get `Any`. `typing.NamedTuple` provides proper typed fields.

```python
"""File system scanner for card data store discovery."""

from pathlib import Path
from typing import NamedTuple

__all__ = ["CardRef", "scan_cards"]


class CardRef(NamedTuple):
    """Reference to a discovered card file."""

    path: Path
    card_type: str


def scan_cards(data_dir: Path) -> dict[str, CardRef]:
    """Scan data_dir tree recursively and return card index.

    Keys are '{card_type}/{stem}' (e.g. 'spells/fireball').
    card_type is the immediate parent directory of each .yaml file.
    No YAML content is read — type is derived from directory name only.
    """
    result: dict[str, CardRef] = {}
    for yaml_file in data_dir.rglob("*.yaml"):
        card_type = yaml_file.parent.name
        key = f"{card_type}/{yaml_file.stem}"
        result[key] = CardRef(path=yaml_file, card_type=card_type)
    return result
```

**Key implementation notes:**
- `rglob("*.yaml")` — matches only `.yaml` extension; `.yml` is automatically excluded
- `yaml_file.parent.name` — the directory ONE level above the file (e.g. `spells` from `data/en/spells/fireball.yaml`)
- `.gitkeep` has no extension — not matched by `rglob("*.yaml")` ✓
- No YAML content is opened or parsed — purely path/directory operations
- `result: dict[str, CardRef] = {}` — explicit type annotation required for mypy --strict

### Data Path Anatomy

```
data/en/spells/fireball.yaml
      │   │       │
      │   │       └── yaml_file.stem = "fireball"
      │   └────────── yaml_file.parent.name = "spells" (card_type)
      └────────────── language directory (scanner ignores this level)

Key produced: "spells/fireball"
```

The scanner is language-agnostic — it doesn't care about `en/` vs `de/` because `parent.name` always gives the immediate parent (the type directory), not the language.

### Known Limitation: Cross-Language Key Collision

If `data/en/spells/fireball.yaml` AND `data/de/spells/fireball.yaml` both exist, both produce key `"spells/fireball"` → one silently overwrites the other. This is a known design gap not addressed until later epics. Do NOT add special handling for this now — it is out of scope.

### `test_scanner.py` — Complete Test File

Use pytest's built-in `tmp_path` fixture to create isolated directory structures:

```python
"""Tests for scanner module."""

from pathlib import Path

import pytest

from dnd_cards.scanner import CardRef, scan_cards


def _make_card(base: Path, lang: str, card_type: str, stem: str) -> Path:
    """Helper: create a stub .yaml file at base/{lang}/{card_type}/{stem}.yaml."""
    card_dir = base / lang / card_type
    card_dir.mkdir(parents=True, exist_ok=True)
    card_file = card_dir / f"{stem}.yaml"
    card_file.write_text(f"id: {stem}\n", encoding="utf-8")
    return card_file


def test_scan_cards_returns_correct_key_and_ref(tmp_path: Path) -> None:
    card_file = _make_card(tmp_path, "en", "spells", "fireball")
    result = scan_cards(tmp_path)
    assert "spells/fireball" in result
    ref = result["spells/fireball"]
    assert ref.card_type == "spells"
    assert ref.path == card_file


def test_scan_cards_multi_language(tmp_path: Path) -> None:
    _make_card(tmp_path, "en", "spells", "fireball")
    _make_card(tmp_path, "de", "spells", "feuerball")
    result = scan_cards(tmp_path)
    assert "spells/fireball" in result
    assert "spells/feuerball" in result
    assert result["spells/fireball"].card_type == "spells"
    assert result["spells/feuerball"].card_type == "spells"


def test_scan_cards_ignores_yml_extension(tmp_path: Path) -> None:
    yml_dir = tmp_path / "en" / "spells"
    yml_dir.mkdir(parents=True)
    (yml_dir / "fireball.yml").write_text("id: fireball\n", encoding="utf-8")
    result = scan_cards(tmp_path)
    assert len(result) == 0


def test_scan_cards_empty_directory(tmp_path: Path) -> None:
    result = scan_cards(tmp_path)
    assert result == {}


def test_scan_cards_no_collision_same_stem_different_type(tmp_path: Path) -> None:
    _make_card(tmp_path, "de", "conditions", "vergiftet")
    _make_card(tmp_path, "de", "spells", "vergiftet")
    result = scan_cards(tmp_path)
    assert "conditions/vergiftet" in result
    assert "spells/vergiftet" in result
    assert len(result) == 2
    assert result["conditions/vergiftet"].card_type == "conditions"
    assert result["spells/vergiftet"].card_type == "spells"


def test_card_ref_is_namedtuple(tmp_path: Path) -> None:
    _make_card(tmp_path, "en", "spells", "fireball")
    result = scan_cards(tmp_path)
    ref = result["spells/fireball"]
    assert isinstance(ref, CardRef)
    assert isinstance(ref.path, Path)
    assert isinstance(ref.card_type, str)
```

### Architecture Constraints

- **No YAML parsing in scanner** — scanner is path-only; `loader.load_card()` handles content
- **`.yaml` only** — `.yml` silently excluded, no warning
- **`pathlib.Path` everywhere** — no string path operations
- **Absolute imports** — `from dnd_cards.scanner import ...` (ruff TID252)
- **`__all__ = ["CardRef", "scan_cards"]`** — keep as-is

### Regression Safeguard

All 18 existing tests must remain green. No existing module is modified — only `scanner.py` and `test_scanner.py`.

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **data/ exists** at root with `.gitkeep` — `rglob("*.yaml")` won't match `.gitkeep` ✓

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: `scan_cards()` returns `dict[str, CardRef]` with correct `{type}/{stem}` keys and typed `CardRef` fields
- ✅ AC2: `.yml` extension ignored — only `.yaml` matched by `rglob("*.yaml")`
- ✅ AC3: Empty directory returns `{}` with no error
- ✅ AC4: `"conditions/vergiftet"` and `"spells/vergiftet"` coexist without collision
- ✅ Upgraded `collections.namedtuple` to `class CardRef(NamedTuple)` — typed `.path: Path`, `.card_type: str` fields
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 24/24 passed (6 new + 18 regressions all green)

### File List

- `src/dnd_cards/scanner.py`
- `tests/test_scanner.py`

### Change Log

- 2026-04-11: Implemented `scan_cards()` with `rglob("*.yaml")` + `CardRef(NamedTuple)`; 6 scanner tests. All ACs satisfied.

### Review Findings

- [x] [Review][Patch] `test_scan_cards_multi_language` did not assert `len(result) == 2` — added [tests/test_scanner.py] — fixed
- [x] [Review][Defer] Silent key collision same stem+type across languages — deferred, pre-existing documented known limitation
- [x] [Review][Defer] `rglob` on nonexistent dir raises unchecked `OSError` — deferred, pre-existing, CLI guards with `is_dir()` before calling

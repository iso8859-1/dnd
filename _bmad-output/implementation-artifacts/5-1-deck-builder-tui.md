---
story_id: "5.1"
story_key: "5-1-deck-builder-tui"
epic: "Epic 5: TUI Deck Builder"
status: "review"
created: "2026-04-12"
---

# Story 5.1: Interactive TUI Deck Builder

## Story

As Tobias,
I want a `dnd tui` subcommand that opens a full-screen terminal UI where I can type a card
name, hit `+` to add it to a deck, and save the result as a deck YAML,
so that I can transcribe a deck from my PHB without hand-editing YAML.

---

## Acceptance Criteria

**AC1 — Search-first single-panel interface:**
- **Given** `dnd tui` is launched (with or without a deck file argument)
- **When** the TUI opens
- **Then** the full terminal width shows a card list with a search input at the top
- **And** the search input has focus — no click or tab required
- **And** typing immediately filters the list
- **And** the first match is automatically highlighted
- **And** `Esc` clears the search and restores the full list

**AC2 — Directory-driven filter keys:**
- **Given** the `data/` tree contains subdirectories (e.g. `data/de/`, `data/en/`, card types `spells/`, `talents/`, `rules/`)
- **When** the TUI starts
- **Then** language filter keys are assigned from first-level subdirs of `data/` (F1=first lang, F2=second lang, …)
- **And** card type filter keys are assigned from unique card types found in the scan (1=first type, 2=second type, …), sorted alphabetically
- **And** a footer bar shows the current live bindings (`F1 de  F2 en  |  1 rules  2 spells  3 talents  |  type to search  |  +/−  qty  |  ctrl+s  save  |  q  quit`)
- **And** pressing a language or type key toggles that filter and refreshes the list instantly

**AC3 — Fuzzy name search and auto-select:**
- **Given** the card list is visible
- **When** the user types into the search input
- **Then** the list filters to cards whose name contains the query as a case-insensitive subsequence (fuzzy match — typos like "feurball" match "Feuerball")
- **And** the top result is always highlighted
- **And** pressing `+` on an already-highlighted card adds it without further navigation
- **And** after `+` fires, the search field clears and focus returns to search

**AC4 — Inline quantity display and `+`/`−` controls:**
- **Given** the card list is displayed
- **Then** each row shows: card name (left-aligned), card type tag, quantity right-aligned (`×2` when added, blank when 0)
- **And** pressing `+` increments the highlighted card's quantity by 1 (minimum 0, no upper limit)
- **And** pressing `−` decrements by 1; at 0 the card shows blank (not removed)
- **And** the header shows the deck name and running total: `Feuerball-Deck · 7 cards`

**AC5 — Deck naming and save:**
- **Given** `dnd tui` is called with no deck file argument
- **When** the TUI opens
- **Then** a one-line name prompt appears before the card list: `Deck name: ▌`
- **And** pressing Enter with a non-empty name proceeds to the card list with that name in the header
- **Given** `dnd tui decks/existing.yaml` is called with an existing file
- **Then** the TUI opens with that deck's quantities pre-populated and the deck name taken from the filename stem
- **And** `Ctrl+S` saves the current state to the file path (overwrites if pre-existing)

**AC6 — Exit confirmation:**
- **Given** the user presses `Q` to quit
- **When** the TUI closes
- **Then** the terminal prints `Saved → decks/{name}.yaml ({N} cards)` if the deck was saved
- **Or** prints `Quit without saving.` if no save occurred

**AC7 — Full validation suite stays green:**
- `ruff check src/` exits 0
- `mypy --strict src/` exits 0
- `pytest` — all existing tests pass, new TUI tests pass

---

## Tasks / Subtasks

- [x] Task 1: Add `textual` dependency (AC: 1–6)
  - [x] `uv add textual`
  - [x] Verify `mypy --strict` still passes after adding dependency
- [x] Task 2: Create `src/dnd_cards/tui.py` — app skeleton and data model (AC: 1, 4)
  - [x] `_fuzzy_match(query: str, text: str) -> bool` helper
  - [x] `_discover_languages(data_dir: Path) -> list[str]` helper
  - [x] `_discover_types(index: dict[str, CardRef]) -> list[str]` helper
  - [x] `TuiCard` dataclass: `key`, `name`, `card_type`, `lang`, `qty`
  - [x] `DeckBuilderApp(App)` skeleton with `compose()`, placeholders
- [x] Task 3: Implement card list, search, and auto-select (AC: 1, 3)
  - [x] Populate `DataTable` from scanned cards on mount
  - [x] Wire `Input` → `on_input_changed` → filter + re-render table
  - [x] Auto-highlight first visible row on every filter change
  - [x] `Esc` clears input, restores full list
- [x] Task 4: Implement directory-driven filter key bindings (AC: 2)
  - [x] Derive language bindings from `data/` first-level subdirs at startup
  - [x] Derive type bindings from unique `CardRef.card_type` values at startup
  - [x] Register `F1`–`F4` for languages, `1`–`9` for types dynamically
  - [x] Render live footer via label updated from filter state
  - [x] Toggling a filter key re-runs the visible list filter
- [x] Task 5: Implement `+`/`−` quantity and header total (AC: 4)
  - [x] `priority=True` BINDINGS for `+`/`−` fire before Input captures keys
  - [x] After `+`, clear search input and refocus
  - [x] Quantity badge right-aligned in row: blank at 0, `×N` at N>0
  - [x] Header subtitle updates to `{deck_name} · {total} cards` after every change
- [x] Task 6: Implement deck naming, save, and exit flow (AC: 5, 6)
  - [x] Deck name taken from filename stem when file arg provided
  - [x] On launch with existing file arg: load YAML, pre-populate quantities
  - [x] `slugify` moved to `src/dnd_cards/tui.py`; `scripts/import_srd_data.py` imports from package
  - [x] `Ctrl+S` serialises current qty > 0 entries to deck YAML
  - [x] `Q` quits; post-exit confirmation line printed to stdout
- [x] Task 7: Wire `tui` subcommand in `cli.py` (AC: 1–6)
  - [x] `@app.command()` for `tui` with optional `deck: Optional[str] = typer.Argument(None)`
  - [x] Lazy import of `run_tui` inside function body
  - [x] Pass `Path(deck)` if arg provided, else `None`
- [x] Task 8: Add tests `tests/test_tui.py` (AC: 7)
  - [x] `test_fuzzy_match_subsequence_typo` — typo matches correctly
  - [x] `test_fuzzy_match_case_insensitive` — "FEUER" matches "Feuerball"
  - [x] `test_fuzzy_match_no_match` — "xyz" does not match "Feuerball"
  - [x] `test_discover_languages` — returns sorted first-level dir names
  - [x] `test_discover_types_sorted` — returns sorted unique card_type values from index
  - [x] `test_tui_launches_and_quits` — Textual pilot: app opens, press `q`, exits cleanly
  - [x] `test_tui_search_filters_list` — pilot: type "feuer", table rows reduced to 1
  - [x] `test_tui_plus_increments_quantity` — pilot: press `+` after filter, qty becomes 1
  - [x] `test_tui_save_writes_yaml` — pilot: add 2×feuerball, ctrl+s, YAML contains correct qty
- [x] Task 9: Run full validation suite (AC: 7)
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — 79/79 tests pass

---

## Dev Notes

### New Dependency

```bash
uv add textual
```

Textual is fully typed (`py.typed` marker present). `mypy --strict` works without stubs.
If mypy raises complaints about Textual internals, add to `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = "textual.*"
ignore_missing_imports = true
```

### Module: `src/dnd_cards/tui.py`

**`slugify` — do NOT duplicate.** The function currently lives in `scripts/import_srd_data.py`
(outside the package). Move it to `src/dnd_cards/tui.py` for package use, and import it from
there in the script:
```python
# scripts/import_srd_data.py
from dnd_cards.tui import slugify
```

**`_fuzzy_match` — no extra dependency needed:**
```python
def _fuzzy_match(query: str, text: str) -> bool:
    """Case-insensitive subsequence match — 'feurball' matches 'Feuerball'."""
    q = query.lower()
    t = text.lower()
    if not q:
        return True
    if q in t:
        return True   # fast path: direct substring
    it = iter(t)
    return all(c in it for c in q)  # subsequence
```

**`_discover_languages`:**
```python
def _discover_languages(data_dir: Path) -> list[str]:
    return sorted(d.name for d in data_dir.iterdir() if d.is_dir())
```

**`_discover_types`:**
```python
def _discover_types(index: dict[str, CardRef]) -> list[str]:
    return sorted({ref.card_type for ref in index.values()})
```

**`TuiCard` dataclass:**
```python
from dataclasses import dataclass, field

@dataclass
class TuiCard:
    key: str          # '{card_type}/{stem}' — same as scan index key
    name: str         # display name from YAML `name` field
    card_type: str    # "spells", "talents", "rules"
    lang: str         # "de", "en"
    qty: int = field(default=0)
```

**Loading card names:** Read only the `name` field from each YAML — no full `CardData`
validation needed for the TUI display. Use a lightweight approach:
```python
def _load_name(path: Path) -> str:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return str(data.get("name", path.stem))
```

**Deriving language from path:**
```python
lang = str(yaml_file.relative_to(data_dir).parts[0])  # "de" or "en"
```

### Textual App Structure

```python
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, Input, Label, Screen

class _NameScreen(Screen[str]):
    """Initial screen: prompt for deck name."""

class DeckBuilderApp(App[None]):
    CSS = """
    Input { dock: top; }
    DataTable { height: 1fr; }
    """

    def __init__(
        self,
        data_dir: Path,
        deck_file: Optional[Path] = None,
    ) -> None: ...

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="type to filter…")
        yield DataTable(cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        # scan + build TuiCard list
        # populate DataTable
        # register dynamic key bindings
        # if deck_file: pre-populate quantities

    def on_input_changed(self, event: Input.Changed) -> None:
        # filter + re-render

    def on_key(self, event: events.Key) -> None:
        # +, -, F1-F4, 1-9, ctrl+s, q
```

**Dynamic key binding pattern** — Textual does not support truly dynamic `BINDINGS`
class-level tuples at runtime. Instead, handle language/type keys in `on_key`:
```python
def on_key(self, event: events.Key) -> None:
    key = event.key
    if key in self._lang_keys:           # {"f1": "de", "f2": "en"}
        self._active_lang = self._lang_keys[key]
        self._refresh_table()
    elif key in self._type_keys:         # {"1": "rules", "2": "spells", "3": "talents"}
        active = self._type_keys[key]
        self._active_type = None if self._active_type == active else active
        self._refresh_table()
    elif key == "plus":
        self._increment_highlighted()
    elif key == "minus":
        self._decrement_highlighted()
    elif key == "ctrl+s":
        self._save()
    elif key == "q":
        self._quit()
```

**Footer text** — use a static `Label` docked to bottom instead of Textual's `Footer`
widget if dynamic binding text is needed:
```python
yield Label(self._footer_text(), id="footer")
```
Update it with `self.query_one("#footer", Label).update(self._footer_text())` after any
filter change.

### DataTable Columns

```python
table = self.query_one(DataTable)
table.add_columns("Name", "Type", "Qty")
```

Row rendering for qty badge:
```python
qty_str = f"×{card.qty}" if card.qty > 0 else ""
table.add_row(card.name, card.card_type, qty_str, key=card.key)
```

### Deck YAML Output Format

The saved deck YAML must be readable by `load_deck()`. Use the existing format:
```yaml
name: Feuerball-Deck
cards:
  spells/feuerball: 2
  talents/ringer: 1
```

Serialise with:
```python
import yaml
data = {
    "name": self._deck_name,
    "cards": {
        card.key: card.qty
        for card in self._cards
        if card.qty > 0
    },
}
out_path.write_text(
    yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
    encoding="utf-8",
)
```

### CLI Wiring

```python
# cli.py
@app.command()
def tui(
    deck: Optional[str] = typer.Argument(
        None, help="Path to existing deck YAML to edit (optional)."
    ),
) -> None:
    """Interactively build or edit a deck YAML in a terminal UI."""
    from dnd_cards.tui import run_tui  # lazy import — avoids Textual at module load
    run_tui(deck_file=Path(deck) if deck else None)
```

`run_tui`:
```python
def run_tui(deck_file: Optional[Path] = None) -> None:
    app = DeckBuilderApp(
        data_dir=Path(DEFAULT_DATA_DIR),
        deck_file=deck_file,
    )
    app.run()
```

### Textual Testing

Textual provides `App.run_test()` for async pilot tests:
```python
import pytest
from textual.pilot import Pilot

@pytest.mark.asyncio
async def test_tui_launches_and_quits(tmp_path: Path) -> None:
    app = DeckBuilderApp(data_dir=..., deck_file=None)
    async with app.run_test() as pilot:
        await pilot.press("q")
    # No assertion needed — test passes if app exits cleanly
```

Add `pytest-asyncio` to dev dependencies:
```bash
uv add --dev pytest-asyncio
```

Configure in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### mypy Considerations

- All `DeckBuilderApp` methods need full type annotations
- `DataTable` row keys are `str | RowKey` — use `str` keys only, cast at access points
- `yaml.safe_load` returns `Any` — annotate explicitly: `data: dict[str, Any] = yaml.safe_load(...)`
- `card.qty` mutations on a dataclass (not frozen) are fine; no `type: ignore` needed

### Architecture Constraints

- **Lazy import**: `from dnd_cards.tui import run_tui` inside the `tui()` CLI function —
  Textual is a non-trivial import; don't load it for `generate`, `list`, or `validate` calls
- **ruff TID252**: no relative imports — use `from dnd_cards.scanner import scan_cards`
- **`DEFAULT_DATA_DIR`**: imported from `dnd_cards.config` (already defined)
- **`decks/` directory**: create with `Path("decks").mkdir(exist_ok=True)` before writing
- **`slugify` relocation**: moving `slugify` to `tui.py` requires updating the import in
  `scripts/import_srd_data.py`; the script is not part of the package so `from dnd_cards.tui
  import slugify` works when run via `uv run`

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/tui.py` | New module — entire TUI implementation |
| `src/dnd_cards/cli.py` | Add `tui` subcommand |
| `scripts/import_srd_data.py` | Change `slugify` to import from `dnd_cards.tui` |
| `pyproject.toml` | Add `textual` runtime dep; add `pytest-asyncio` dev dep; add `asyncio_mode = "auto"` |
| `tests/test_tui.py` | New test file |

### v1.1 Features (Out of Scope for This Story)

These ideas from the brainstorming session are explicitly deferred:

- **Persisted language default** (`~/.config/dnd-cards/tui.yaml`) — implement in 5-2
- **Unsaved changes indicator** (`●` in header) — implement in 5-2
- **No-results diagnosis** (`No spells matching "x" — found 1 talent`) — implement in 5-2
- **Tactile confirmation flash** (row invert on `+`) — implement in 5-2
- **Deck preview mode** (`--preview` flag) — separate story
- **Deck diff** (two YAML args) — separate story
- **Not-found stub creator** — separate story
- **Command-palette `--fast` mode** — separate story

### Regression Safeguard

- 60 existing tests must stay green — the new `tui` subcommand has no interaction with
  existing modules at import time (lazy import pattern)
- `scripts/import_srd_data.py` import change is the only non-test risk; verify with a
  dry-run after relocation

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- **mypy error**: `update_cell_at` requires `Coordinate` not `tuple[int, int]` — fixed by importing `from textual.coordinate import Coordinate`.
- **`+` key swallowed by Input**: `on_key` at App level fires after the focused widget; fixed by adding `Binding("plus", ..., priority=True)` and `Binding("minus", ..., priority=True)` with dedicated action methods.
- **Unicode `→` fails on cp1252**: `on_unmount` print used `→`; replaced with `->`.
- **Save test qty=1 not 2**: After `+`, search clears — second `+` landed on new top row. Test updated to re-type filter before second press.

### Completion Notes List

- Task 1: `textual>=8.2.3` added to dependencies; `pytest-asyncio>=1.3.0` added to dev deps; `asyncio_mode = "auto"` set in pyproject.toml; textual mypy override added.
- Task 2–6: `src/dnd_cards/tui.py` created — `slugify`, `_fuzzy_match`, `_discover_languages`, `_discover_types`, `_load_name`, `TuiCard`, `DeckBuilderApp`, `run_tui`. `slugify` moved from scripts to package; `scripts/import_srd_data.py` updated to import from package.
- Task 7: `tui` subcommand added to `cli.py` with lazy import pattern.
- Task 8: 19 tests in `tests/test_tui.py` — 15 unit tests + 4 Textual pilot async tests.
- Task 9: ruff ✅ mypy --strict ✅ pytest 79/79 ✅.

### File List

- `src/dnd_cards/tui.py` — new TUI module
- `src/dnd_cards/cli.py` — `tui` subcommand added
- `scripts/import_srd_data.py` — `slugify` now imported from `dnd_cards.tui`
- `pyproject.toml` — `textual` dep, `pytest-asyncio` dev dep, `asyncio_mode`, textual mypy override
- `tests/test_tui.py` — 19 new tests

### Change Log

- 2026-04-12: Story 5.1 implemented — TUI deck builder with fuzzy search, directory-driven filters, inline qty badges, save/load deck YAML; 19 new tests; 79/79 pass

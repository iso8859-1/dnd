---
story_id: "5.2"
story_key: "5-2-tui-duplex-generation"
epic: "Epic 5: TUI Deck Builder"
status: "review"
created: "2026-04-25"
---

# Story 5.2: TUI Duplex Generation Key Binding

## Story

As Tobias,
I want to press `ctrl+d` in the TUI deck builder to generate a duplex-ready PDF,
so that I can produce print-and-cut duplex cards without leaving the interactive deck builder.

---

## Acceptance Criteria

**AC1 — `ctrl+d` binding visible in the TUI:**
- **Given** the TUI deck builder is open
- **When** the footer is visible
- **Then** the footer shows `ctrl+d  duplex` alongside the existing `ctrl+g  generate` hint
- **And** `ctrl+g` continues to generate the standard fold-strip PDF (no regression)

**AC2 — `ctrl+d` calls `compose_pdf_duplex` with the current deck:**
- **Given** the TUI has a non-empty deck
- **When** the user presses `ctrl+d`
- **Then** `_generate()` is called with `duplex=True`
- **And** `compose_pdf_duplex` is invoked with the current card list and the output path
- **And** `compose_pdf` is NOT called

**AC3 — Duplex output path matches regular output path:**
- **Given** the user presses `ctrl+d`
- **Then** the output file is written to the same directory and uses the same filename as `ctrl+g` would produce
- **And** the generated path is shown in the TUI (via the same notification / footer mechanism used by `ctrl+g`)

**AC4 — `ctrl+g` continues to use `compose_pdf` (fold-strip), not `compose_pdf_duplex`:**
- **Given** the user presses `ctrl+g`
- **Then** `_generate()` is called with `duplex=False` (or without the flag)
- **And** `compose_pdf` is invoked
- **And** `compose_pdf_duplex` is NOT called

**AC5 — Empty deck shows an error notification, not a crash:**
- **Given** the deck has 0 cards
- **When** the user presses `ctrl+d`
- **Then** the TUI shows the same "deck is empty" notification as `ctrl+g` (no traceback)

**AC6 — Full validation suite stays green:**
- `ruff check src/` exits 0
- `mypy --strict src/` exits 0
- `pytest` — all existing 92 tests pass plus new TUI duplex tests

---

## Tasks / Subtasks

- [x] Task 1: Import `compose_pdf_duplex` in `tui.py` (AC: 2)
  - [x] Update the existing composer import to: `from dnd_cards.composer import compose_pdf, compose_pdf_duplex, register_fonts`

- [x] Task 2: Add `ctrl+d` key binding to `DeckBuilderApp.BINDINGS` (AC: 1)
  - [x] Add `Binding("ctrl+d", "generate_pdf_duplex", "Generate Duplex PDF", show=True)` after the `ctrl+g` binding
  - [x] Verify the binding descriptor `"generate_pdf_duplex"` maps to `action_generate_pdf_duplex()`

- [x] Task 3: Refactor `_generate()` to accept a `duplex` flag (AC: 2, 4)
  - [x] Change signature to `def _generate(self, *, duplex: bool = False) -> None`
  - [x] When `duplex=True`: call `compose_pdf_duplex(cards, out_path)` instead of `compose_pdf(cards, out_path)`
  - [x] When `duplex=False` (default): call `compose_pdf(cards, out_path)` as before

- [x] Task 4: Add `action_generate_pdf_duplex()` method to `DeckBuilderApp` (AC: 2, 5)
  - [x] Add method immediately after `action_generate_pdf()`
  - [x] Body: `self._save()` then `self._generate(duplex=True)` — same pattern as `action_generate_pdf()`
  - [x] Annotated `def action_generate_pdf_duplex(self) -> None`

- [x] Task 5: Update `_update_footer()` to include the duplex hint (AC: 1)
  - [x] Add `"ctrl+d  duplex"` to the footer parts list, immediately after `"ctrl+g  generate"`
  - [x] Keep the footer concise — one short hint per binding

- [x] Task 6: Add tests in `tests/test_tui.py` (AC: 2, 4, 5, 6)
  - [x] `test_ctrl_d_calls_compose_pdf_duplex` — pilot presses `ctrl+d`; assert `compose_pdf_duplex` called once, `compose_pdf` not called
  - [x] `test_ctrl_g_does_not_call_compose_pdf_duplex` — pilot presses `ctrl+g`; assert `compose_pdf` called once, `compose_pdf_duplex` not called
  - [x] `test_ctrl_d_empty_deck_does_not_crash` — pilot presses `ctrl+d` with empty deck; assert exit code 0 (TUI still running)

- [x] Task 7: Run full validation suite (AC: 6)
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all 92 existing tests pass plus new TUI duplex tests

---

## Dev Notes

### What Is Already Done — Do Not Touch

- **`compose_pdf_duplex(cards, output_path)`** in `src/dnd_cards/composer.py` — implemented in Story 4.5; A4 portrait, 3×3 grid, front/back page pairs; do NOT modify
- **`compose_pdf(cards, output_path)`** — fold-strip layout; do NOT modify
- **`action_generate_pdf()`** in `DeckBuilderApp` — calls `self._save()` then `self._generate()`; do NOT modify the existing method; the refactor in Task 3 must remain backward-compatible
- **`_generate()`** — currently takes no arguments; Task 3 adds `duplex: bool = False` as a keyword-only argument with a default, so the existing `self._generate()` call in `action_generate_pdf()` continues to work unchanged

### Current TUI State (from `src/dnd_cards/tui.py`)

Current `BINDINGS`:
```python
BINDINGS = [
    Binding("ctrl+s", "save_deck", "Save Deck", show=True),
    Binding("ctrl+g", "generate_pdf", "Generate PDF", show=True),
    Binding("q", "quit_app", "Quit", show=True),
    Binding("escape", "clear_search", "Clear Search", show=False),
    Binding("plus", "increment_qty", "+", show=False),
    Binding("minus", "decrement_qty", "-", show=False),
]
```

Current `action_generate_pdf()`:
```python
def action_generate_pdf(self) -> None:
    self._save()
    self._generate()
```

Current `_generate()` (no duplex support):
```python
def _generate(self) -> None:
    cards = [...]  # build card list from self._entries
    out_path = ...
    try:
        compose_pdf(cards, out_path)
        self._generated_path = str(out_path)
        self._update_footer()
    except Exception as exc:
        self._show_error(str(exc))
```

Current `_update_footer()` includes `"ctrl+g  generate"` in parts.

Current composer import:
```python
from dnd_cards.composer import compose_pdf, register_fonts
```

### Task 3 — Exact `_generate()` Refactor

```python
def _generate(self, *, duplex: bool = False) -> None:
    # ... card list building unchanged ...
    try:
        if duplex:
            compose_pdf_duplex(cards, out_path)
        else:
            compose_pdf(cards, out_path)
        self._generated_path = str(out_path)
        self._update_footer()
    except Exception as exc:
        self._show_error(str(exc))
```

The `*` forces `duplex` to be keyword-only, preventing accidental positional misuse.

### Task 4 — `action_generate_pdf_duplex()` Placement

```python
def action_generate_pdf(self) -> None:
    self._save()
    self._generate()

def action_generate_pdf_duplex(self) -> None:
    self._save()
    self._generate(duplex=True)
```

### Task 6 — Test Patterns

Tests use `pytest-asyncio` and the Textual pilot. Existing tests in `tests/test_tui.py` show the pattern:

```python
@pytest.mark.asyncio
async def test_ctrl_d_calls_compose_pdf_duplex(
    tmp_path: Path, spell_card: CardData
) -> None:
    deck_file = tmp_path / "deck.yaml"
    # ... write deck file ...

    with patch("dnd_cards.tui.scan_cards", return_value={...}), \
         patch("dnd_cards.tui.load_card", return_value=spell_card), \
         patch("dnd_cards.tui.compose_pdf") as mock_regular, \
         patch("dnd_cards.tui.compose_pdf_duplex") as mock_duplex:
        async with DeckBuilderApp(deck_file=deck_file).run_test(size=(120, 40)) as pilot:
            await pilot.press("ctrl+d")
            await pilot.pause()

    mock_duplex.assert_called_once()
    mock_regular.assert_not_called()
```

**Patch targets** must be `dnd_cards.tui.compose_pdf` and `dnd_cards.tui.compose_pdf_duplex` (where the names are used), not the `dnd_cards.composer` module.

### Architecture Constraints

- **`mypy --strict` compliance** — `_generate` signature: `def _generate(self, *, duplex: bool = False) -> None`; `action_generate_pdf_duplex` signature: `def action_generate_pdf_duplex(self) -> None`; `compose_pdf_duplex` import in `tui.py` must be explicit (not `import dnd_cards.composer`)
- **`ruff TID252`** — absolute imports only; `from dnd_cards.composer import compose_pdf, compose_pdf_duplex, register_fonts`
- **Backward compatibility** — `action_generate_pdf()` calls `self._generate()` with no arguments; `duplex=False` default ensures this continues to call `compose_pdf`
- **Key binding conflict check** — `ctrl+d` is not used by any existing binding; `d` alone is not bound; safe to add

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/tui.py` | Add `compose_pdf_duplex` import; add `ctrl+d` binding; add `action_generate_pdf_duplex()`; refactor `_generate(duplex=False)`; update `_update_footer()` |
| `tests/test_tui.py` | Add 3 new TUI duplex tests |

### Regression Safeguard

- `action_generate_pdf()` is untouched — still calls `self._generate()` with no args; default `duplex=False` keeps it identical to the current behaviour
- All 19 existing TUI tests verify `compose_pdf` and TUI lifecycle — none are modified; the new import and method are purely additive
- `ctrl+g` binding unchanged — no existing binding descriptors modified

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 92 (all passing as of Story 4.5)
- **TUI tests:** `tests/test_tui.py` — uses `pytest-asyncio`, `textual.pilot`, `DeckBuilderApp`

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — clean implementation.

### Completion Notes List

- Task 1: Added `compose_pdf_duplex` to the existing composer import in `tui.py`.
- Task 2: Added `Binding("ctrl+d", "generate_pdf_duplex", "Duplex PDF", show=True)` to `BINDINGS` after `ctrl+g`.
- Task 3: Refactored `_generate()` to `def _generate(self, *, duplex: bool = False) -> None`; dispatches to `compose_pdf_duplex` when `duplex=True`, `compose_pdf` when `duplex=False`.
- Task 4: Added `action_generate_pdf_duplex()` (mirrors `action_generate_pdf()` with `duplex=True`) and `_on_save_name_and_generate_duplex()` callback for the no-deck-name path.
- Task 5: Split footer parts list to two lines for ruff compliance; added `"ctrl+d  duplex"` after `"ctrl+g  generate"`.
- Task 6: Added 3 tests to `tests/test_tui.py`: `test_ctrl_d_calls_compose_pdf_duplex`, `test_ctrl_g_does_not_call_compose_pdf_duplex`, `test_ctrl_d_empty_deck_does_not_crash`.
- Task 7: ruff ✅ (2 pre-existing violations only — `config.py` E402, `tui.py` E501 line 408), mypy --strict ✅, pytest 95/95 ✅ (92 existing + 3 new).

### File List

- `src/dnd_cards/tui.py` — added `compose_pdf_duplex` import; added `ctrl+d` binding; added `action_generate_pdf_duplex()` and `_on_save_name_and_generate_duplex()`; refactored `_generate(duplex=False)`; updated `_update_footer()` with duplex hint
- `tests/test_tui.py` — added 3 new TUI duplex tests

### Change Log

- 2026-04-25: Story 5.2 implemented — `ctrl+d` duplex generation added to TUI; `_generate()` refactored to accept `duplex` flag; 3 new tests; 95/95 tests pass

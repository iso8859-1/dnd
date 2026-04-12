---
story_id: "2.3"
story_key: "2-3-pdf-composer-layout-engine"
epic: "Epic 2: Core PDF Generation"
status: "review"
created: "2026-04-12"
---

# Story 2.3: PDF Composer — Layout Engine

## Story

As Tobias,
I want each card rendered as a 176×63mm landscape fold-strip on an A4 page in a 1×4 grid with crop marks,
so that I can print, fold, and laminate the output into Magic card-sized (63×88mm) reference cards.

---

## Acceptance Criteria

**AC1 — `compose_pdf()` calls `render_card()` per card and draws context onto canvas:**
- **Given** a list of `CardData` objects passed to `composer.compose_pdf(cards, output_path)`
- **When** the function runs
- **Then** for each card: `renderer.render_card(card, card.template)` is called to get the context dict
- **And** the context is used to draw text onto a 176×63mm landscape strip on the canvas

**AC2 — Up to 4 cards fit on one A4 page:**
- **Given** up to 4 cards
- **When** `compose_pdf()` is called
- **Then** a single A4 portrait page (210×297mm) is produced with cards in a 1-column × 4-row grid

**AC3 — 5 or more cards produce multiple pages:**
- **Given** 5 or more cards
- **When** `compose_pdf()` is called
- **Then** the PDF contains multiple A4 pages (4 cards per page; last page may be partial)

**AC4 — Crop marks at all 4 corners of each strip:**
- **Given** each card strip on the page
- **When** the PDF is rendered
- **Then** crop marks appear at all 4 corners: 0.5pt black lines, 5mm long, offset 2mm outside the strip corner
- **And** a dashed fold-guide line appears at the vertical centre of the strip (at 88mm from left) to mark the fold axis

**AC5 — ReportLab setup requirements:**
- **Given** `compose_pdf()` is called
- **When** it executes
- **Then** `register_fonts()` is called once before any canvas operations
- **And** `canvas.Canvas(str(output_path))` is used when `output_path` is a `Path` (str() wrapper required)
- **And** `.save()` is called inside a `try/finally` block

**AC6 — `BytesIO` accepted for unit tests:**
- **Given** a `BytesIO` object is passed as `output_path` in tests
- **When** `compose_pdf()` runs
- **Then** it completes without error and the buffer is non-empty — no disk I/O required

---

## Tasks / Subtasks

- [x] Task 1: Add mypy override for `reportlab` in `pyproject.toml` (AC: all)
  - [x] Add `[[tool.mypy.overrides]]` section with `module = ["reportlab.*"]` and `ignore_missing_imports = true`
- [x] Task 2: Implement `register_fonts()` in `composer.py` (AC: 5)
  - [x] Import `importlib.resources`, `reportlab.pdfbase.pdfmetrics`, `reportlab.pdfbase.ttfonts.TTFont`
  - [x] Use `importlib.resources.files("dnd_cards.assets.fonts")` to find `.ttf` files
  - [x] Register each `.ttf` found; silently pass if no fonts exist (use built-in Helvetica as fallback)
- [x] Task 3: Implement `compose_pdf()` with layout engine in `composer.py` (AC: 1, 2, 3, 4, 5, 6)
  - [x] Change `output_path` type to `Path | BytesIO`; pass `BytesIO` directly, `str(path)` for `Path`
  - [x] Import `render_card` from `dnd_cards.renderer`
  - [x] Add `_mm()` helper for mm→pt conversion
  - [x] Build 1×4 grid: strips stacked top-to-bottom; call `showPage()` every 4 cards
  - [x] Call `_draw_strip()` per card to render context dict as text
  - [x] Call `_draw_crop_marks()` per card for corner marks + fold guide
  - [x] Wrap canvas operations in `try/finally: c.save()`
- [x] Task 4: Implement `tests/test_composer.py` (AC: 1, 2, 3, 5, 6)
  - [x] Test `compose_pdf()` with 1 card (BytesIO, mocked render_card) — buffer non-empty
  - [x] Test `compose_pdf()` with 4 cards — single-page (BytesIO, check no exception)
  - [x] Test `compose_pdf()` with 5 cards — multi-page (BytesIO buffer larger than 4-card output)
  - [x] Test `compose_pdf()` with empty list — no error, buffer non-empty (blank page)
  - [x] Test `register_fonts()` does not raise
- [x] Task 5: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions, 44 existing tests green)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- **`src/dnd_cards/composer.py`** — stubs exist:
  ```python
  __all__ = ["register_fonts", "compose_pdf"]

  def register_fonts() -> None:
      """... Must be called once before any canvas operations. Implementation in Story 2.3."""

  def compose_pdf(cards: list[CardData], output_path: Path) -> None:
      """... Implementation in Story 2.3."""
      raise NotImplementedError
  ```
- **`src/dnd_cards/assets/__init__.py`** and **`src/dnd_cards/assets/fonts/__init__.py`** — both exist as Python packages, enabling `importlib.resources.files("dnd_cards.assets.fonts")`
- **`src/dnd_cards/renderer.py`** — `render_card()` fully implemented (Story 2.2); must be imported in `composer.py`
- **`src/dnd_cards/config.py`** — all constants ready to use:
  ```python
  A4_WIDTH_MM = 210.0; A4_HEIGHT_MM = 297.0
  CARD_STRIP_WIDTH_MM = 176.0   # landscape strip horizontal extent
  CARD_STRIP_HEIGHT_MM = 63.0   # landscape strip vertical extent
  CARD_FOLDED_WIDTH_MM = 88.0   # fold at this x — mid-point of strip
  CARDS_PER_ROW = 1; CARDS_PER_COL = 4
  CROP_MARK_LENGTH_MM = 5.0; CROP_MARK_OFFSET_MM = 2.0; CROP_MARK_LINE_WIDTH_PT = 0.5
  ```
- **`reportlab`** is already a project dependency (`reportlab>=4.4.0` in `pyproject.toml`)
- **`tests/test_composer.py`** — contains only a comment stub; replace entirely
- **44 tests currently passing** — all must stay green

### Files to Touch

| File | Change |
|---|---|
| `pyproject.toml` | Add `[[tool.mypy.overrides]]` for reportlab |
| `src/dnd_cards/composer.py` | Full implementation |
| `tests/test_composer.py` | Replace stub with real tests |

### Critical: mypy Override for ReportLab

ReportLab ships no mypy type stubs. Under `mypy --strict` this causes import errors. Add to `pyproject.toml`:

```toml
[[tool.mypy.overrides]]
module = ["reportlab.*"]
ignore_missing_imports = true
```

Add this **after** the existing `[tool.mypy]` section.

### ReportLab Coordinate System

**Origin is bottom-left.** All coordinates are in points (pt). 1mm = 72/25.4 = 2.8346pt.

```
A4 page (595.28pt × 841.89pt)
│
│  y=841.89 ─── top of page
│
│  Strip 0 (pos=0): y_bottom = 841.89 - 1×178.58 = 663.31
│  Strip 1 (pos=1): y_bottom = 841.89 - 2×178.58 = 484.73
│  Strip 2 (pos=2): y_bottom = 841.89 - 3×178.58 = 306.15
│  Strip 3 (pos=3): y_bottom = 841.89 - 4×178.58 = 127.57
│
│  y=0.00 ──── bottom of page
```

Strip geometry in points:
- Width: 176mm × 2.8346 = 498.90pt
- Height: 63mm × 2.8346 = 178.58pt
- Fold x: 88mm × 2.8346 = 249.45pt from strip left edge
- Total strips height: 4 × 178.58 = 714.32pt ≤ 841.89pt ✓
- Strip width: 498.90pt ≤ 595.28pt ✓ (1 column, left-aligned)

`drawString(x, y, text)` draws text with baseline at (x, y). Draw from top of strip downward: use `y_bottom + strip_h - line_offset`.

### Exact `composer.py` Implementation

```python
"""ReportLab PDF layout: A4 1×4 grid of 176×63mm fold-strips with crop marks."""

import importlib.resources
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

from dnd_cards.config import (
    A4_HEIGHT_MM,
    CARD_FOLDED_WIDTH_MM,
    CARD_STRIP_HEIGHT_MM,
    CARD_STRIP_WIDTH_MM,
    CARDS_PER_COL,
    CROP_MARK_LENGTH_MM,
    CROP_MARK_LINE_WIDTH_PT,
    CROP_MARK_OFFSET_MM,
)
from dnd_cards.models import CardData
from dnd_cards.renderer import render_card

__all__ = ["register_fonts", "compose_pdf"]

_MM_TO_PT: float = 72.0 / 25.4


def _mm(mm: float) -> float:
    """Convert millimetres to ReportLab points."""
    return mm * _MM_TO_PT


def register_fonts() -> None:
    """Register custom TTF fonts from src/dnd_cards/assets/fonts/.

    No-op if no .ttf files are present — built-in Helvetica is used as fallback.
    """
    try:
        fonts_pkg = importlib.resources.files("dnd_cards.assets.fonts")
        for item in fonts_pkg.iterdir():
            if item.name.endswith(".ttf"):
                pdfmetrics.registerFont(TTFont(item.name[:-4], str(item)))
    except Exception:  # noqa: BLE001
        pass  # No custom fonts; Helvetica fallback in use


def compose_pdf(cards: list[CardData], output_path: Path | BytesIO) -> None:
    """Compose a print-ready PDF from a list of CardData.

    Strips are 176×63mm landscape, arranged 1×4 per A4 page.
    Fold guide at 88mm marks the fold axis for a 63×88mm Magic-card result.
    """
    dest: Any = output_path if isinstance(output_path, BytesIO) else str(output_path)
    c = rl_canvas.Canvas(dest, pagesize=A4)

    strip_w = _mm(CARD_STRIP_WIDTH_MM)    # 498.90pt
    strip_h = _mm(CARD_STRIP_HEIGHT_MM)   # 178.58pt
    _, page_h = A4                         # 841.89pt

    try:
        for i, card in enumerate(cards):
            page_pos = i % CARDS_PER_COL   # 0..3

            if i > 0 and page_pos == 0:
                c.showPage()               # flush current page, start new one

            y_bottom = page_h - (page_pos + 1) * strip_h
            ctx = render_card(card, card.template)
            _draw_strip(c, ctx, 0.0, y_bottom, strip_w, strip_h)
            _draw_crop_marks(c, 0.0, y_bottom, strip_w, strip_h)

    finally:
        c.save()


def _draw_strip(
    c: Any, ctx: dict[str, Any], x: float, y: float, w: float, h: float
) -> None:
    """Draw card text fields onto the left (front) half of the strip."""
    # Front half: x to x + fold_x
    fold_x = x + _mm(CARD_FOLDED_WIDTH_MM)  # 249.45pt = 88mm from strip left

    # Name — bold, larger font
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 4, y + h - 12, str(ctx["name"]))

    # Level · School
    c.setFont("Helvetica", 7)
    c.drawString(x + 4, y + h - 22, f"Stufe {ctx['level']} \u00b7 {ctx['school']}")

    # Spell properties
    c.drawString(x + 4, y + h - 32, f"Zeit: {ctx['casting_time']}")
    c.drawString(x + 4, y + h - 42, f"Reichweite: {ctx['range']}")
    c.drawString(x + 4, y + h - 52, f"Komp.: {ctx['components']}")
    c.drawString(x + 4, y + h - 62, f"Dauer: {ctx['duration']}")

    # Description (first 80 chars for MVP layout)
    desc = str(ctx["description"])
    c.setFont("Helvetica", 6)
    c.drawString(x + 4, y + h - 72, desc[:80])
    if len(desc) > 80:
        c.drawString(x + 4, y + h - 80, desc[80:160])

    # Back half (right of fold): repeat name for back-face orientation
    c.setFont("Helvetica-Bold", 9)
    c.drawString(fold_x + 4, y + h - 12, str(ctx["name"]))
    c.setFont("Helvetica", 7)
    c.drawString(fold_x + 4, y + h - 22, f"Stufe {ctx['level']} \u00b7 {ctx['school']}")

    # Fold guide line (dashed, centred at 88mm)
    c.setLineWidth(0.25)
    c.setDash(3, 3)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.line(fold_x, y, fold_x, y + h)
    c.setDash()
    c.setStrokeColorRGB(0, 0, 0)


def _draw_crop_marks(
    c: Any, x: float, y: float, w: float, h: float
) -> None:
    """Draw 0.5pt crop marks at all 4 corners of the strip, offset 2mm outside."""
    c.setLineWidth(CROP_MARK_LINE_WIDTH_PT)
    c.setStrokeColorRGB(0, 0, 0)
    off = _mm(CROP_MARK_OFFSET_MM)   # 5.67pt
    lng = _mm(CROP_MARK_LENGTH_MM)   # 14.17pt

    # Bottom-left corner
    c.line(x - off - lng, y, x - off, y)        # horizontal, extends left
    c.line(x, y - off - lng, x, y - off)         # vertical, extends down

    # Bottom-right corner
    c.line(x + w + off, y, x + w + off + lng, y) # horizontal, extends right
    c.line(x + w, y - off - lng, x + w, y - off) # vertical, extends down

    # Top-left corner
    c.line(x - off - lng, y + h, x - off, y + h) # horizontal, extends left
    c.line(x, y + h + off, x, y + h + off + lng) # vertical, extends up

    # Top-right corner
    c.line(x + w + off, y + h, x + w + off + lng, y + h) # horizontal, extends right
    c.line(x + w, y + h + off, x + w, y + h + off + lng) # vertical, extends up
```

**Key notes:**
- `dest: Any` — needed because mypy can't type-narrow `Path | BytesIO` for the ReportLab call
- `c: Any` in helper functions — ReportLab canvas has no stubs; typing as `Any` avoids mypy noise
- `\u00b7` is the `·` middle dot (safe in Helvetica without custom font registration)
- `_draw_strip` draws text in the LEFT half (front face) and a brief name repeat in the RIGHT half (back face)
- `_draw_crop_marks` draws marks OUTSIDE the strip boundary (negative x is fine — expected in print margins)
- `c.setDash()` with no args resets to solid line after the fold guide

### `tests/test_composer.py` — Complete Test File

Test strategy: patch `dnd_cards.composer.render_card` to avoid template filesystem dependency. Use `BytesIO` for all output.

```python
"""Tests for composer module."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dnd_cards.composer import compose_pdf, register_fonts
from dnd_cards.models import CardData, Language


@pytest.fixture
def spell_card() -> CardData:
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
        description="A bright streak flashes from your pointing finger to a point.",
    )


def _fake_ctx(card: CardData) -> dict[str, object]:
    return {
        "id": card.id, "type": card.type, "template": card.template,
        "name": card.name, "lang": card.lang.value, "level": card.level,
        "school": card.school, "casting_time": card.casting_time,
        "range": card.range, "components": card.components,
        "duration": card.duration, "description": card.description,
        "edition": card.edition, "source_book": card.source_book,
    }


def test_register_fonts_does_not_raise() -> None:
    register_fonts()  # no .ttf files present — must not raise


def test_compose_pdf_single_card_produces_output(spell_card: CardData) -> None:
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card], buf)
    assert buf.tell() > 0, "PDF buffer should be non-empty after save()"


def test_compose_pdf_four_cards_no_error(spell_card: CardData) -> None:
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card] * 4, buf)
    assert buf.tell() > 0


def test_compose_pdf_five_cards_produces_larger_output(spell_card: CardData) -> None:
    """5 cards spans 2 pages — output should be larger than 4-card single page."""
    buf4 = BytesIO()
    buf5 = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card] * 4, buf4)
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card] * 5, buf5)
    assert buf5.tell() > buf4.tell(), "5-card PDF should be larger than 4-card PDF"


def test_compose_pdf_empty_list_no_error() -> None:
    buf = BytesIO()
    compose_pdf([], buf)
    assert buf.tell() > 0  # ReportLab still writes PDF header/trailer


def test_compose_pdf_calls_render_card_per_card(spell_card: CardData) -> None:
    buf = BytesIO()
    mock_render = MagicMock(side_effect=_fake_ctx)
    with patch("dnd_cards.composer.render_card", mock_render):
        compose_pdf([spell_card, spell_card, spell_card], buf)
    assert mock_render.call_count == 3


def test_compose_pdf_uses_card_template_name(spell_card: CardData) -> None:
    buf = BytesIO()
    mock_render = MagicMock(side_effect=_fake_ctx)
    with patch("dnd_cards.composer.render_card", mock_render):
        compose_pdf([spell_card], buf)
    mock_render.assert_called_once_with(spell_card, "zauber-v1")


def test_compose_pdf_path_output(spell_card: CardData, tmp_path: Path) -> None:
    out = tmp_path / "test.pdf"
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card], out)
    assert out.exists()
    assert out.stat().st_size > 0
```

### Architecture Constraints

- **`output_path: Path | BytesIO`** — `Path` uses `str()` wrapper at `canvas.Canvas()` call site; `BytesIO` is passed directly
- **`render_card` imported in `composer.py`** — patch as `dnd_cards.composer.render_card` in tests (not `dnd_cards.renderer.render_card`)
- **`try/finally: c.save()`** — `save()` MUST be in `finally` block to ensure PDF is finalized even on error
- **`c.showPage()` only between pages** — called when `i > 0 and page_pos == 0`; ReportLab's `save()` handles the final page
- **`_mm()` helper** — use throughout; never hard-code point values
- **All constants from `config.py`** — never hard-code `176`, `63`, `88`, `4`, etc.
- **`c: Any` type annotation** in helper functions — reportlab has no stubs; `Any` is correct here
- **Absolute imports only** — `from dnd_cards.renderer import render_card` (ruff TID252)
- **`__all__ = ["register_fonts", "compose_pdf"]`** — keep as-is; private helpers (`_mm`, `_draw_strip`, `_draw_crop_marks`) are not exported

### Regression Safeguard

All 44 existing tests must remain green. Only `composer.py`, `pyproject.toml`, and `tests/test_composer.py` are modified.

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 44 (all passing)
- **No actual font files** — `register_fonts()` will find no `.ttf` files and silently continue

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: `render_card(card, card.template)` called per card; context dict used to draw text via `_draw_strip()`
- ✅ AC2: 1 column × 4 rows per A4 page; strips stacked top-to-bottom at 178.58pt intervals
- ✅ AC3: `showPage()` called at `i > 0 and page_pos == 0`; 5-card PDF confirmed larger than 4-card PDF
- ✅ AC4: Crop marks at all 4 corners (0.5pt, 5mm long, 2mm offset); dashed grey fold-guide at 88mm centre
- ✅ AC5: `register_fonts()` uses `importlib.resources`; `str(output_path)` for Path; `.save()` in `try/finally`
- ✅ AC6: `BytesIO` accepted; `isinstance` check routes correctly; buffer non-empty after save
- ✅ Bug fixed during implementation: `_fake_ctx` test helper needed second `template_name: str` arg to match `render_card(card, template_name)` call signature
- ✅ mypy override added for `reportlab.*` in `pyproject.toml`
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 52/52 passed (8 new + 44 regressions all green)

### File List

- `pyproject.toml`
- `src/dnd_cards/composer.py`
- `tests/test_composer.py`

### Change Log

- 2026-04-12: Implemented `register_fonts()` (importlib.resources, no-op if no TTFs) and `compose_pdf()` (1×4 grid, 176×63mm strips, crop marks, fold guide, try/finally save); 8 composer tests. All ACs satisfied.

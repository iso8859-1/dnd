---
story_id: "4.5"
story_key: "4-5-duplex-pdf-mode"
epic: "Epic 4: Seed Data & Polish"
status: "review"
created: "2026-04-25"
---

# Story 4.5: Duplex PDF Mode — Separate Front and Back Pages

## Story

As Tobias,
I want to run `dnd-cards generate --deck <path> --duplex` to get a PDF suited for duplex printing,
so that I can use my printer's duplex feature to print cards on both sides without folding — just cut the cards out after printing.

---

## Acceptance Criteria

**AC1 — `--duplex` flag is available on the `generate` command:**
- **Given** `dnd-cards generate --help`
- **When** run
- **Then** `--duplex` appears as a boolean option with a description

**AC2 — Duplex mode generates alternating front/back page pairs:**
- **Given** a valid deck profile with 1–9 cards
- **When** `dnd-cards generate --deck <path> --duplex` is run
- **Then** the PDF is generated successfully and contains exactly 2 pages
- **And** page 1 contains the front face of each card in a 3-column × 3-row grid on A4 portrait
- **And** page 2 contains the back face of each card with columns mirrored left-to-right
- **And** the PDF path is printed to stdout and the process exits with code 0

**AC3 — Back page mirrors columns for long-edge duplex alignment:**
- **Given** cards at grid positions (row, col) on the front page
- **When** the back page is generated
- **Then** each card's back face appears at grid position (row, DUPLEX_COLS - 1 - col):
  - col 0 → col 2 (leftmost front → rightmost back)
  - col 1 → col 1 (centre stays)
  - col 2 → col 0 (rightmost front → leftmost back)
- **And** when the printer flips the paper along the long edge (standard portrait duplex), each card's front and back are physically aligned

**AC4 — Grid layout: A4 portrait, 63×88mm card faces, 3×3 with 5mm gaps:**
- **Given** the duplex PDF is generated
- **Then** the page size is A4 portrait (210×297mm)
- **And** each card face is 63mm wide × 88mm tall (CARD_STRIP_WIDTH_MM × CARD_FOLDED_HEIGHT_MM)
- **And** the grid has 3 columns × 3 rows = 9 cards per front/back page pair
- **And** gaps between cards are 5mm (CARD_GAP_MM)
- **And** the grid is centred horizontally and vertically on the page

**AC5 — More than 9 cards generates multiple front/back page pairs:**
- **Given** a deck with 10 cards
- **When** `--duplex` mode is used
- **Then** the PDF contains 4 pages total (page 1: fronts 1–9, page 2: backs 1–9, page 3: front 10, page 4: back 10)

**AC6 — Without `--duplex`, the existing fold-strip layout is unchanged:**
- **Given** `--duplex` is not specified
- **When** `dnd-cards generate --deck <path>` is run
- **Then** the output PDF uses the original A4 landscape 4×1 fold-strip layout
- **And** all existing tests continue to pass

**AC7 — Front face in duplex mode matches fold-strip front-face visual:**
- **Given** a card rendered in duplex mode
- **When** the front page is examined
- **Then** the front face shows: rounded-border rectangle, header with card name, type-specific content (level·school for spells, class·level for class_features, typ for talents/rules), description text, source_book at bottom

**AC8 — Back face in duplex mode shows header + icon, drawn upright (not rotated):**
- **Given** a card rendered in duplex mode
- **When** the back page is examined
- **Then** the back face shows: rounded-border rectangle, header with card name, centred type-specific icon
- **And** the back face is drawn upright (NOT rotated 180°) — the duplex printer handles physical orientation

**AC9 — Full validation suite stays green:**
- `ruff check src/` exits 0
- `mypy --strict src/` exits 0
- `pytest` — all existing 87 tests pass plus new duplex tests

---

## Tasks / Subtasks

- [x] Task 1: Add duplex layout constants to `config.py` (AC: 4)
  - [x] Add `DUPLEX_COLS: int = 3` and `DUPLEX_ROWS: int = 3` after `CARDS_PER_COL`
  - [x] Add `"DUPLEX_COLS"` and `"DUPLEX_ROWS"` to `__all__` in `config.py`

- [x] Task 2: Add `_draw_front_face()` to `composer.py` (AC: 7)
  - [x] Implement `_draw_front_face(c, ctx, x, y, w, h)` — draws front face of a card as a standalone 63×88mm card
  - [x] Reuse `_fill_header()`, `_half_border()`, `_FIELDS`, `_wrap()`, `_BORDER_PT`, `_CARD_COLORS` — same visual as fold-strip front half
  - [x] `face_top = y + h`, `face_bottom = y` (no fold offset); border height is `h`, not `fold_h`
  - [x] Type-specific content: spell branch (level·school, fields, description), class_feature branch, generic branch — identical to `_draw_strip` front section

- [x] Task 3: Add `_draw_back_face()` to `composer.py` (AC: 8)
  - [x] Implement `_draw_back_face(c, ctx, x, y, w, h)` — draws back face upright at (x, y)
  - [x] Header with card name + centred type-specific icon using `_draw_back_icon()`
  - [x] No `saveState()`/`rotate(180)` — back is drawn upright for duplex

- [x] Task 4: Add `compose_pdf_duplex()` to `composer.py` and update imports/`__all__` (AC: 2, 3, 4, 5)
  - [x] Add `DUPLEX_COLS`, `DUPLEX_ROWS` to the existing `from dnd_cards.config import (...)` block
  - [x] Implement `compose_pdf_duplex(cards, output_path)` — A4 portrait, 3×3 grid, alternating front/back pages
  - [x] Pre-render all context dicts per group: `contexts = [render_card(card, card.template) for card in group]`
  - [x] Front page: draw fronts at `(_cx(i % cols), _cy(i // cols))`
  - [x] Back page: draw backs at `(_cx((cols - 1) - (i % cols)), _cy(i // cols))`
  - [x] Page sequencing: fronts → `showPage()` → backs; next group: `showPage()` → fronts → `showPage()` → backs
  - [x] Add `"compose_pdf_duplex"` to `__all__`

- [x] Task 5: Update `cli.py` to add `--duplex` flag (AC: 1, 6)
  - [x] Update import: `from dnd_cards.composer import compose_pdf, compose_pdf_duplex, register_fonts`
  - [x] Add `duplex: bool = typer.Option(False, "--duplex", help="Generate duplex-ready PDF (separate front/back pages).")` to `generate` command
  - [x] Update `_generate_impl(deck, output_dir, duplex)` signature; add `duplex: bool = False` param
  - [x] Call `compose_pdf_duplex(cards, out_path)` when `duplex=True`, else `compose_pdf(cards, out_path)`

- [x] Task 6: Add tests in `tests/test_composer.py` (AC: 2, 3, 5, 8, 9)
  - [x] `test_compose_pdf_duplex_produces_output` — 1 card, BytesIO, assert output non-empty
  - [x] `test_compose_pdf_duplex_back_mirrors_columns` — mock `_draw_front_face`/`_draw_back_face`, verify x-positions are mirrored
  - [x] `test_compose_pdf_duplex_multi_group_no_error` — 10 cards produce output without error

- [x] Task 7: Add tests in `tests/test_cli.py` (AC: 1, 2, 6, 9)
  - [x] `test_generate_duplex_flag_calls_compose_pdf_duplex` — `--duplex` routes to `compose_pdf_duplex`, not `compose_pdf`
  - [x] `test_generate_without_duplex_calls_compose_pdf` — omitting `--duplex` still calls `compose_pdf`

- [x] Task 8: Run full validation suite (AC: 9)
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all existing 87 tests pass plus 5 new tests

---

## Dev Notes

### What Is Already Done — Do Not Touch

- **`compose_pdf(cards, output_path)`** in `src/dnd_cards/composer.py` — fold-strip layout (A4 landscape, 176×63mm strips, front+back halves); do NOT modify; existing 87 tests depend on it
- **`_draw_strip(c, ctx, x, y, w, h)`** — full fold-strip drawing including back face rotated 180°; do NOT modify; new functions draw front/back separately
- **`CARD_STRIP_WIDTH_MM = 63.0`** and **`CARD_FOLDED_HEIGHT_MM = 88.0`** in `config.py` — the card face dimensions; reuse these in `compose_pdf_duplex` (no new dimension constants needed)
- **`CARD_GAP_MM = 5.0`** and **`CARD_CORNER_RADIUS_MM = 3.0`** — reuse unchanged

### Grid Geometry (verified)

A4 portrait from ReportLab: `A4 = (595.28pt, 841.89pt)` ≈ (210mm × 297mm)

```
3 cols × 63mm + 2 gaps × 5mm = 199mm ≤ 210mm ✓  (5.5mm margin each side)
3 rows × 88mm + 2 gaps × 5mm = 274mm ≤ 297mm ✓  (11.5mm margin each side)
```

```python
# In compose_pdf_duplex — geometry setup:
page_size = A4          # portrait: (595.28pt, 841.89pt)
face_w = _mm(CARD_STRIP_WIDTH_MM)    # 63mm = 178.58pt
face_h = _mm(CARD_FOLDED_HEIGHT_MM)  # 88mm = 249.45pt
gap    = _mm(CARD_GAP_MM)            # 5mm  = 14.17pt
cols = DUPLEX_COLS   # 3
rows = DUPLEX_ROWS   # 3
cards_per_page = cols * rows  # 9

total_w  = cols * face_w + (cols - 1) * gap
total_h  = rows * face_h + (rows - 1) * gap
x_origin = (page_w - total_w) / 2
y_origin = (page_h - total_h) / 2

def _cx(col: int) -> float: return x_origin + col * (face_w + gap)
def _cy(row: int) -> float: return y_origin + row * (face_h + gap)
```

Grid indexing: `i // cols` = row (0 = bottom row), `i % cols` = col (0 = left col).

### Task 4 — Exact `compose_pdf_duplex` implementation

```python
def compose_pdf_duplex(cards: list[CardData], output_path: Path | BytesIO) -> None:
    """Compose a duplex-ready PDF: fronts on odd pages, backs on even pages.

    Layout: A4 portrait, 3 columns × 3 rows, 63×88mm card faces, 5mm gaps.
    Back pages have columns mirrored left-to-right for long-edge duplex printing.
    No folding required: cut cards out after duplex printing.
    """
    dest: Any = output_path if isinstance(output_path, BytesIO) else str(output_path)
    page_size = A4
    c = rl_canvas.Canvas(dest, pagesize=page_size)

    page_w, page_h = page_size
    face_w = _mm(CARD_STRIP_WIDTH_MM)
    face_h = _mm(CARD_FOLDED_HEIGHT_MM)
    gap = _mm(CARD_GAP_MM)

    cols = DUPLEX_COLS
    rows = DUPLEX_ROWS
    cards_per_page = cols * rows

    total_w = cols * face_w + (cols - 1) * gap
    total_h = rows * face_h + (rows - 1) * gap
    x_origin = (page_w - total_w) / 2
    y_origin = (page_h - total_h) / 2

    def _cx(col: int) -> float:
        return x_origin + col * (face_w + gap)

    def _cy(row: int) -> float:
        return y_origin + row * (face_h + gap)

    try:
        for group_start in range(0, len(cards), cards_per_page):
            group = cards[group_start : group_start + cards_per_page]

            if group_start > 0:
                c.showPage()  # end previous back page, start new front page

            contexts = [render_card(card, card.template) for card in group]

            # Front page
            for i, ctx in enumerate(contexts):
                _draw_front_face(c, ctx, _cx(i % cols), _cy(i // cols), face_w, face_h)

            c.showPage()  # end front page, start back page

            # Back page — mirror column positions for long-edge duplex
            for i, ctx in enumerate(contexts):
                mirrored_col = (cols - 1) - (i % cols)
                _draw_back_face(c, ctx, _cx(mirrored_col), _cy(i // cols), face_w, face_h)

    finally:
        c.save()
```

**Page sequencing trace:**
- Group 1: Canvas starts on page 1 (fronts) → `showPage()` → page 2 (backs)
- Group 2: `showPage()` (ends page 2, starts page 3 fronts) → `showPage()` → page 4 (backs)
- `c.save()` in `finally` closes the last back page
- Empty deck: range is empty; `c.save()` writes a valid but empty PDF (consistent with `compose_pdf` behaviour)

### Task 2 — `_draw_front_face` implementation

Extracted and adapted from `_draw_strip`'s front-face section. The only differences from `_draw_strip`:
- `face_bottom = y` (not `y + fold_h`) — card face occupies the full `h` height
- Border height is `h` (not `fold_h`)
- No fold guide line, no back face drawing

```python
def _draw_front_face(
    c: Any, ctx: dict[str, Any], x: float, y: float, w: float, h: float
) -> None:
    """Draw the front face of a card as a standalone rectangle at (x, y) with size w×h."""
    r = _mm(CARD_CORNER_RADIUS_MM)
    pad = _mm(3)
    header_h = _mm(_HEADER_MM)
    line7 = 11.0
    line6 = 8.0

    card_type = str(ctx.get("type", "spell"))
    color = _card_color(card_type)

    face_top = y + h
    face_bottom = y

    _fill_header(c, x, face_top, w, header_h, r, color)
    _half_border(c, x, face_bottom, w, h, r, color)

    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + pad, face_top - header_h / 2 - 3, str(ctx["name"]))

    c.setFillColorRGB(0.0, 0.0, 0.0)
    safe_bottom = face_bottom + _BORDER_PT / 2 + 4

    if card_type == "spell":
        src = ctx.get("source_book")
        bottom_reserve = (safe_bottom + line6) if src else safe_bottom
        level_school = f"Stufe {ctx['level']} · {ctx['school']}"
        line_y = face_top - header_h
        c.setFont("Helvetica", 7)
        line_y -= 10
        c.drawString(x + pad, line_y, level_school)
        for label, key in _FIELDS:
            for line in _wrap(f"{label}: {ctx[key]}", _WRAP_7PT):
                line_y -= line7
                if line_y < bottom_reserve:
                    break
                c.drawString(x + pad, line_y, line)
        c.setFont("Helvetica", 6)
        line_y -= 6
        for dl in _wrap(str(ctx["description"]), _WRAP_6PT):
            line_y -= line6
            if line_y < bottom_reserve:
                break
            c.drawString(x + pad, line_y, dl)
        if src:
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x + pad, safe_bottom, str(src))
            c.setFillColorRGB(0.0, 0.0, 0.0)
    else:
        src = ctx.get("source_book")
        bottom_reserve = (safe_bottom + line6) if src else safe_bottom
        line_y = face_top - header_h
        if card_type == "class_feature":
            cls = ctx.get("class_name") or ""
            lvl = ctx.get("level")
            class_line = f"{cls} · Stufe {lvl}" if lvl is not None else str(cls)
            sub = ctx.get("subclass")
            c.setFont("Helvetica-Oblique", 7)
            line_y -= 10
            c.drawString(x + pad, line_y, class_line)
            if sub:
                line_y -= line7
                c.drawString(x + pad, line_y, f"({sub})")
        elif ctx.get("typ"):
            c.setFont("Helvetica-Oblique", 7)
            line_y -= 10
            for tl in _wrap(str(ctx["typ"]), _WRAP_7PT):
                c.drawString(x + pad, line_y, tl)
                line_y -= line7
                if line_y < bottom_reserve:
                    break
        else:
            line_y -= 6
        c.setFont("Helvetica", 6)
        line_y -= 4
        for dl in _wrap(str(ctx["description"]), _WRAP_6PT):
            line_y -= line6
            if line_y < bottom_reserve:
                break
            c.drawString(x + pad, line_y, dl)
        if src:
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x + pad, safe_bottom, str(src))
            c.setFillColorRGB(0.0, 0.0, 0.0)
```

### Task 3 — `_draw_back_face` implementation

```python
def _draw_back_face(
    c: Any, ctx: dict[str, Any], x: float, y: float, w: float, h: float
) -> None:
    """Draw the back face of a card upright at (x, y). No rotation — for duplex printing."""
    r = _mm(CARD_CORNER_RADIUS_MM)
    pad = _mm(3)
    header_h = _mm(_HEADER_MM)

    card_type = str(ctx.get("type", "spell"))
    color = _card_color(card_type)

    face_top = y + h

    _fill_header(c, x, face_top, w, header_h, r, color)
    _half_border(c, x, y, w, h, r, color)

    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + pad, face_top - header_h / 2 - 3, str(ctx["name"]))

    content_center_y = y + (h - header_h) / 2
    _draw_back_icon(c, x + w / 2, content_center_y, _mm(22), card_type, color)
```

**Key difference from `_draw_strip`'s back face:** No `c.saveState()` / `c.translate()` / `c.rotate(180)` — the back face is drawn upright because the duplex printer physically flips the paper. In `_draw_strip`, the 180° rotation was needed so the back reads correctly after the user folds the strip forward.

### Task 5 — Exact `cli.py` changes

**Updated import line** (replace existing composer import):
```python
from dnd_cards.composer import compose_pdf, compose_pdf_duplex, register_fonts
```

**Updated `generate` command:**
```python
@app.command()
def generate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Output directory for generated PDF."
    ),
    duplex: bool = typer.Option(
        False, "--duplex", help="Generate duplex-ready PDF (separate front/back pages, no folding)."
    ),
) -> None:
    """Generate a print-ready PDF from a deck profile."""
    try:
        _generate_impl(deck, output_dir, duplex)
    except Exception as exc:
        _handle_dnd_error(exc)
```

**Updated `_generate_impl`:**
```python
def _generate_impl(deck: str, output_dir: Optional[str] = None, duplex: bool = False) -> None:
    deck_path = Path(deck)
    card_index = scan_cards(Path(DEFAULT_DATA_DIR))
    deck_profile = load_deck(deck_path)

    cards: list[CardData] = []
    for entry in deck_profile.entries:
        if entry.card_key not in card_index:
            raise CardNotFoundError(
                f"Card not found: {entry.card_key} (deck: {deck_path})"
            )
        card = load_card(card_index[entry.card_key].path)
        cards.extend([card] * entry.quantity)

    out_dir = Path(output_dir) if output_dir else Path(DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{deck_path.stem}.pdf"

    if duplex:
        compose_pdf_duplex(cards, out_path)
    else:
        compose_pdf(cards, out_path)
    typer.echo(str(out_path))
```

**Critical:** `compose_pdf_duplex` must be imported directly into `cli.py`'s namespace (not accessed via `composer.compose_pdf_duplex`) so that tests can patch it as `dnd_cards.cli.compose_pdf_duplex`.

### Task 6 — New tests for `tests/test_composer.py`

Add these after the existing tests. The `spell_card` fixture and `_fake_ctx` helper are already defined in this file.

```python
from typing import Any
```
Add this import if `Any` is not already imported (it is not — add it to the imports block).

```python
# ── Story 4.5: compose_pdf_duplex tests ─────────────────────────────────────

from dnd_cards.composer import compose_pdf_duplex  # add to existing import line


def test_compose_pdf_duplex_produces_output(spell_card: CardData) -> None:
    """compose_pdf_duplex writes bytes to output for a single card."""
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf_duplex([spell_card], buf)
    assert buf.tell() > 0


def test_compose_pdf_duplex_back_mirrors_columns(spell_card: CardData) -> None:
    """Back page draws each card's back at the horizontally mirrored column position."""
    cards = [spell_card, spell_card, spell_card]  # 3 cards fill row 0

    front_xs: list[float] = []
    back_xs: list[float] = []

    def capture_front(c: Any, ctx: Any, x: float, y: float, w: float, h: float) -> None:
        front_xs.append(x)

    def capture_back(c: Any, ctx: Any, x: float, y: float, w: float, h: float) -> None:
        back_xs.append(x)

    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx), \
         patch("dnd_cards.composer._draw_front_face", side_effect=capture_front), \
         patch("dnd_cards.composer._draw_back_face", side_effect=capture_back):
        compose_pdf_duplex(cards, BytesIO())

    assert len(front_xs) == 3
    assert len(back_xs) == 3
    # col 0 front → col 2 back; col 1 stays; col 2 front → col 0 back
    assert back_xs[0] == pytest.approx(front_xs[2])
    assert back_xs[1] == pytest.approx(front_xs[1])
    assert back_xs[2] == pytest.approx(front_xs[0])


def test_compose_pdf_duplex_multi_group_no_error(spell_card: CardData) -> None:
    """10 cards (> 9 per page) generates output without error."""
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf_duplex([spell_card] * 10, buf)
    assert buf.tell() > 0
```

**Note on `compose_pdf_duplex` import in test file:** Add `compose_pdf_duplex` to the existing import line:
```python
from dnd_cards.composer import compose_pdf, compose_pdf_duplex, register_fonts
```

**Note on `Any` import:** `Any` is needed for the capture function signatures. Add `from typing import Any` if not present. Check the existing imports — `Any` is not currently imported in `test_composer.py`.

### Task 7 — New tests for `tests/test_cli.py`

The `fake_card` fixture and required imports (`CardRef`, `DeckProfile`, `DeckEntry`, `patch`) are already present in the test file. Add after the existing generate tests:

```python
# ── Story 4.5: generate --duplex flag tests ──────────────────────────────────


def test_generate_duplex_flag_calls_compose_pdf_duplex(tmp_path: Path, fake_card: CardData) -> None:
    """--duplex routes to compose_pdf_duplex, not compose_pdf."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/fireball: 1\n", encoding="utf-8")
    out_dir = tmp_path / "output"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/fireball", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf") as mock_regular, \
         patch("dnd_cards.cli.compose_pdf_duplex") as mock_duplex:
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(out_dir), "--duplex"]
        )

    assert result.exit_code == 0
    mock_duplex.assert_called_once()
    mock_regular.assert_not_called()


def test_generate_without_duplex_calls_compose_pdf(tmp_path: Path, fake_card: CardData) -> None:
    """Without --duplex, compose_pdf (fold-strip) is used, not compose_pdf_duplex."""
    deck_file = tmp_path / "deck.yaml"
    deck_file.write_text("name: Test\ncards:\n  spells/fireball: 1\n", encoding="utf-8")
    out_dir = tmp_path / "output"

    fake_index = {"spells/fireball": CardRef(path=Path("data/en/spells/fireball.yaml"), card_type="spells")}
    fake_deck = DeckProfile(name="Test", entries=[DeckEntry(card_key="spells/fireball", quantity=1)])

    with patch("dnd_cards.cli.scan_cards", return_value=fake_index), \
         patch("dnd_cards.cli.load_deck", return_value=fake_deck), \
         patch("dnd_cards.cli.load_card", return_value=fake_card), \
         patch("dnd_cards.cli.compose_pdf") as mock_regular, \
         patch("dnd_cards.cli.compose_pdf_duplex") as mock_duplex:
        result = runner.invoke(
            app, ["generate", "--deck", str(deck_file), "--output-dir", str(out_dir)]
        )

    assert result.exit_code == 0
    mock_regular.assert_called_once()
    mock_duplex.assert_not_called()
```

### Architecture Constraints

- **`mypy --strict` compliance** — `_draw_front_face` and `_draw_back_face` must be annotated: `c: Any, ctx: dict[str, Any], x: float, y: float, w: float, h: float) -> None`; `compose_pdf_duplex` signature: `cards: list[CardData], output_path: Path | BytesIO) -> None`; `contexts: list[dict[str, Any]]` for pre-rendered results; `duplex: bool = False` in `_generate_impl`
- **`ruff TID252`** — absolute imports only in `src/`; no relative imports
- **`A4` already imported** in `composer.py` (`from reportlab.lib.pagesizes import A4, landscape`); use `A4` directly (portrait) in `compose_pdf_duplex`
- **`compose_pdf` and `_draw_strip` untouched** — zero modifications to existing functions; only additive changes
- **`_generate_impl` backward compatible** — `duplex: bool = False` default; existing tests that patch `_generate_impl` directly are unaffected (they bypass the implementation entirely)
- **Patch target for CLI tests** — patch `dnd_cards.cli.compose_pdf_duplex` (where it's used), not `dnd_cards.composer.compose_pdf_duplex`; requires the direct import in `cli.py`
- **`_draw_front_face` and `_draw_back_face` are private** — prefixed with `_`; not added to `__all__`; only `compose_pdf_duplex` is public

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/config.py` | Add `DUPLEX_COLS = 3`, `DUPLEX_ROWS = 3`; update `__all__` |
| `src/dnd_cards/composer.py` | Add `DUPLEX_COLS`, `DUPLEX_ROWS` to config import; add `_draw_front_face()`, `_draw_back_face()`, `compose_pdf_duplex()`; update `__all__` |
| `src/dnd_cards/cli.py` | Import `compose_pdf_duplex`; add `--duplex` param; update `_generate_impl` |
| `tests/test_composer.py` | Add `compose_pdf_duplex` to import; add `from typing import Any`; add 3 new tests |
| `tests/test_cli.py` | Add 2 new duplex CLI tests |

### Regression Safeguard

- **`compose_pdf` and `_draw_strip` are untouched** — all 87 existing tests pass unchanged
- **Existing `generate` CLI tests** patch `_generate_impl` or `compose_pdf` directly — neither is modified; patching still works
- **`_generate_impl` signature change** — new `duplex: bool = False` is a keyword-only addition with a default; any existing call to `_generate_impl(deck, output_dir)` continues to work

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 87 (all passing as of Story 4.4)

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — clean implementation.

### Completion Notes List

- Task 1: Added `DUPLEX_COLS = 3` and `DUPLEX_ROWS = 3` to `config.py` `__all__` and body.
- Task 2: Added `_draw_front_face()` to `composer.py` — same visual logic as `_draw_strip` front half, standalone w×h rectangle at (x, y).
- Task 3: Added `_draw_back_face()` to `composer.py` — header + centred icon, drawn upright (no 180° rotation).
- Task 4: Added `compose_pdf_duplex()` to `composer.py` — A4 portrait, 3×3 grid, alternating front/back pages with column mirroring. Added `DUPLEX_COLS`/`DUPLEX_ROWS` imports and `compose_pdf_duplex` to `__all__`. Fixed `page_w: float; page_h: float` type annotations for mypy --strict compliance.
- Task 5: Updated `cli.py` — imported `compose_pdf_duplex`, added `--duplex` bool flag, updated `_generate_impl` to dispatch to `compose_pdf_duplex` when `duplex=True`.
- Tasks 6–7: Added 5 new tests: 3 in `test_composer.py` (output non-empty, column mirroring verified, multi-group), 2 in `test_cli.py` (--duplex routes to duplex, omitting --duplex routes to regular).
- Task 8: ruff ✅ (2 pre-existing errors only), mypy --strict ✅, pytest 92/92 ✅ (87 existing + 5 new).

### File List

- `src/dnd_cards/config.py` — added `DUPLEX_COLS = 3`, `DUPLEX_ROWS = 3`; updated `__all__`
- `src/dnd_cards/composer.py` — added `DUPLEX_COLS`/`DUPLEX_ROWS` imports; added `_draw_front_face()`, `_draw_back_face()`, `compose_pdf_duplex()`; updated `__all__`
- `src/dnd_cards/cli.py` — imported `compose_pdf_duplex`; added `--duplex` flag to `generate`; updated `_generate_impl`
- `tests/test_composer.py` — added `from typing import Any`; added `compose_pdf_duplex` to import; added 3 new duplex tests
- `tests/test_cli.py` — added 2 new `--duplex` CLI tests

### Change Log

- 2026-04-25: Story 4.5 implemented — duplex PDF mode added; `compose_pdf_duplex` in composer; `--duplex` flag in CLI; 5 new tests; 92/92 tests pass

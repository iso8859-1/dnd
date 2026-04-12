---
story_id: "4.3"
story_key: "4-3-talent-and-rule-card-type"
epic: "Epic 4: Seed Data & Polish"
status: "review"
created: "2026-04-12"
---

# Story 4.3: Talent and Rule Card Type — Data Import & New Template

## Story

As Tobias,
I want talent and rule entries from the SRD imported as individual card YAML files and rendered
with their own grey-bordered, distinct-icon template,
so that I can include talents and rules in decks alongside spells and print them with matching visual quality.

---

## Acceptance Criteria

**AC1 — Import script splits bulk YAML into individual card files:**
- **Given** the 5 source files in `SRDs/` (allgemeine_talente.yaml, epische_gabe_talente.yaml,
  herkunftstalente.yaml, kampfstiltalente.yaml, regelglossar.yaml)
- **When** `uv run python scripts/import_srd_data.py` is run from the project root
- **Then** 17 talent YAML files are written to `data/de/SRD 5.2/talents/`
- **And** 155 rule YAML files are written to `data/de/SRD 5.2/rules/`
- **And** each file is named `{slug}.yaml` where slug = lowercased name with umlauts transliterated
  and spaces/special chars replaced by hyphens
- **And** the script is idempotent (re-running overwrites without error)

**AC2 — Individual card YAML format is correct:**
- **Given** a talent entry with `name`, `typ`, `beschreibung`, `Regelbuch` in the source
- **Then** its output YAML contains:
  ```yaml
  id: <slug>
  type: talent
  template: talent-v1
  name: <original German name>
  lang: de
  typ: <typ string, omitted for rules>
  description: <beschreibung>
  source_book: <Regelbuch>
  ```
- **And** rule entries use `type: rule`, `template: rule-v1`, no `typ` field

**AC3 — CardData model accepts talent and rule cards:**
- **Given** a talent YAML that omits `level`, `school`, `casting_time`, `range`, `components`, `duration`
- **When** `load_card()` parses it
- **Then** the resulting `CardData` object has those fields as `None`
- **And** a spell YAML that provides all those fields continues to load correctly

**AC4 — Renderer produces correct context for talent/rule cards:**
- **Given** a talent `CardData` with `typ` set and spell fields `None`
- **When** `render_card(card, "talent-v1")` is called
- **Then** the context dict contains `typ` with the talent category string
- **And** spell-specific keys (`level`, `school`, etc.) are present but `None`

**AC5 — Talent and rule cards render with grey border and matching icon:**
- **Given** a `CardData` with `type = "talent"` or `type = "rule"`
- **When** `compose_pdf([card], output_path)` is called
- **Then** the front face uses a pastel grey header (not violet)
- **And** the back face displays a shield icon (talent) or scroll icon (rule) instead of the spellbook
- **And** the front face shows: name in header, `typ` if present, description (word-wrapped),
  `source_book` at the bottom — no Zeit/Reichweite/Komp./Dauer rows

**AC6 — Existing spell rendering is unchanged:**
- **Given** any existing spell card deck
- **When** `compose_pdf` runs
- **Then** output is identical to pre-story behaviour (violet header, spellbook icon, all spell fields shown)

**AC7 — Full validation suite stays green:**
- `ruff check src/` exits 0
- `mypy --strict src/` exits 0
- `pytest` — all tests pass (56 existing + new tests)

---

## Tasks / Subtasks

- [x] Task 1: Make spell-specific `CardData` fields optional; add `typ` field (AC: 3)
  - [x] Change `level`, `school`, `casting_time`, `range`, `components`, `duration` to `Optional[X] = None`
  - [x] Add `typ: Optional[str] = None`
  - [x] Update `test_load_card_missing_required_field` to test `description` absence, not `level`
- [x] Task 2: Update renderer to include `typ` in context (AC: 4)
  - [x] Add `"typ": card.typ` to the context dict in `render_card`
- [x] Task 3: Create template files (AC: 4, 5)
  - [x] Create `templates/talent-v1.jinja2`
  - [x] Create `templates/rule-v1.jinja2`
- [x] Task 4: Update composer for type-specific colour, icon, and front-face layout (AC: 5, 6)
  - [x] Replace module-level `_VIOLET` constant with `_CARD_COLORS` dict + `_card_color()` helper
  - [x] Propagate colour parameter through `_fill_header`, `_half_border`, `_draw_sparkle`, `_draw_spellbook_icon`
  - [x] Add `_draw_shield_icon()` for talent back face
  - [x] Add `_draw_scroll_icon()` for rule back face
  - [x] Add `_draw_back_icon()` dispatcher; call from `_draw_strip`
  - [x] Add type-specific front-face branch in `_draw_strip`: spell path (existing) vs. generic path (typ + description + source_book)
- [x] Task 5: Write import script `scripts/import_srd_data.py` (AC: 1, 2)
  - [x] `slugify(name)` helper: transliterate umlauts, lowercase, spaces→hyphens, strip specials
  - [x] `import_talents(source_file, out_dir)` — reads `talente:` list, writes individual YAMLs
  - [x] `import_rules(source_file, out_dir)` — reads `regelglossar:` list, writes individual YAMLs
  - [x] Main block: call import for all 5 source files; create output dirs
- [x] Task 6: Run import script to populate data (AC: 1, 2)
  - [x] `uv run python scripts/import_srd_data.py`
  - [x] Verify file count: 17 in `data/de/SRD 5.2/talents/`, 155 in `data/de/SRD 5.2/rules/`
- [x] Task 7: Add tests (AC: 3, 4, 5, 7)
  - [x] `test_models.py`: `test_card_data_talent_minimal` — CardData with only required fields
  - [x] `test_renderer.py`: `test_render_card_talent_context` — context has `typ`, spell fields are `None`
  - [x] `test_composer.py`: `test_compose_pdf_talent_card_no_error` — talent card renders without error
- [x] Task 8: Run full validation suite (AC: 7)
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass

---

## Dev Notes

### Source Data

All 5 source files live in `SRDs/` (project root). Do NOT modify them.

| Source file | List key | card type | template | Count |
|---|---|---|---|---|
| `allgemeine_talente.yaml` | `talente` | `talent` | `talent-v1` | 2 |
| `herkunftstalente.yaml` | `talente` | `talent` | `talent-v1` | 4 |
| `kampfstiltalente.yaml` | `talente` | `talent` | `talent-v1` | 4 |
| `epische_gabe_talente.yaml` | `talente` | `talent` | `talent-v1` | 7 |
| `regelglossar.yaml` | `regelglossar` | `rule` | `rule-v1` | 155 |

**Source YAML field mapping:**

| Source field | CardData field | Notes |
|---|---|---|
| `name` | `name`, `id` (slugified) | same value, different forms |
| `typ` | `typ` | talent only; absent in regelglossar |
| `beschreibung` | `description` | |
| `Regelbuch` | `source_book` | capital R in source |

### Task 1 — Exact `models.py` changes

Replace required spell fields with Optional in `CardData`:

```python
class CardData(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    type: str
    template: str
    name: str
    lang: Language
    # Spell-specific — None for talent/rule cards
    level: Optional[int] = None
    school: Optional[str] = None
    casting_time: Optional[str] = None
    range: Optional[str] = None
    components: Optional[str] = None
    duration: Optional[str] = None
    # Shared optional fields
    typ: Optional[str] = None          # talent category string
    description: str                   # required for all types
    edition: Optional[str] = None
    source_book: Optional[str] = None
```

**Regression fix — `tests/test_loader.py` line 30–43:**
`test_load_card_missing_required_field` currently tests that a missing `level` raises `ValidationError`.
After this change `level` is optional, so the test will fail. Update it to test a missing `description`
(which remains required for all types):

```python
def test_load_card_missing_required_field(tmp_path: Path) -> None:
    # `description` is required for every card type
    missing_desc = tmp_path / "no_description.yaml"
    missing_desc.write_text(
        "id: x\ntype: talent\ntemplate: talent-v1\nname: X\nlang: de\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError) as exc_info:
        load_card(missing_desc)
    err = str(exc_info.value)
    assert "description" in err
    assert str(missing_desc) in err
```

Also update `test_load_card_invalid_lang_value` — it currently provides all spell fields in the inline
YAML. Those lines can stay as-is; extra optional fields are accepted by Pydantic. No change needed.

### Task 2 — Renderer change

In `src/dnd_cards/renderer.py`, add `"typ": card.typ` to the context dict:

```python
context: dict[str, Any] = {
    "id": card.id,
    "type": card.type,
    "template": card.template,
    "name": card.name,
    "lang": card.lang.value,
    "level": card.level,
    "school": card.school,
    "casting_time": card.casting_time,
    "range": card.range,
    "components": card.components,
    "duration": card.duration,
    "typ": card.typ,               # ← add this line
    "description": card.description,
    "edition": card.edition,
    "source_book": card.source_book,
}
```

### Task 3 — Template files

Both templates are validation markers in this system (the renderer checks the template exists, then
returns a Python dict — it does not render the template to HTML/text). Minimal content is fine:

**`templates/talent-v1.jinja2`:**
```jinja2
{{ name }}
{% if typ %}{{ typ }}{% endif %}
{{ description }}
{% if source_book %}Quelle: {{ source_book }}{% endif %}
```

**`templates/rule-v1.jinja2`:**
```jinja2
{{ name }}
{{ description }}
{% if source_book %}Quelle: {{ source_book }}{% endif %}
```

### Task 4 — Composer changes (detailed)

**4a — Replace `_VIOLET` with a colour lookup**

Remove:
```python
_VIOLET: tuple[float, float, float] = (0.75, 0.62, 0.85)
```

Add:
```python
_CARD_COLORS: dict[str, tuple[float, float, float]] = {
    "spell":  (0.75, 0.62, 0.85),  # pastel violet
    "talent": (0.62, 0.62, 0.65),  # pastel grey
    "rule":   (0.62, 0.62, 0.65),  # pastel grey
}
_DEFAULT_COLOR: tuple[float, float, float] = (0.62, 0.62, 0.65)


def _card_color(card_type: str) -> tuple[float, float, float]:
    return _CARD_COLORS.get(card_type, _DEFAULT_COLOR)
```

**4b — Add colour parameter to drawing helpers**

Update `_fill_header`, `_half_border`, `_draw_sparkle`, and `_draw_spellbook_icon` to accept
`color: tuple[float, float, float]` instead of reading `_VIOLET` directly.

`_fill_header` signature change:
```python
def _fill_header(
    c: Any, x: float, y_top: float, w: float, h: float, r: float,
    color: tuple[float, float, float],
) -> None:
    rv, gv, bv = color
    ...
```

Same pattern for `_half_border`, `_draw_sparkle`, `_draw_spellbook_icon`.

**4c — New back-face icons**

Add `_draw_shield_icon` (for talents) and `_draw_scroll_icon` (for rules). Keep them simple vector
shapes in the same style as `_draw_spellbook_icon`. Then add a dispatcher:

```python
def _draw_back_icon(
    c: Any, cx: float, cy: float, size: float,
    card_type: str, color: tuple[float, float, float],
) -> None:
    if card_type == "spell":
        _draw_spellbook_icon(c, cx, cy, size, color)
    elif card_type == "talent":
        _draw_shield_icon(c, cx, cy, size, color)
    else:
        _draw_scroll_icon(c, cx, cy, size, color)
```

**Suggested `_draw_shield_icon`** — a pointed shield with a cross-sword motif:
```python
def _draw_shield_icon(c: Any, cx: float, cy: float, size: float,
                      color: tuple[float, float, float]) -> None:
    rv, gv, bv = color
    dv = rv * 0.72, gv * 0.72, bv * 0.72
    sw = size * 0.70
    sh = size * 0.85
    sx = cx - sw / 2
    sy = cy - sh / 2

    # Shield body: top rectangle + bottom triangle pointing down
    p = c.beginPath()
    p.moveTo(sx, sy + sh * 0.55)            # bottom-left of rect portion
    p.lineTo(sx, sy + sh)                   # top-left
    p.lineTo(sx + sw, sy + sh)              # top-right
    p.lineTo(sx + sw, sy + sh * 0.55)       # bottom-right of rect portion
    p.lineTo(cx, sy)                        # bottom point
    p.close()
    c.setFillColorRGB(rv, gv, bv)
    c.setStrokeColorRGB(*dv)
    c.setLineWidth(1.2)
    c.drawPath(p, stroke=1, fill=1)

    # Cross symbol (white lines)
    c.setStrokeColorRGB(1.0, 1.0, 1.0)
    c.setLineWidth(1.5)
    mid_y = sy + sh * 0.72
    c.line(cx, sy + sh * 0.48, cx, sy + sh * 0.96)        # vertical
    c.line(sx + sw * 0.22, mid_y, sx + sw * 0.78, mid_y)  # horizontal

    _draw_sparkle(c, cx, sy - size * 0.18, size * 0.14, color)
```

**Suggested `_draw_scroll_icon`** — a rolled scroll with text lines:
```python
def _draw_scroll_icon(c: Any, cx: float, cy: float, size: float,
                      color: tuple[float, float, float]) -> None:
    rv, gv, bv = color
    dv = rv * 0.72, gv * 0.72, bv * 0.72
    rw = size * 0.68
    rh = size * 0.80
    roll = size * 0.10   # rolled-end height
    rx = cx - rw / 2
    ry = cy - rh / 2

    # Scroll body fill
    c.setFillColorRGB(rv, gv, bv)
    c.rect(rx, ry + roll, rw, rh - 2 * roll, stroke=0, fill=1)

    # Rolled ends (ellipses approximated with filled rects)
    c.roundRect(rx, ry + rh - roll * 2, rw, roll * 2, roll * 0.8,
                stroke=0, fill=1)
    c.roundRect(rx, ry, rw, roll * 2, roll * 0.8, stroke=0, fill=1)

    # Outline
    c.setLineWidth(1.2)
    c.setStrokeColorRGB(*dv)
    c.roundRect(rx, ry, rw, rh, roll * 0.5, stroke=1, fill=0)

    # Text lines (white)
    c.setStrokeColorRGB(1.0, 1.0, 1.0)
    c.setLineWidth(0.8)
    lx0 = rx + rw * 0.12
    lx1 = rx + rw * 0.88
    for frac in (0.35, 0.52, 0.69):
        py = ry + rh * frac
        c.line(lx0, py, lx1, py)

    _draw_sparkle(c, cx, ry - size * 0.18, size * 0.14, color)
```

**4d — `_draw_strip` front-face branch**

In `_draw_strip`, resolve the colour once and add a type-specific front-face content branch:

```python
def _draw_strip(
    c: Any, ctx: dict[str, Any], x: float, y: float, w: float, h: float
) -> None:
    fold_h = _mm(CARD_FOLDED_HEIGHT_MM)
    r = _mm(CARD_CORNER_RADIUS_MM)
    pad = _mm(3)
    header_h = _mm(_HEADER_MM)
    line7 = 11.0
    line6 = 8.0

    card_type = str(ctx.get("type", "spell"))
    color = _card_color(card_type)
    level_school = f"Stufe {ctx['level']} \u00b7 {ctx['school']}"  # spell only

    front_top = y + h
    front_bottom = y + fold_h

    _fill_header(c, x, front_top, w, header_h, r, color)
    _half_border(c, x, front_bottom, w, fold_h, r, color)

    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + pad, front_top - header_h / 2 - 3, str(ctx["name"]))

    c.setFillColorRGB(0.0, 0.0, 0.0)

    if card_type == "spell":
        # ── Spell front face (existing layout) ──────────────────────────────
        line_y = front_top - header_h
        c.setFont("Helvetica", 7)
        line_y -= 10
        c.drawString(x + pad, line_y, level_school)
        for label, key in _FIELDS:
            for line in _wrap(f"{label}: {ctx[key]}", _WRAP_7PT):
                line_y -= line7
                if line_y < front_bottom + 4:
                    break
                c.drawString(x + pad, line_y, line)
        c.setFont("Helvetica", 6)
        line_y -= 6
        for dl in _wrap(str(ctx["description"]), _WRAP_6PT):
            line_y -= line6
            if line_y < front_bottom + 4:
                break
            c.drawString(x + pad, line_y, dl)
    else:
        # ── Generic front face (talent / rule) ───────────────────────────────
        # typ (category), then description filling most of the space,
        # then source_book at the bottom.
        line_y = front_top - header_h
        if ctx.get("typ"):
            c.setFont("Helvetica-Oblique", 7)
            line_y -= 10
            for tl in _wrap(str(ctx["typ"]), _WRAP_7PT):
                c.drawString(x + pad, line_y, tl)
                line_y -= line7
                if line_y < front_bottom + 4:
                    break
        else:
            line_y -= 6

        c.setFont("Helvetica", 6)
        line_y -= 4
        src = ctx.get("source_book")
        # Reserve space for source_book line at bottom
        bottom_reserve = (front_bottom + 4 + line6 + 4) if src else (front_bottom + 4)
        for dl in _wrap(str(ctx["description"]), _WRAP_6PT):
            line_y -= line6
            if line_y < bottom_reserve:
                break
            c.drawString(x + pad, line_y, dl)

        if src:
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x + pad, front_bottom + 6, str(src))
            c.setFillColorRGB(0.0, 0.0, 0.0)

    # ── Fold guide ─────────────────────────────────────────────────────────────
    c.setLineWidth(0.25)
    c.setDash(3, 3)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.line(x, y + fold_h, x + w, y + fold_h)
    c.setDash()
    c.setStrokeColorRGB(0.0, 0.0, 0.0)

    # ── Back face ──────────────────────────────────────────────────────────────
    c.saveState()
    c.translate(x + w, y + fold_h)
    c.rotate(180)

    _fill_header(c, 0.0, fold_h, w, header_h, r, color)
    _half_border(c, 0.0, 0.0, w, fold_h, r, color)

    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(pad, fold_h - header_h / 2 - 3, str(ctx["name"]))

    _draw_back_icon(c, w / 2, (fold_h - header_h) / 2, _mm(22), card_type, color)

    c.restoreState()
```

### Task 5 — Import script `scripts/import_srd_data.py`

Create the `scripts/` directory. The script uses only stdlib (`re`, `pathlib`) and `PyYAML`
(already a project dependency). No `uv add` needed.

```python
#!/usr/bin/env python
"""One-time import: split bulk SRD YAML files into individual card YAML files.

Usage (from project root):
    uv run python scripts/import_srd_data.py
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SRD_DIR = Path("SRDs")
DATA_BASE = Path("data") / "de" / "SRD 5.2"

_UMLAUT: dict[str, str] = {
    "ä": "a", "ö": "o", "ü": "u",
    "Ä": "a", "Ö": "o", "Ü": "u",
    "ß": "ss",
}
_UMLAUT_TABLE = str.maketrans(_UMLAUT)


def slugify(name: str) -> str:
    """Lowercase slug: transliterate German umlauts, spaces→hyphens, strip specials."""
    s = name.translate(_UMLAUT_TABLE).lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return re.sub(r"-+", "-", s).strip("-")


def _write_card(out_dir: Path, card: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{card['id']}.yaml"
    with out_path.open("w", encoding="utf-8") as fh:
        yaml.dump(card, fh, allow_unicode=True, default_flow_style=False,
                  sort_keys=False)
    print(f"  {out_path}")


def import_talents(source: Path, out_dir: Path) -> int:
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    count = 0
    for entry in data["talente"]:
        card: dict[str, Any] = {
            "id": slugify(entry["name"]),
            "type": "talent",
            "template": "talent-v1",
            "name": entry["name"],
            "lang": "de",
            "description": entry["beschreibung"],
            "source_book": entry.get("Regelbuch"),
        }
        if entry.get("typ"):
            card["typ"] = entry["typ"]
        _write_card(out_dir, card)
        count += 1
    return count


def import_rules(source: Path, out_dir: Path) -> int:
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    count = 0
    for entry in data["regelglossar"]:
        card = {
            "id": slugify(entry["name"]),
            "type": "rule",
            "template": "rule-v1",
            "name": entry["name"],
            "lang": "de",
            "description": entry["beschreibung"],
            "source_book": entry.get("Regelbuch"),
        }
        _write_card(out_dir, card)
        count += 1
    return count


if __name__ == "__main__":
    talents_dir = DATA_BASE / "talents"
    rules_dir = DATA_BASE / "rules"
    total = 0

    for fname in (
        "allgemeine_talente.yaml",
        "herkunftstalente.yaml",
        "kampfstiltalente.yaml",
        "epische_gabe_talente.yaml",
    ):
        print(f"Importing {fname}…")
        total += import_talents(SRD_DIR / fname, talents_dir)

    print("Importing regelglossar.yaml…")
    total += import_rules(SRD_DIR / "regelglossar.yaml", rules_dir)

    print(f"\nDone — {total} files written.")
```

**Expected output directories after running:**
```
data/de/SRD 5.2/
  spells/   (339 existing files)
  talents/  (17 new files)
  rules/    (155 new files)
```

### Task 7 — New tests

**`tests/test_models.py` — add:**
```python
def test_card_data_talent_minimal() -> None:
    """Talent card with only non-spell required fields."""
    card = CardData(
        id="ringer",
        type="talent",
        template="talent-v1",
        name="Ringer",
        lang=Language.DE,
        description="Du erhältst folgende Vorzüge.",
        typ="Allgemeines Talent",
        source_book="SRD 5.2.1",
    )
    assert card.level is None
    assert card.school is None
    assert card.casting_time is None
    assert card.range is None
    assert card.components is None
    assert card.duration is None
    assert card.typ == "Allgemeines Talent"
```

**`tests/test_renderer.py` — add:**
```python
def test_render_card_talent_context(tmp_path: Path) -> None:
    """render_card for a talent card includes typ; spell fields are None."""
    (tmp_path / "talent-v1.jinja2").write_text(
        "{{ name }}\n{{ description }}\n", encoding="utf-8"
    )
    card = CardData(
        id="ringer",
        type="talent",
        template="talent-v1",
        name="Ringer",
        lang=Language.DE,
        description="Vorzüge.",
        typ="Allgemeines Talent",
    )
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        ctx = render_card(card, "talent-v1")

    assert ctx["typ"] == "Allgemeines Talent"
    assert ctx["level"] is None
    assert ctx["school"] is None
    assert ctx["casting_time"] is None
    assert ctx["range"] is None
    assert ctx["components"] is None
    assert ctx["duration"] is None
```

**`tests/test_composer.py` — add:**
```python
def test_compose_pdf_talent_card_no_error(tmp_path: Path) -> None:
    """Talent card (no spell fields) renders without error."""
    talent = CardData(
        id="ringer",
        type="talent",
        template="talent-v1",
        name="Ringer",
        lang=Language.DE,
        description="Du erhältst folgende Vorzüge.",
        typ="Allgemeines Talent",
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([talent], buf)
    assert buf.tell() > 0


def test_compose_pdf_rule_card_no_error(tmp_path: Path) -> None:
    """Rule card renders without error."""
    rule = CardData(
        id="abenteuer",
        type="rule",
        template="rule-v1",
        name="Abenteuer",
        lang=Language.DE,
        description="Ein Abenteuer ist eine Serie von Begegnungen.",
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([rule], buf)
    assert buf.tell() > 0
```

Note: `_fake_ctx` in `test_composer.py` already handles `CardData` with any fields — it reads from
`card.*` attributes. After making spell fields optional, `_fake_ctx` will return `None` for those keys,
which is fine since the composer uses `ctx.get("typ")` etc. with guards.

**Update `_fake_ctx` in `test_composer.py`** to also include `typ` and `source_book` in the returned dict:

```python
def _fake_ctx(card: CardData, template_name: str) -> dict[str, object]:  # noqa: ARG001
    return {
        "id": card.id,
        "type": card.type,
        "template": card.template,
        "name": card.name,
        "lang": card.lang.value,
        "level": card.level,
        "school": card.school,
        "casting_time": card.casting_time,
        "range": card.range,
        "components": card.components,
        "duration": card.duration,
        "typ": card.typ,
        "description": card.description,
        "edition": card.edition,
        "source_book": card.source_book,
    }
```

### Architecture Constraints

- **`mypy --strict`** — all new functions need full type annotations including the colour parameter
  `tuple[float, float, float]`
- **ruff TID252** — no relative imports; use `from dnd_cards.X import ...` in src
- **Script is not part of the package** — `scripts/import_srd_data.py` lives at project root level,
  not in `src/`; it uses `import yaml` directly (PyYAML is already a dependency via `pyproject.toml`)
- **`level_school` string in `_draw_strip`** — only computed in the spell branch; the variable is
  used only in that branch. Do not compute it unconditionally (would crash on `None` values)
- **Pydantic field order** — `description: str` must appear AFTER the new optional spell fields so
  that mypy infers field ordering correctly; place it between `duration` and `edition`
- **Scanner unchanged** — `card_type = yaml_file.parent.name`; talents → `talents/{slug}`,
  rules → `rules/{slug}`. Deck YAML keys would be `talents/ringer: 1` etc.

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/models.py` | Make 6 fields Optional; add `typ` |
| `src/dnd_cards/renderer.py` | Add `"typ": card.typ` to context dict |
| `src/dnd_cards/composer.py` | Colour table, colour param propagation, 2 new icons, front-face branch |
| `templates/talent-v1.jinja2` | New file |
| `templates/rule-v1.jinja2` | New file |
| `scripts/import_srd_data.py` | New file (one-time import utility) |
| `tests/test_loader.py` | Update `test_load_card_missing_required_field` (line 30) |
| `tests/test_models.py` | Add `test_card_data_talent_minimal` |
| `tests/test_renderer.py` | Add `test_render_card_talent_context` |
| `tests/test_composer.py` | Update `_fake_ctx` + add 2 new tests |

### Regression Safeguard

- **56 existing tests must stay green** — spell fields become Optional but spell YAML files still
  provide them, so all existing spell-related tests are unaffected
- **`test_load_card_missing_required_field`** — MUST be updated (see Task 1); it will fail if not
- **`_fake_ctx` update** — required so that `_draw_strip`'s generic branch does not crash when
  `ctx.get("typ")` is called on the test context dict

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was clean on first pass.

### Completion Notes List

- Task 1: Made `level`, `school`, `casting_time`, `range`, `components`, `duration` Optional[X] = None in CardData; added `typ: Optional[str] = None`; updated `test_load_card_missing_required_field` to assert `description` absence.
- Task 2: Added `"typ": card.typ` to renderer context dict.
- Task 3: Created `templates/talent-v1.jinja2` and `templates/rule-v1.jinja2` as Jinja2 validation markers.
- Task 4: Replaced `_VIOLET` with `_CARD_COLORS` dict + `_card_color()` helper; propagated `color` param through all drawing helpers; added `_draw_shield_icon`, `_draw_scroll_icon`, `_draw_back_icon`; added type-specific front-face branch in `_draw_strip`.
- Task 5: Created `scripts/import_srd_data.py` with `slugify()`, `import_talents()`, `import_rules()`, and main block.
- Task 6: Ran import script — 17 files in `data/de/SRD 5.2/talents/`, 155 files in `data/de/SRD 5.2/rules/`.
- Task 7: Added `test_card_data_talent_minimal`, `test_render_card_talent_context`, `test_compose_pdf_talent_card_no_error`, `test_compose_pdf_rule_card_no_error`; updated `_fake_ctx` with `typ` and `source_book` keys.
- Task 8: ruff ✅, mypy --strict ✅, pytest 60/60 ✅.

### File List

- `src/dnd_cards/models.py` — 6 spell fields made Optional; `typ` field added
- `src/dnd_cards/renderer.py` — `"typ": card.typ` added to context dict
- `src/dnd_cards/composer.py` — `_CARD_COLORS` table; colour param on all helpers; shield/scroll/back-icon dispatchers; generic front-face branch
- `templates/talent-v1.jinja2` — new file
- `templates/rule-v1.jinja2` — new file
- `scripts/import_srd_data.py` — new import utility
- `data/de/SRD 5.2/talents/` — 17 new card YAML files
- `data/de/SRD 5.2/rules/` — 155 new card YAML files
- `tests/test_loader.py` — updated `test_load_card_missing_required_field`
- `tests/test_models.py` — added `test_card_data_talent_minimal`
- `tests/test_renderer.py` — added `test_render_card_talent_context`
- `tests/test_composer.py` — updated `_fake_ctx`; added `test_compose_pdf_talent_card_no_error`, `test_compose_pdf_rule_card_no_error`

### Change Log

- 2026-04-12: Story 4.3 implemented — talent/rule card type support added; 172 SRD card files imported; 4 new tests; 60/60 tests pass

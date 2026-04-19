---
story_id: "4.4"
story_key: "4-4-class-feature-card-type"
epic: "Epic 4: Seed Data & Polish"
status: "review"
created: "2026-04-18"
---

# Story 4.4: Class Feature Card Type — Model Support & Template

## Story

As Tobias,
I want the 233 class feature YAML files (already extracted to `data/de/SRD 5.2/classes/`) to load,
render, and produce PDF cards that show the class name, level, optional subclass, and description,
so that I can build decks combining class features with spells and talents.

---

## Acceptance Criteria

**AC1 — `CardData` loads a class feature YAML without `template` field:**
- **Given** a class feature YAML such as:
  ```yaml
  id: barbar-kampfrausch
  type: class_feature
  class: Barbar
  lang: de
  level: 1
  name: Kampfrausch
  description: "..."
  source_book: SRD 5.2.1
  ```
- **When** `load_card(path)` is called
- **Then** it returns a `CardData` with `class_name="Barbar"`, `level=1`, and `template="class-feature-v1"` (auto-injected by loader)
- **And** no `ValidationError` is raised

**AC2 — `CardData` loads a subclass feature YAML:**
- **Given** a class feature YAML containing `subclass: Pfad des Berserkers`
- **When** `load_card(path)` is called
- **Then** the resulting `CardData` has `subclass="Pfad des Berserkers"`

**AC3 — `CardData` model accepts class feature fields:**
- **Given** a `CardData` constructed directly with `class_name="Barbar"`, `level=1`, `type="class_feature"`, no spell fields
- **Then** `card.class_name == "Barbar"`
- **And** `card.school is None`, `card.casting_time is None`, etc.
- **And** the model is frozen (mutation raises `TypeError`)

**AC4 — Renderer includes `class_name` and `subclass` in context dict:**
- **Given** a class feature `CardData` with `class_name` set
- **When** `render_card(card, "class-feature-v1")` is called
- **Then** the returned context dict contains `"class_name": "Barbar"` and `"subclass": None` (or the value if set)

**AC5 — Template `class-feature-v1.jinja2` exists and uses class feature fields:**
- **Given** `templates/class-feature-v1.jinja2` exists
- **When** the template is used to validate the render pipeline
- **Then** the file references `{{ class_name }}`, `{{ level }}`, `{{ name }}`, `{{ description }}`
- **And** `{% if subclass %}` guard wraps the subclass display

**AC6 — PDF renders class feature cards with a distinct warm-amber colour:**
- **Given** a `CardData` with `type="class_feature"`
- **When** `compose_pdf([card], output_path)` is called (with renderer mock)
- **Then** the header uses the warm-amber colour (`(0.85, 0.75, 0.55)`) — not violet or grey
- **And** the front face shows: name in header, `{class_name} · Stufe {level}` line, optional subclass in italic, description (word-wrapped), source_book at the bottom
- **And** the back face shows a sword/tower icon (not the spellbook)
- **And** no exception is raised

**AC7 — Existing spell, talent, and rule rendering is unchanged:**
- **Given** any existing deck with spell, talent, or rule cards
- **When** `compose_pdf` runs
- **Then** output is identical to pre-story behaviour

**AC8 — Full validation suite stays green:**
- `ruff check src/` exits 0
- `mypy --strict src/` exits 0
- `pytest` — all existing tests pass plus new tests for class feature

---

## Tasks / Subtasks

- [x] Task 1: Extend `CardData` model (AC: 1, 2, 3)
  - [x] Add `class_name: Optional[str] = Field(default=None, alias="class")` to `CardData`
  - [x] Add `subclass: Optional[str] = None` to `CardData`
  - [x] Change `model_config` to `ConfigDict(frozen=True, populate_by_name=True)` so alias works
  - [x] Keep `template: str` required in the model — injection happens in loader (see Task 2)
- [x] Task 2: Update loader to auto-inject `template` for class features (AC: 1)
  - [x] In `load_card()`, after parsing `raw`, call `raw["template"] = _DEFAULT_TEMPLATES.get(...)` when absent
  - [x] Add module-level constant: `_DEFAULT_TEMPLATES: dict[str, str] = {"class_feature": "class-feature-v1"}`
  - [x] The constant does NOT need entries for spell/talent/rule — those always have `template` in YAML
- [x] Task 3: Update renderer to include `class_name` and `subclass` (AC: 4)
  - [x] Add `"class_name": card.class_name` to context dict in `render_card()`
  - [x] Add `"subclass": card.subclass` to context dict
- [x] Task 4: Create template `templates/class-feature-v1.jinja2` (AC: 5)
  - [x] Template content (see Dev Notes for exact content)
- [x] Task 5: Update composer for `class_feature` colour, icon, and front-face layout (AC: 6, 7)
  - [x] Add `"class_feature": (0.85, 0.75, 0.55)` to `_CARD_COLORS` dict
  - [x] Add `_draw_sword_icon()` for class feature back face
  - [x] Extend `_draw_back_icon()` dispatcher: `elif card_type == "class_feature": _draw_sword_icon(...)`
  - [x] Add `"class_feature"` branch in `_draw_strip` front-face section (see Dev Notes)
- [x] Task 6: Add tests (AC: 1–4, 6, 8)
  - [x] `test_models.py`: `test_card_data_class_feature_minimal` — CardData with class_name, level, no spell fields
  - [x] `test_models.py`: `test_card_data_class_feature_with_subclass` — CardData with subclass field set
  - [x] `test_loader.py`: `test_load_card_class_feature_no_template` — loads a YAML without `template`, verifies auto-injection
  - [x] `test_renderer.py`: `test_render_card_class_feature_context` — context has `class_name` and `subclass`
  - [x] `test_composer.py`: `test_compose_pdf_class_feature_no_error` — class feature card renders without error
  - [x] `test_composer.py`: `test_compose_pdf_class_feature_with_subclass_no_error` — subclass variant renders
  - [x] Update `_fake_ctx` in `test_composer.py` to include `class_name` and `subclass` keys
- [x] Task 7: Run full validation suite (AC: 8)
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — 87/87 tests pass

---

## Dev Notes

### Data Shape

The 233 class feature YAML files are in `data/de/SRD 5.2/classes/` (already extracted — do NOT re-import).

**Fields present in every class feature YAML:**
| YAML key | `CardData` field | Type | Notes |
|---|---|---|---|
| `id` | `id` | `str` | slug, e.g. `barbar-kampfrausch` |
| `type` | `type` | `str` | always `"class_feature"` |
| `class` | `class_name` | `Optional[str]` | alias — Python reserved word |
| `lang` | `lang` | `Language` | always `"de"` |
| `level` | `level` | `Optional[int]` | 1–20 |
| `name` | `name` | `str` | German name |
| `description` | `description` | `str` | required |
| `source_book` | `source_book` | `Optional[str]` | always `"SRD 5.2.1"` |
| *(absent)* | `template` | `str` | auto-injected as `"class-feature-v1"` by loader |

**Optional field (58 of 233 files):**
| YAML key | `CardData` field | Notes |
|---|---|---|
| `subclass` | `subclass` | e.g. `"Pfad des Berserkers"` |

**12 classes present:** Barbar, Barde, Druide, Hexenmeister, Kleriker, Kämpfer, Magier, Mönch, Paladin, Schurke, Waldläufer, Zauberer

### Task 1 — Exact `models.py` changes

Add two fields to `CardData` and update `model_config`:

```python
from pydantic import BaseModel, ConfigDict, Field

class CardData(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)

    id: str
    type: str
    template: str
    name: str
    lang: Language
    # Spell-specific — None for non-spell cards
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
    # Class feature fields
    class_name: Optional[str] = Field(default=None, alias="class")
    subclass: Optional[str] = None
```

**Key constraint:** `populate_by_name=True` is required so that the model can be constructed both by alias (`"class"`) and by field name (`"class_name"`) — the latter is needed for direct construction in tests.

### Task 2 — Loader template auto-injection

In `src/dnd_cards/loader.py`, add at module level:

```python
_DEFAULT_TEMPLATES: dict[str, str] = {
    "class_feature": "class-feature-v1",
}
```

In `load_card()`, after `raw` is parsed and confirmed to be a dict, add one line before `CardData.model_validate(raw)`:

```python
if "template" not in raw:
    raw["template"] = _DEFAULT_TEMPLATES.get(str(raw.get("type", "")), "")
```

This is a targeted one-line guard. Spell/talent/rule YAMLs always have `template` in their YAML, so the guard only fires for class features (and hypothetical future types).

**Important:** `raw` is a `dict` returned by `yaml.safe_load()`, so mutation is safe here. Do NOT mutate a frozen Pydantic model.

### Task 3 — Renderer context dict

In `src/dnd_cards/renderer.py`, extend the context dict:

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
    "typ": card.typ,
    "description": card.description,
    "edition": card.edition,
    "source_book": card.source_book,
    "class_name": card.class_name,   # ← add
    "subclass": card.subclass,       # ← add
}
```

### Task 4 — Template file

**`templates/class-feature-v1.jinja2`:**
```jinja2
{{ name }}
{{ class_name }} · Stufe {{ level }}{% if subclass %} ({{ subclass }}){% endif %}

{{ description }}
{% if source_book %}Quelle: {{ source_book }}{% endif %}
```

The template is a validation marker (renderer checks it exists, then returns a Python dict). Minimal content is fine.

### Task 5 — Composer changes (detailed)

**5a — Add colour entry in `_CARD_COLORS`:**
```python
_CARD_COLORS: dict[str, tuple[float, float, float]] = {
    "spell":         (0.75, 0.62, 0.85),  # pastel violet
    "talent":        (0.62, 0.62, 0.65),  # pastel grey
    "rule":          (0.62, 0.62, 0.65),  # pastel grey
    "class_feature": (0.85, 0.75, 0.55),  # warm amber/gold
}
```

**5b — Add `_draw_sword_icon()`** for class feature back face:

```python
def _draw_sword_icon(
    c: Any, cx: float, cy: float, size: float,
    color: tuple[float, float, float],
) -> None:
    rv, gv, bv = color
    dv = rv * 0.72, gv * 0.72, bv * 0.72
    blade_w = size * 0.15
    blade_h = size * 0.75
    guard_w = size * 0.55
    guard_h = size * 0.12
    grip_w = size * 0.10
    grip_h = size * 0.28

    bx = cx - blade_w / 2
    by = cy - blade_h * 0.35

    # Blade
    p = c.beginPath()
    p.moveTo(cx, by + blade_h)          # tip
    p.lineTo(bx, by)                    # bottom-left
    p.lineTo(bx + blade_w, by)          # bottom-right
    p.close()
    c.setFillColorRGB(rv, gv, bv)
    c.setStrokeColorRGB(*dv)
    c.setLineWidth(1.0)
    c.drawPath(p, stroke=1, fill=1)

    # Guard (crosspiece)
    gx = cx - guard_w / 2
    gy = by - guard_h / 2
    c.setFillColorRGB(*dv)
    c.rect(gx, gy, guard_w, guard_h, stroke=0, fill=1)

    # Grip
    grx = cx - grip_w / 2
    gry = gy - grip_h
    c.setFillColorRGB(rv * 0.85, gv * 0.85, bv * 0.75)
    c.roundRect(grx, gry, grip_w, grip_h, grip_w * 0.3, stroke=0, fill=1)

    _draw_sparkle(c, cx, by + blade_h + size * 0.12, size * 0.14, color)
```

**5c — Extend `_draw_back_icon()` dispatcher:**
```python
def _draw_back_icon(
    c: Any, cx: float, cy: float, size: float,
    card_type: str, color: tuple[float, float, float],
) -> None:
    if card_type == "spell":
        _draw_spellbook_icon(c, cx, cy, size, color)
    elif card_type == "talent":
        _draw_shield_icon(c, cx, cy, size, color)
    elif card_type == "class_feature":
        _draw_sword_icon(c, cx, cy, size, color)
    else:
        _draw_scroll_icon(c, cx, cy, size, color)
```

**5d — Add `class_feature` branch in `_draw_strip` front-face section:**

In the `else` block (generic front face), before `"talent"`/`"rule"` handling, extract the front-face section and add a `class_feature` sub-branch. The existing generic branch already handles the `class_feature` type correctly via `ctx.get("typ")` guard (it will be `None`). However, for class features we want to show `{class_name} · Stufe {level}` instead of the `typ` line.

Replace the `else:` front-face block with:

```python
    else:
        # ── Generic front face (talent / rule / class_feature) ─────────────
        line_y = front_top - header_h
        if card_type == "class_feature":
            # class · level line
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
                if line_y < front_bottom + 4:
                    break
        else:
            line_y -= 6

        c.setFont("Helvetica", 6)
        line_y -= 4
        src = ctx.get("source_book")
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
```

### Task 6 — New tests

**`tests/test_models.py` — add:**
```python
def test_card_data_class_feature_minimal() -> None:
    """Class feature card with required fields and no spell fields."""
    card = CardData(
        id="barbar-kampfrausch",
        type="class_feature",
        template="class-feature-v1",
        name="Kampfrausch",
        lang=Language.DE,
        description="Eine Urmacht...",
        class_name="Barbar",
        level=1,
        source_book="SRD 5.2.1",
    )
    assert card.class_name == "Barbar"
    assert card.subclass is None
    assert card.school is None
    assert card.casting_time is None


def test_card_data_class_feature_with_subclass() -> None:
    """Class feature with subclass field."""
    card = CardData(
        id="barbar-raserei",
        type="class_feature",
        template="class-feature-v1",
        name="Raserei",
        lang=Language.DE,
        description="...",
        class_name="Barbar",
        level=3,
        subclass="Pfad des Berserkers",
    )
    assert card.subclass == "Pfad des Berserkers"
```

**`tests/test_loader.py` — add:**
```python
def test_load_card_class_feature_no_template(tmp_path: Path) -> None:
    """Class feature YAML without 'template' field loads with auto-injected template."""
    yaml_path = tmp_path / "kampfrausch.yaml"
    yaml_path.write_text(
        "id: barbar-kampfrausch\n"
        "type: class_feature\n"
        "class: Barbar\n"
        "lang: de\n"
        "level: 1\n"
        "name: Kampfrausch\n"
        "description: Eine Urmacht...\n"
        "source_book: SRD 5.2.1\n",
        encoding="utf-8",
    )
    card = load_card(yaml_path)
    assert card.template == "class-feature-v1"
    assert card.class_name == "Barbar"
    assert card.level == 1
```

**`tests/test_renderer.py` — add:**
```python
def test_render_card_class_feature_context(tmp_path: Path) -> None:
    """render_card for class feature includes class_name and subclass."""
    (tmp_path / "class-feature-v1.jinja2").write_text(
        "{{ name }}\n{{ class_name }}\n", encoding="utf-8"
    )
    card = CardData(
        id="barbar-kampfrausch",
        type="class_feature",
        template="class-feature-v1",
        name="Kampfrausch",
        lang=Language.DE,
        description="...",
        class_name="Barbar",
        level=1,
    )
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        ctx = render_card(card, "class-feature-v1")

    assert ctx["class_name"] == "Barbar"
    assert ctx["subclass"] is None
    assert ctx["level"] == 1
```

**`tests/test_composer.py` — update `_fake_ctx` and add test:**

Update `_fake_ctx` to include `class_name` and `subclass`:
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
        "class_name": card.class_name,
        "subclass": card.subclass,
    }
```

Add test:
```python
def test_compose_pdf_class_feature_no_error(tmp_path: Path) -> None:
    """Class feature card renders without error."""
    feat = CardData(
        id="barbar-kampfrausch",
        type="class_feature",
        template="class-feature-v1",
        name="Kampfrausch",
        lang=Language.DE,
        description="Eine Urmacht namens Kampfrausch...",
        class_name="Barbar",
        level=1,
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([feat], buf)
    assert buf.tell() > 0


def test_compose_pdf_class_feature_with_subclass_no_error(tmp_path: Path) -> None:
    """Class feature with subclass renders without error."""
    feat = CardData(
        id="barbar-raserei",
        type="class_feature",
        template="class-feature-v1",
        name="Raserei",
        lang=Language.DE,
        description="...",
        class_name="Barbar",
        level=3,
        subclass="Pfad des Berserkers",
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([feat], buf)
    assert buf.tell() > 0
```

### Architecture Constraints

- **`mypy --strict`** — `Field` import from `pydantic` is required; `class_name` must be `Optional[str]`, not just `str | None`; `_DEFAULT_TEMPLATES` must be typed `dict[str, str]`
- **`ruff TID252`** — no relative imports in `src/`
- **`populate_by_name=True`** in `model_config` — required so tests can construct `CardData(class_name="Barbar")` without using the alias
- **Loader mutation guard** — `raw` is a plain dict from PyYAML; mutation is safe. Do NOT mutate after `model_validate()`
- **`level_school` in spell branch** — only computed inside the `card_type == "spell"` branch; do NOT use it in the `class_feature` branch (it would crash on `None` school)
- **No re-import of files** — the 233 YAML files in `data/de/SRD 5.2/classes/` are already correct; do NOT run `import_srd_data.py` or modify those files
- **Scanner unchanged** — directory name `classes` becomes `card_type`; deck keys look like `classes/barbar-kampfrausch: 1`

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/models.py` | Add `class_name` (alias `class`), `subclass`; update `model_config` |
| `src/dnd_cards/loader.py` | Add `_DEFAULT_TEMPLATES`; inject template when absent in `load_card()` |
| `src/dnd_cards/renderer.py` | Add `class_name` and `subclass` to context dict |
| `src/dnd_cards/composer.py` | Add amber colour; `_draw_sword_icon()`; extend dispatcher; add `class_feature` front-face branch |
| `templates/class-feature-v1.jinja2` | New file |
| `tests/test_models.py` | Add 2 new tests |
| `tests/test_loader.py` | Add 1 new test |
| `tests/test_renderer.py` | Add 1 new test |
| `tests/test_composer.py` | Update `_fake_ctx`; add 2 new tests |

### Regression Safeguard

- **All existing tests must stay green** — spell/talent/rule cards are unaffected; `populate_by_name=True` is backward-compatible with existing construction patterns
- **`_fake_ctx` update is mandatory** — `_draw_strip` now reads `ctx.get("class_name")` and `ctx.get("subclass")`; without these keys in the mock context, the class_feature branch silently degrades but other tests still pass since those types skip the branch
- **`template` remains `str` (required) in `CardData`** — the loader injects it, so `model_validate()` always receives it; do not make it `Optional` in the model

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was clean on first pass.

### Completion Notes List

- Task 1: Added `class_name: Optional[str] = Field(default=None, alias="class")` and `subclass: Optional[str] = None` to `CardData`; updated `model_config` to `ConfigDict(frozen=True, populate_by_name=True)` for alias+direct-construction support.
- Task 2: Added `_DEFAULT_TEMPLATES` constant and template injection guard in `load_card()` — fires only when `template` key is absent (class feature YAMLs); spell/talent/rule unaffected.
- Task 3: Added `"class_name": card.class_name` and `"subclass": card.subclass` to renderer context dict.
- Task 4: Created `templates/class-feature-v1.jinja2` with name, class·level, optional subclass, description, and source_book.
- Task 5: Added `"class_feature": (0.85, 0.75, 0.55)` to `_CARD_COLORS`; added `_draw_sword_icon()` (blade triangle + guard + grip + sparkle); extended `_draw_back_icon()` dispatcher for `class_feature`; added `class_feature` front-face sub-branch in `_draw_strip` showing `{class_name} · Stufe {level}` and optional subclass.
- Task 6: Added 7 tests across 4 test files; updated `_fake_ctx` with `class_name` and `subclass` keys.
- Task 7: ruff ✅, mypy --strict ✅, pytest 87/87 ✅.

### File List

- `src/dnd_cards/models.py` — added `class_name` (alias `class`) and `subclass` fields; `populate_by_name=True`
- `src/dnd_cards/loader.py` — added `_DEFAULT_TEMPLATES`; template auto-injection in `load_card()`
- `src/dnd_cards/renderer.py` — added `class_name` and `subclass` to context dict
- `src/dnd_cards/composer.py` — amber colour entry; `_draw_sword_icon()`; extended dispatcher; class_feature front-face branch
- `templates/class-feature-v1.jinja2` — new template file
- `tests/test_models.py` — added `test_card_data_class_feature_minimal`, `test_card_data_class_feature_with_subclass`
- `tests/test_loader.py` — added `test_load_card_class_feature_no_template`
- `tests/test_renderer.py` — added `test_render_card_class_feature_context`
- `tests/test_composer.py` — updated `_fake_ctx`; added `test_compose_pdf_class_feature_no_error`, `test_compose_pdf_class_feature_with_subclass_no_error`

### Change Log

- 2026-04-18: Story 4.4 implemented — class_feature card type added; `class_name`/`subclass` model fields; template auto-injection in loader; sword icon and amber colour in composer; 7 new tests; 87/87 tests pass

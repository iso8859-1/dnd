---
story_id: "2.2"
story_key: "2-2-jinja2-template-system-and-spell-card-renderer"
epic: "Epic 2: Core PDF Generation"
status: "review"
created: "2026-04-12"
---

# Story 2.2: Jinja2 Template System & Spell Card Renderer

## Story

As Tobias,
I want a `zauber-v1.jinja2` template that defines the visual layout of a spell card,
so that card appearance is controlled by a file I can edit without touching any Python code.

---

## Acceptance Criteria

**AC1 — `render_card()` returns a context dict with all card field values:**
- **Given** `templates/zauber-v1.jinja2` exists with placeholders for all `CardData` fields (name, level, school, casting_time, range, components, duration, description)
- **When** `renderer.render_card(card: CardData, template_name: str) -> dict[str, Any]` is called
- **Then** it returns a context dict containing all card field values
- **And** the dict is passed to `compose_pdf()` — no canvas or PDF objects are created in this function

**AC2 — German text (umlauts, ß) preserved without HTML escaping:**
- **Given** the Jinja2 `Environment` is configured with `autoescape=False` and loader rooted at `templates/`
- **When** a card with German text (umlauts, ß) is rendered
- **Then** the context dict preserves those characters without HTML escaping (e.g. `ü` stays `ü`, not `&uuml;`)

**AC3 — Missing template raises `GenerationError`:**
- **Given** a template name that does not exist as `templates/{name}.jinja2`
- **When** `renderer.render_card()` is called
- **Then** a `GenerationError` is raised with the missing template name in the message

---

## Tasks / Subtasks

- [x] Task 1: Add module-level `_TEMPLATES_DIR` and implement `render_card()` in `renderer.py` (AC: 1, 2, 3)
  - [x] Import `jinja2`, `pathlib.Path`, `GenerationError` in `renderer.py`
  - [x] Add `_TEMPLATES_DIR: Path = Path("templates")` module-level constant (enables test patching)
  - [x] Implement `render_card()`: create Jinja2 env with `autoescape=False`, load template, build context dict, return it
  - [x] On `jinja2.TemplateNotFound` → raise `GenerationError(f"Template not found: {template_name}")`
- [x] Task 2: Create `templates/zauber-v1.jinja2` (AC: 1, 2)
  - [x] Add Jinja2 template with placeholders for all spell card fields
- [x] Task 3: Implement `tests/test_renderer.py` (AC: 1, 2, 3)
  - [x] Test `render_card()` returns a dict with correct field values (use `tmp_path` + patch `_TEMPLATES_DIR`)
  - [x] Test German text (umlaut characters) preserved in context dict values
  - [x] Test missing template raises `GenerationError` with template name in message
  - [x] Test returned dict contains all required fields
- [x] Task 4: Run full validation suite
  - [x] `ruff check src/` exits 0
  - [x] `mypy --strict src/` exits 0
  - [x] `pytest` — all tests pass (no regressions, 38 existing tests green)

---

## Dev Notes

### What Is Already Done — Do Not Touch

- **`src/dnd_cards/renderer.py`** — stub exists:
  ```python
  from typing import Any
  from dnd_cards.models import CardData

  __all__ = ["render_card"]

  def render_card(card: CardData, template_name: str) -> dict[str, Any]:
      """Render a card to a context dict via Jinja2. Implementation in Story 2.2."""
      raise NotImplementedError
  ```
- **`templates/`** — directory exists at project root with `.gitkeep` only. Create `zauber-v1.jinja2` inside it.
- **`tests/test_renderer.py`** — contains only a comment `# Tests implemented in Story 2.2`. Replace entirely.
- **`jinja2`** is already a project dependency (see `pyproject.toml`): `jinja2>=3.1.0`
- **`src/dnd_cards/errors.py`** — `GenerationError` is defined and ready to use
- **38 tests currently passing** — all must stay green

### Files to Touch

| File | Change |
|---|---|
| `src/dnd_cards/renderer.py` | Add imports, `_TEMPLATES_DIR` constant, implement `render_card()` |
| `templates/zauber-v1.jinja2` | Create spell card template |
| `tests/test_renderer.py` | Replace stub with real tests |

### Exact `renderer.py` Implementation

```python
"""Jinja2 template rendering for card data."""

from pathlib import Path
from typing import Any

import jinja2

from dnd_cards.errors import GenerationError
from dnd_cards.models import CardData

__all__ = ["render_card"]

# Module-level constant — patch `dnd_cards.renderer._TEMPLATES_DIR` in tests
_TEMPLATES_DIR: Path = Path("templates")


def render_card(card: CardData, template_name: str) -> dict[str, Any]:
    """Render a card to a context dict via Jinja2.

    Validates the template exists, then returns a dict of all card field
    values for use by compose_pdf(). No canvas or PDF objects are created here.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=False,
    )
    try:
        env.get_template(f"{template_name}.jinja2")
    except jinja2.TemplateNotFound as exc:
        raise GenerationError(f"Template not found: {template_name}") from exc

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
        "description": card.description,
        "edition": card.edition,
        "source_book": card.source_book,
    }
    return context
```

**Key implementation notes:**
- `autoescape=False` — **never change this**; PDF content is not HTML; enabling autoescape would corrupt German chars
- `env.get_template(...)` is called only to validate the template exists; no `.render()` call needed here
- `_TEMPLATES_DIR: Path = Path("templates")` resolves relative to CWD at runtime (correct for CLI use from project root)
- `card.lang.value` — converts `Language.DE` enum to `"de"` string for the context dict
- `edition` and `source_book` are `Optional[str]` — stored as-is (may be `None`) for compose_pdf to handle

### `templates/zauber-v1.jinja2` Content

```jinja2
{{ name }}
Stufe {{ level }} · {{ school }}
Zauberzeit: {{ casting_time }}
Reichweite: {{ range }}
Komponenten: {{ components }}
Wirkungsdauer: {{ duration }}
{{ description }}
{% if edition %}Ausgabe: {{ edition }}{% endif %}
{% if source_book %}Quelle: {{ source_book }}{% endif %}
```

The template uses every field from `CardData`. It is the only template in this story; `compose_pdf()` (Story 2.3) will use the rendered context dict to draw text on the ReportLab canvas.

**Strip geometry reminder (for template authors):** Each strip is 176mm wide × 63mm tall (landscape orientation) on the A4 page. The fold line is at 88mm from the left edge. Front content goes in the left half (0–88mm), back content in the right half (88–176mm). The final folded card is 88mm × 63mm — Magic card portrait size.

### `tests/test_renderer.py` — Complete Test File

**Test strategy:** Tests must not depend on CWD being the project root. Create a real `zauber-v1.jinja2` in `tmp_path` and patch `dnd_cards.renderer._TEMPLATES_DIR` to point to it.

```python
"""Tests for renderer module."""

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from dnd_cards.errors import GenerationError
from dnd_cards.models import CardData, Language
from dnd_cards.renderer import render_card


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
        description="A bright streak flashes from your pointing finger.",
        edition="5e",
        source_book="SRD 5.1",
    )


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    """Create a temp templates dir with zauber-v1.jinja2."""
    (tmp_path / "zauber-v1.jinja2").write_text(
        "{{ name }} Level {{ level }} {{ school }}", encoding="utf-8"
    )
    return tmp_path


def test_render_card_returns_dict(spell_card: CardData, templates_dir: Path) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", templates_dir):
        result = render_card(spell_card, "zauber-v1")
    assert isinstance(result, dict)


def test_render_card_context_has_correct_values(spell_card: CardData, templates_dir: Path) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", templates_dir):
        ctx = render_card(spell_card, "zauber-v1")
    assert ctx["name"] == "Fireball"
    assert ctx["level"] == 3
    assert ctx["school"] == "Evocation"
    assert ctx["casting_time"] == "1 action"
    assert ctx["range"] == "150 ft"
    assert ctx["components"] == "V, S, M"
    assert ctx["duration"] == "Instantaneous"
    assert ctx["description"] == "A bright streak flashes from your pointing finger."
    assert ctx["edition"] == "5e"
    assert ctx["source_book"] == "SRD 5.1"
    assert ctx["lang"] == "en"


def test_render_card_preserves_german_text(tmp_path: Path) -> None:
    (tmp_path / "zauber-v1.jinja2").write_text("{{ name }}", encoding="utf-8")
    german_card = CardData(
        id="feuerball",
        type="spell",
        template="zauber-v1",
        name="Feuerball — Zerstörungszauber",
        lang=Language.DE,
        level=3,
        school="Verwandlung",
        casting_time="1 Aktion",
        range="45 m",
        components="V, S, M",
        duration="Sofort",
        description="Ein heller Streifen schießt aus deinem Finger. Äther und Ödland.",
    )
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        ctx = render_card(german_card, "zauber-v1")
    # Characters must NOT be HTML-escaped (autoescape=False)
    assert "Feuerball — Zerstörungszauber" in ctx["name"]
    assert "Äther" in ctx["description"]
    assert ctx["lang"] == "de"


def test_render_card_missing_template_raises_generation_error(
    spell_card: CardData, tmp_path: Path
) -> None:
    # tmp_path has no templates — any lookup should fail
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        with pytest.raises(GenerationError) as exc_info:
            render_card(spell_card, "nonexistent-template")
    assert "nonexistent-template" in str(exc_info.value)


def test_render_card_contains_all_required_fields(spell_card: CardData, templates_dir: Path) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", templates_dir):
        ctx = render_card(spell_card, "zauber-v1")
    required = {"id", "type", "template", "name", "lang", "level", "school",
                "casting_time", "range", "components", "duration", "description",
                "edition", "source_book"}
    assert required.issubset(ctx.keys())
```

### Architecture Constraints

- **`autoescape=False`** — mandatory; PDF is not HTML; enabling autoescape corrupts German characters
- **Template filename convention** — `{type}-v{n}.jinja2`; card YAML stores `template: zauber-v1`; renderer appends `.jinja2` on lookup
- **`render_card()` returns context dict only** — no canvas, no ReportLab, no PDF objects
- **`_TEMPLATES_DIR` resolves relative to CWD** — correct for CLI use; tests must patch this constant
- **Patch `dnd_cards.renderer._TEMPLATES_DIR`** (where it's used), not `jinja2.FileSystemLoader` directly
- **Absolute imports only** — `from dnd_cards.errors import GenerationError` (ruff TID252)
- **`__all__ = ["render_card"]`** — keep as-is; do not expose `_TEMPLATES_DIR`
- **No new dependencies** — `jinja2` is already in `pyproject.toml`
- **`card.lang.value`** — use `.value` to get the string `"de"`/`"en"`, not the enum object

### Regression Safeguard

All 38 existing tests must remain green. Only `renderer.py`, `templates/zauber-v1.jinja2`, and `tests/test_renderer.py` are modified.

### Project Context

- **Run:** `uv run pytest -v`, `uv run ruff check src/`, `uv run mypy --strict src/`
- **Project root:** `C:\Development\dnd`
- **Current test count:** 38 (all passing)
- **Jinja2 version:** `>=3.1.x` (already installed)

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- ✅ AC1: `render_card()` returns `dict[str, Any]` with all 14 `CardData` field values; no canvas or PDF objects created
- ✅ AC2: `autoescape=False` confirmed — German chars (ü, ö, ß, Ä) preserved unescaped in context dict values
- ✅ AC3: `jinja2.TemplateNotFound` → `GenerationError(f"Template not found: {template_name}")`; template name in message
- ✅ `_TEMPLATES_DIR: Path = Path("templates")` module-level constant enables patching without changing function signature
- ✅ `templates/zauber-v1.jinja2` created with all spell card field placeholders
- ✅ `ruff check src/` — All checks passed
- ✅ `mypy --strict src/` — Success: no issues found in 11 source files
- ✅ `pytest` — 44/44 passed (6 new + 38 regressions all green)

### File List

- `src/dnd_cards/renderer.py`
- `templates/zauber-v1.jinja2`
- `tests/test_renderer.py`

### Change Log

- 2026-04-12: Implemented `render_card()` with Jinja2 env + context dict; `zauber-v1.jinja2` template created; 6 renderer tests. All ACs satisfied.

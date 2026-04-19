# dnd-cards — Architecture

**Generated:** 2026-04-12 | **Scan level:** Deep

---

## Executive Summary

`dnd-cards` is a single-package Python CLI that converts YAML card data into print-ready A4 PDFs. It follows a strict pipeline architecture: discover → load → render → compose → output. All state lives in files; no process state is maintained between runs.

A companion TUI (Textual-based) allows interactive construction of deck profile YAMLs.

---

## Module Architecture

```
src/dnd_cards/
├── __init__.py          (empty)
├── cli.py               Typer app — argument parsing, error routing, exit codes
├── config.py            Global constants: PDF dimensions, default paths
├── errors.py            DndCardsError hierarchy (4 typed subclasses)
├── models.py            Pydantic v2 models: CardData, DeckProfile, DeckEntry, Language
├── loader.py            PyYAML parse + Pydantic validate for card and deck files
├── scanner.py           Runtime scan of data/ tree → dict[key, CardRef]
├── renderer.py          Jinja2 template validation + context dict construction
├── composer.py          ReportLab PDF layout: A4 landscape, 4×1 strip grid
└── tui.py               Textual TUI deck builder: DeckBuilderApp, run_tui()
```

### Module responsibilities

| Module | Responsibility | Raises |
|---|---|---|
| `cli.py` | Parse args, call domain, catch all exceptions, print errors to stderr, set exit code | — |
| `config.py` | Module-level constants only | — |
| `errors.py` | Exception class definitions only | — |
| `models.py` | Immutable data containers (frozen Pydantic) | — |
| `loader.py` | YAML → dict → Pydantic model; wraps PyYAML + Pydantic errors | `YamlParseError`, `ValidationError` |
| `scanner.py` | `data/` tree scan → `dict[str, CardRef]`; no YAML reads | — |
| `renderer.py` | Validate template exists; return context dict | `GenerationError` |
| `composer.py` | ReportLab canvas; calls `render_card` per card; `canvas.save()` in `try/finally` | `GenerationError` |
| `tui.py` | Textual `App`; reads card index and YAML names; writes deck YAML on save | — |

---

## Data Flow

### `generate` subcommand

```
dnd-cards generate --deck decks/example.yaml
         │
         ▼
    cli.py           parse --deck arg
         │
         ▼
    scanner.py       scan data/ → dict["{type}/{stem}", CardRef]
         │
         ▼
    loader.py        load_deck() → DeckProfile; load_card() × N → list[CardData]
         │
         ▼
    renderer.py      render_card(card, card.template) → dict[str, Any]  (per card)
         │
         ▼
    composer.py      compose_pdf(cards, out_path)
                       for each card: _draw_strip(canvas, ctx, x, y, w, h)
         │
         ▼
    stdout: output/example.pdf
```

### `tui` subcommand

```
dnd-cards tui [deck.yaml]
         │
         ▼
    tui.py           DeckBuilderApp(data_dir, deck_name, deck_file)
                       on_mount: scan_cards() + _load_name() per card
                       on key: filter/search, +/- qty, F-key lang, 1-9 type
                       ctrl+s: write deck YAML to decks/{slug}.yaml
```

---

## Data Models

### `CardData` (frozen)

```python
class CardData(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str                          # e.g. "feuerball"
    type: str                        # e.g. "spell", "talent", "rule"
    template: str                    # e.g. "zauber-v1" (filename without .jinja2)
    name: str                        # display name
    lang: Language                   # Language.DE | Language.EN
    # Spell-specific (None for talent/rule)
    level: Optional[int] = None
    school: Optional[str] = None
    casting_time: Optional[str] = None
    range: Optional[str] = None
    components: Optional[str] = None
    duration: Optional[str] = None
    # Shared optional
    typ: Optional[str] = None        # talent category label
    description: str                 # required for all types
    edition: Optional[str] = None
    source_book: Optional[str] = None
```

### `DeckProfile` (frozen)

```python
class DeckProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    entries: list[DeckEntry]         # reshaped from YAML 'cards' dict

class DeckEntry(BaseModel):
    model_config = ConfigDict(frozen=True)
    card_key: str    # "{card_type}/{id}" e.g. "spells/feuerball"
    quantity: int    # ≥1
```

**YAML deck format vs model:** Deck YAMLs use `cards: {key: qty}` (flat dict). `loader.load_deck()` reshapes this into `entries: [DeckEntry]` before passing to `model_validate()`.

---

## Error Handling

### Exception hierarchy

```python
DndCardsError           (base)
  ├── YamlParseError    exit 1 — YAML syntax error (includes file + line)
  ├── ValidationError   exit 1 — Pydantic validation failure (includes file + field)
  ├── CardNotFoundError exit 1 — deck references unknown card key
  └── GenerationError   exit 2 — ReportLab PDF composition failure
```

### Error routing in `cli.py`

```python
def _handle_dnd_error(exc: BaseException) -> NoReturn:
    if isinstance(exc, (YamlParseError, ValidationError, CardNotFoundError)):
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    if isinstance(exc, GenerationError):
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    typer.echo(traceback.format_exc(), err=True)   # unexpected → full traceback
    raise typer.Exit(2)
```

**Contract:** Domain modules raise, never print. `cli.py` is the sole output/exit boundary.

---

## PDF Layout

Cards are printed as fold-strips: a `63×176mm` portrait strip that folds in half to produce a `63×88mm` double-sided card (standard Magic card size).

```
A4 landscape (297×210mm):
┌──────────────────────────────────────────────────┐
│  [strip1] gap [strip2] gap [strip3] gap [strip4]  │  ← 4 strips × 63mm + 3 gaps × 5mm = 267mm ≤ 297mm
│  each strip: 63×176mm                             │  ← 176mm ≤ 210mm
└──────────────────────────────────────────────────┘

Each strip:
┌─────────────────┐  ← y + 176mm  (top of strip)
│  FRONT FACE     │
│  ┌─────────────┐│  ← colored header band (7.5mm) with title
│  │ name        ││
│  │─────────────││
│  │ level·school││  ← spell only
│  │ casting_time││
│  │ range       ││
│  │ components  ││
│  │ duration    ││
│  │ description ││
│  └─────────────┘│  ← y + 88mm
│  - - - - - - - -│  ← fold guide (dashed line)
│  BACK FACE      │  ← rotated 180° so it reads after forward fold
│  ┌─────────────┐│  ← colored header + name
│  │   [icon]    ││  ← spellbook / shield / scroll based on card type
│  └─────────────┘│
└─────────────────┘  ← y (bottom of strip)
```

### Color coding

| Card type | Color |
|---|---|
| `spell` | Pastel violet `(0.75, 0.62, 0.85)` |
| `talent` | Pastel grey `(0.62, 0.62, 0.65)` |
| `rule` | Pastel grey `(0.62, 0.62, 0.65)` |

### Back-face icons

| Card type | Icon |
|---|---|
| `spell` | Stylised spellbook with sparkle |
| `talent` | Pointed shield with cross |
| `rule` | Rolled scroll |

---

## Template System

Templates are Jinja2 files in `templates/`. Filename convention: `{type}-v{n}.jinja2`.

| Template | Card type |
|---|---|
| `zauber-v1.jinja2` | spell (German) |
| `spell.jinja2` | spell (English, legacy) |
| `talent-v1.jinja2` | talent |
| `rule-v1.jinja2` | rule |

The `renderer.py` validates template existence only — no rendering to HTML/text. The template file acts as a presence-check marker; actual card layout is drawn directly in `composer.py`.

---

## Card Scanner

```python
def scan_cards(data_dir: Path) -> dict[str, CardRef]:
    # key = "{card_type}/{stem}"   e.g. "spells/feuerball"
    # card_type = immediate parent directory name
```

Directory structure drives everything: `data/{lang}/{rulebook}/{card_type}/{id}.yaml`.

Example: `data/de/SRD 5.2/spells/feuerball.yaml` → key `spells/feuerball`, `card_type="spells"`.

---

## TUI Deck Builder

`DeckBuilderApp` (Textual `App`) runs a full-screen interactive deck builder.

### Layout

```
┌─ Header (deck name · card count) ─────────────────┐
│ [search input — always focused]                    │
│ ┌─ DataTable ────────────────────────────────────┐ │
│ │ Name          Type       Qty                   │ │
│ │ Feuerball     spells     ×2                    │ │
│ │ Blitz         spells                           │ │
│ └────────────────────────────────────────────────┘ │
│ F1=●de  F2= en  1=●rules  2= spells  +/−  qty  q  │
└────────────────────────────────────────────────────┘
```

### Key bindings

| Key | Action |
|---|---|
| Typing | Fuzzy-filter card name (subsequence match) |
| `+` | Increment qty of highlighted card; clear search |
| `-` | Decrement qty |
| `F1`–`F4` | Toggle language filter (from `data/` first-level dirs) |
| `1`–`9` | Toggle card type filter (from unique `card_type` values) |
| `Escape` | Clear search |
| `Ctrl+S` | Save deck YAML |
| `q` | Quit |

### Save format

```yaml
name: My Deck
cards:
  spells/feuerball: 2
  talents/ringer: 1
```

Saved to `decks/{slug}.yaml` (or the `deck_file` path if provided).

---

## Key Architectural Boundaries

| Boundary | Contract |
|---|---|
| CLI ↔ domain | `cli.py` sole catch boundary; domain never prints or exits |
| Scanner ↔ Loader | Scanner returns paths only; no YAML content read |
| YAML ↔ Models | `loader.py` reshapes raw YAML dict before `model_validate()` |
| Templates ↔ Renderer | Renderer validates template existence; does not render to string |
| Composer ↔ Canvas | Canvas injected as param (enables `BytesIO` in tests); `str(path)` at call site |
| Fonts ↔ ReportLab | `register_fonts()` called once at CLI startup; no-op if no TTF files |
| TUI ↔ Scanner | TUI calls `scan_cards()` and reads `name` field per card; no full `load_card()` |

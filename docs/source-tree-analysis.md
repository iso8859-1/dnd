# dnd-cards — Source Tree Analysis

**Generated:** 2026-04-12 | **Scan level:** Deep

---

## Annotated Directory Tree

```
dnd-cards/
│
├── pyproject.toml              ← project metadata, dependencies, ruff/mypy/pytest config
├── uv.lock                     ← committed lockfile (pins Typer/Click versions)
├── .python-version             ← Python version pin for uv
├── .gitignore
│
├── src/
│   └── dnd_cards/              ← single installable package
│       ├── __init__.py         (empty — package marker)
│       ├── cli.py              ENTRY POINT — Typer app with 4 subcommands
│       ├── config.py           module-level constants: PDF dimensions, default dirs
│       ├── errors.py           DndCardsError hierarchy (YamlParseError, ValidationError,
│       │                       CardNotFoundError, GenerationError)
│       ├── models.py           Pydantic v2: CardData, DeckProfile, DeckEntry, Language
│       ├── loader.py           load_card(path) + load_deck(path) — YAML → Pydantic
│       ├── scanner.py          scan_cards(data_dir) → dict[str, CardRef]
│       ├── renderer.py         render_card(card, template_name) → dict[str, Any]
│       ├── composer.py         compose_pdf(cards, output_path) — ReportLab A4 layout
│       ├── tui.py              DeckBuilderApp (Textual), run_tui(), slugify()
│       └── assets/
│           └── fonts/          TTF font files (registered via importlib.resources)
│               └── .gitkeep
│
├── templates/                  ← Jinja2 card layout templates
│   ├── zauber-v1.jinja2        spell (German SRD)
│   ├── spell.jinja2            spell (English, legacy)
│   ├── talent-v1.jinja2        talent cards
│   └── rule-v1.jinja2          rule/glossary cards
│
├── data/                       ← Git-versioned YAML card data store
│   └── de/                     ← language: German
│       └── SRD 5.2/            ← rulebook edition
│           ├── spells/         ← 339 YAML files (one per spell)
│           │   ├── feuerball.yaml
│           │   ├── blitz.yaml
│           │   └── ...
│           ├── talents/        ← 17 YAML files
│           │   ├── ringer.yaml
│           │   └── ...
│           └── rules/          ← 155 YAML files
│               ├── abenteuer.yaml
│               └── ...
│
├── decks/                      ← deck profile YAMLs (user-created)
│   ├── .gitkeep
│   └── example.yaml            ← example deck for testing/demo
│
├── assets/
│   └── fonts/                  ← TTF font files (project root copy, if any)
│       └── .gitkeep
│
├── output/                     ← generated PDFs (.gitignored)
│   └── example.pdf
│
├── scripts/                    ← one-off data import utilities
│   ├── convert_srd_spells.py   converts raw SRD YAML to per-card files
│   └── import_srd_data.py      imports talents + rules from SRD source files
│
├── SRDs/                       ← source materials (PDFs + raw YAML extracts)
│   ├── DE_SRD_CC_v5.2.1.pdf
│   ├── SRD_CC_v5.1.pdf
│   ├── SRD_CC_v5.1_DE.pdf
│   ├── SRD_CC_v5.2.1.pdf
│   ├── allgemeine_talente.yaml
│   ├── epische_gabe_talente.yaml
│   ├── herkunftstalente.yaml
│   ├── kampfstiltalente.yaml
│   ├── regelglossar.yaml
│   └── zauberbeschreibungen.yaml
│
├── tests/
│   ├── conftest.py             shared fixtures: valid_card_data, fixture_path
│   ├── fixtures/
│   │   ├── spells/             YAML fixtures for loader tests
│   │   ├── decks/              deck YAML fixtures
│   │   └── expected_output/    baseline PDFs for regression testing
│   ├── test_models.py          Pydantic model tests
│   ├── test_errors.py          DndCardsError hierarchy tests
│   ├── test_loader.py          load_card / load_deck tests
│   ├── test_scanner.py         scan_cards tests
│   ├── test_renderer.py        render_card tests
│   ├── test_composer.py        compose_pdf tests (canvas injected as BytesIO)
│   ├── test_cli.py             CLI tests (typer.testing.CliRunner)
│   ├── test_tui.py             TUI tests (Textual async pilot)
│   └── integration/
│       └── test_pipeline.py    full CLI → PDF smoke test (marked slow)
│
├── _bmad-output/               ← BMAD planning + implementation artifacts
│   ├── planning-artifacts/
│   │   ├── prd.md              Product Requirements Document
│   │   ├── architecture.md     Architecture Decision Document
│   │   └── epics.md            Epic breakdown
│   ├── implementation-artifacts/
│   │   ├── sprint-status.yaml  Story-level status tracking
│   │   ├── 1-*.md … 5-*.md     Individual story files
│   │   └── deferred-work.md    Deferred implementation notes
│   └── brainstorming/          Brainstorming session outputs
│
└── .claude/                    ← Claude Code / BMAD skill definitions
    └── skills/
        └── bmad-*/
```

---

## Critical Folders

| Folder | Purpose |
|---|---|
| `src/dnd_cards/` | All application code — 9 modules |
| `templates/` | Jinja2 card templates — add new file to support new card type |
| `data/de/SRD 5.2/` | 511 YAML card files in 3 subdirectories |
| `decks/` | User deck profile YAMLs (`cards: {key: qty}` format) |
| `tests/` | pytest suite — unit + async TUI + integration |
| `src/dnd_cards/assets/fonts/` | TTF fonts loaded via `importlib.resources` |

---

## Entry Points

| File | Purpose |
|---|---|
| `src/dnd_cards/cli.py` | `dnd_cards.cli:app` — registered in `pyproject.toml [project.scripts]` |
| `src/dnd_cards/tui.py` | `run_tui()` called from `cli.py tui` subcommand |
| `scripts/import_srd_data.py` | One-off script to populate `data/` from SRD YAML source files |

---

## File Counts

| Location | Count |
|---|---|
| Python source modules | 9 |
| Jinja2 templates | 4 |
| YAML card data files | 511 |
| Test files | 9 (+ 1 integration) |
| Deck profile YAMLs | 1 (example) |

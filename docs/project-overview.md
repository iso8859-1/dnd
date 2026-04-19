# dnd-cards — Project Overview

**Generated:** 2026-04-12 | **Scan level:** Deep | **Type:** CLI tool (monolith)

---

## What it does

`dnd-cards` is a command-line tool that generates print-ready A4 PDF reference cards for D&D 5.5e (German SRD). Cards are folded double-sided: the front face shows game stats, the back face shows an icon and the card title. PDFs are assembled from a deck profile YAML that references cards by key.

The tool also ships an interactive terminal UI (TUI) for building those deck YAMLs by browsing and searching the card catalog.

---

## Technology Stack

| Category | Technology | Version | Notes |
|---|---|---|---|
| Language | Python | 3.11+ | `pathlib`, `importlib.resources` |
| CLI framework | Typer | 0.9.x | Shell completion via Click |
| PDF generation | ReportLab | 4.4.x | mm-precise geometry, no external process |
| Template engine | Jinja2 | 3.1.x | File-based templates, `autoescape=False` |
| YAML parsing | PyYAML | 6.0.x | `safe_load` only; `problem_mark` for error location |
| Schema validation | Pydantic v2 | 2.5.x | `model_validate()` on plain dicts; frozen models |
| Terminal UI | Textual | 8.2.3+ | Full-screen TUI deck builder |
| Dependency manager | uv | latest | `uv.lock` committed; `uv tool install .` for deployment |
| Build backend | hatchling | latest | `[build-system]` in `pyproject.toml` |
| Linter | ruff | 0.15.x | `TID252` bans relative imports |
| Type checker | mypy | 1.20.x | `--strict` mode |
| Testing | pytest + pytest-cov | 9.x / 7.x | `asyncio_mode=auto` for Textual pilot tests |

---

## Architecture Type

**Pipeline CLI** — pure local file I/O, no network, no database, no server.

```
YAML files → loader (Pydantic) → renderer (Jinja2) → composer (ReportLab) → PDF
```

Card data lives in a `data/` directory tree. The scanner discovers cards at runtime by directory traversal; no card registry is maintained. Deck profiles are YAML files that reference cards by `{card_type}/{stem}` key.

---

## Data Summary

| Language | Rulebook | Card type | Count |
|---|---|---|---|
| de | SRD 5.2 | spells | 339 |
| de | SRD 5.2 | talents | 17 |
| de | SRD 5.2 | rules | 155 |
| **Total** | | | **511** |

---

## Repository Structure

```
dnd-cards/                 ← monolith, single Python package
├── src/dnd_cards/         ← application source (9 modules)
├── tests/                 ← pytest suite (unit + integration)
├── templates/             ← Jinja2 card layout templates
├── data/                  ← Git-versioned YAML card data
├── decks/                 ← deck profile YAMLs
├── assets/fonts/          ← TTF fonts for PDF rendering
├── scripts/               ← one-off SRD import utilities
├── SRDs/                  ← source PDFs and raw YAML extracts
└── output/                ← generated PDFs (.gitignored)
```

---

## Entry Points

| Command | Module | Description |
|---|---|---|
| `dnd-cards generate --deck <file>` | `cli.py → composer.py` | Generate PDF from deck profile |
| `dnd-cards list [--type <type>]` | `cli.py → scanner.py` | List available cards |
| `dnd-cards tui [<deck>]` | `cli.py → tui.py` | Interactive TUI deck builder |
| `dnd-cards validate --deck <file>` | `cli.py` | Validate deck (stub, Epic 3) |

---

## Key Design Decisions

1. **No database** — plain YAML, Git-versioned. Scanner runs at startup; `<1s` for 500+ cards.
2. **No network** — fully offline, portable. `uv tool install .` is the deployment model.
3. **Frozen Pydantic models** — `CardData`, `DeckProfile`, `DeckEntry` are immutable after load.
4. **Single catch boundary** — only `cli.py` catches exceptions; domain modules raise typed errors, never print.
5. **New card type = zero code changes** — add a Jinja2 template + YAML files; `composer.py` dispatches on `card.type`.
6. **`pathlib.Path` everywhere** — `str()` only at the ReportLab `Canvas()` call boundary.
7. **Absolute imports only** — `ruff TID252` bans relative imports project-wide.

---

## Links

- [Architecture](./architecture.md) — detailed module design, data flow, error contracts
- [Source Tree](./source-tree-analysis.md) — annotated directory tree
- [Development Guide](./development-guide.md) — setup, test, lint, build commands
- [Planning artifacts](_bmad-output/planning-artifacts/) — PRD, epics, architecture decision doc
- [Sprint status](_bmad-output/implementation-artifacts/sprint-status.yaml) — story-by-story progress

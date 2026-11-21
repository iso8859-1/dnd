# dnd-cards — Project Overview

**Updated:** 2026-11-21 | **Type:** Desktop app + CLI (Cargo workspace)

---

## What it does

`dnd-cards` generates print-ready A4 PDF reference cards for D&D 5.5e (German SRD).
Two print modes are supported:

- **Fold strips** — a 63×176mm strip per card, four per A4 landscape page. Fold at the
  middle: the front face shows the game text, the back face (printed upside down) shows
  the title and a type icon.
- **Duplex** — 63×88mm faces, nine per A4 portrait page pair. Fronts on odd pages, backs
  on even pages with columns mirrored for long-edge double-sided printing; no folding.

A **desktop app** (Tauri) is the main way to build decks: search and filter the card
catalog, preview cards, set quantities, save/open deck YAML files and generate either PDF.
A **CLI** (`dnd-cards`) does the same headlessly from a deck YAML.

---

## Technology Stack

| Category | Technology | Notes |
|---|---|---|
| Language | Rust 2021, MSRV 1.82 | Cargo workspace with three members |
| PDF generation | `pdf-writer` 0.15 | Base-14 Helvetica family, WinAnsiEncoding, no font embedding |
| YAML | `serde_yaml_ng` 0.10 | Maintained fork of `serde_yaml` |
| Serialization | `serde` | Lenient scalar → string handling for text fields |
| Ordered maps | `indexmap` | Deck card order is preserved on load/save |
| Errors | `thiserror` 2 | One `Error` enum with exit-code mapping |
| Filesystem walk | `walkdir` | Sorted, recursive card discovery |
| CLI | `clap` 4 (derive) | |
| Desktop shell | Tauri 2 | `tauri-plugin-dialog`, `tauri-plugin-opener` |
| Frontend | HTML/CSS/vanilla JS | No npm / bundler; served from `ui/` via `withGlobalTauri` |
| Tests | `cargo test` + `tempfile` | Unit tests live next to the code |

---

## Architecture Type

**Shared-core pipeline** — pure local file I/O, no network, no database, no server.

```
data/**/*.yaml → scanner → loader (serde) → composer (pdf-writer) → PDF bytes
                                   ▲
           CLI (clap)  ────────────┤
           Tauri commands ◄── ui/app.js (invoke)
```

---

## Data Summary

| Language | Rulebook | Card type (dir) | Count | Printable |
|---|---|---|---|---|
| de | SRD 5.2 | spells | 339 | yes |
| de | SRD 5.2 | classes | 233 | yes |
| de | SRD 5.2 | rules | 155 | yes |
| de | SRD 5.2 | talents | 17 | yes |
| de | SRD 5.2 | monsters | 330 | **no** — stat blocks have no `description`; no layout yet |
| **Total** | | | **1074** | |

---

## Entry Points

| Entry | Location | Description |
|---|---|---|
| `dnd-cards-app [deck.yaml]` | `src-tauri/` | Desktop deck builder; optional deck path is opened at start |
| `dnd-cards generate --deck <file> [--duplex] [--output-dir output]` | `crates/dnd-cards-cli` | Write `<output-dir>/<deck-stem>.pdf` |
| `dnd-cards validate --deck <file>` | `crates/dnd-cards-cli` | Load the deck and every referenced card |
| `dnd-cards list [--type <dir>]` | `crates/dnd-cards-cli` | List `stem [type]`, sorted |
| `--data-dir <path>` (global) | CLI | Override data store location |

---

## Key Design Decisions

1. **No database** — plain YAML, Git-versioned; the scanner indexes ~1000 files at startup.
2. **One core, two front-ends** — all parsing and layout lives in `dnd-cards-core`; the CLI
   and the app are thin wrappers.
3. **Layout parity** — the PDF code is a direct port of the former ReportLab layout; output
   was verified pixel-identical against the Python version.
4. **No embedded fonts** — Helvetica / Helvetica-Bold / Helvetica-Oblique with WinAnsi
   encoding cover German text („“, –, …, umlauts, ß); unmappable characters become `?`.
5. **Rust-side dialogs** — file dialogs and opening the PDF run in Tauri commands, so the
   webview only needs `core:default`; no plugin permissions are exposed to JavaScript.
6. **No frontend build step** — `ui/` is static files; the app builds with Cargo alone.
7. **Card type from directory** — the scanner never reads YAML; the key is
   `{parent_dir}/{stem}`, the language is the first directory under `data/`.

---

## Links

- [Architecture](./architecture.md)
- [Source Tree](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)

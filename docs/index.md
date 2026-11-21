# dnd-cards — Documentation Index

**Updated:** 2026-11-21 | **Type:** Desktop app + CLI (Rust / Tauri 2 Cargo workspace)

---

## Quick Reference

| | |
|---|---|
| **Language** | Rust (stable, MSRV 1.82) + plain HTML/CSS/JS for the UI |
| **Architecture** | Shared core library → CLI binary and Tauri desktop app |
| **Pipeline** | scan → load (serde) → compose (pdf-writer) → PDF |
| **Binaries** | `dnd-cards` (CLI), `dnd-cards-app` (desktop, product name "DnD Cards") |
| **Distribution** | Tauri installers (card data bundled) + CLI archive with `data/` |
| **Data** | 1074 YAML card files in `data/de/SRD 5.2/` (339 spells · 233 class features · 155 rules · 17 talents · 330 monsters) |
| **Checks** | `cargo test` · `cargo clippy` · `cargo fmt` |

---

## Documentation

- [Project Overview](./project-overview.md) — what it does, tech stack, key design decisions
- [Architecture](./architecture.md) — crates, data flow, models, errors, PDF layout, desktop app
- [Source Tree](./source-tree-analysis.md) — annotated directory tree
- [Development Guide](./development-guide.md) — setup, build, test, release, adding card types, deck format

### Planning artifacts

- [PRD](../_bmad-output/planning-artifacts/prd.md) — Product Requirements Document
- [Architecture Decision Doc](../_bmad-output/planning-artifacts/architecture.md) — original (Python-era) architecture decisions
- [Epics](../_bmad-output/planning-artifacts/epics.md) — epic and story breakdown

### Implementation tracking

- [Sprint Status](../_bmad-output/implementation-artifacts/sprint-status.yaml) — story-by-story progress
- [Deferred Work](../_bmad-output/implementation-artifacts/deferred-work.md) — known deferred items

> The planning artifacts and story files predate the Rust rewrite; they describe the
> Python implementation (Typer, ReportLab, Textual). Requirements still apply; module and
> library names do not.

---

## Getting Started

```bash
cargo install tauri-cli --version "^2" --locked   # once

cargo tauri dev                                   # desktop deck builder
cargo run -p dnd-cards-cli -- list                # list cards
cargo run -p dnd-cards-cli -- generate --deck decks/example.yaml [--duplex]
cargo test --workspace
```

---

## Module Map

| Crate | Module | Key exports |
|---|---|---|
| `dnd-cards-core` | `models.rs` | `CardData`, `DeckProfile`, `Language` |
| | `loader.rs` | `load_card()`, `load_deck()`, `save_deck()`, `load_name()` |
| | `scanner.rs` | `scan_cards()`, `CardRef`, `discover_languages()` |
| | `layout.rs` | `layout_info()`, `printed_count()`, `LayoutInfo`, wrapping and planning |
| | `metrics.rs` (private) | Helvetica glyph width tables |
| | `composer.rs` | `compose_pdf()`, `compose_pdf_duplex()` |
| | `pdf.rs` (private) | `Canvas` — ReportLab-style drawing on `pdf-writer` |
| | `config.rs` | layout constants, `find_data_dir()` |
| | `error.rs` | `Error` (4 variants) + `exit_code()` |
| | `text.rs` | `slugify()` |
| | `lib.rs` | `resolve_deck()`, `write_pdf()` |
| `dnd-cards-cli` | `main.rs` | `dnd-cards list / validate / generate` (clap) |
| `dnd-cards-app` | `src-tauri/src/lib.rs` | Tauri commands: `catalog`, `card_details`, `initial_deck`, `open_deck`, `save_deck`, `generate_pdf` |
| (frontend) | `ui/app.js` | deck builder UI state, rendering, keyboard handling |

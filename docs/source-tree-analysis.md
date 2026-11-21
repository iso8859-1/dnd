# dnd-cards — Source Tree Analysis

**Updated:** 2026-11-21

---

## Annotated Directory Tree

```
dnd/
├── Cargo.toml                    # workspace: members, shared version (0.4.0) and dependency versions
├── Cargo.lock                    # committed lockfile
├── Readme.md                     # user-facing README (German)
├── LICENSE                       # MIT (code); SRD texts are CC-BY 4.0
│
├── crates/
│   ├── dnd-cards-core/           # library: everything except UI
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs            # re-exports, resolve_deck(), generate()
│   │       ├── models.rs         # CardData, DeckProfile, Language
│   │       ├── loader.rs         # load_card/load_deck/save_deck/load_name + tests
│   │       ├── scanner.rs        # scan_cards, discover_languages + tests
│   │       ├── composer.rs       # fold-strip + duplex layouts, icons + tests
│   │       ├── pdf.rs            # Canvas over pdf-writer, WinAnsi encoding + tests
│   │       ├── config.rs         # layout constants, find_data_dir()
│   │       ├── error.rs          # Error enum, exit codes
│   │       └── text.rs           # wrap(), slugify() + tests
│   │
│   └── dnd-cards-cli/            # binary `dnd-cards`
│       ├── Cargo.toml
│       └── src/main.rs           # clap: list / validate / generate, --data-dir
│
├── src-tauri/                    # Tauri 2 app crate `dnd-cards-app`
│   ├── Cargo.toml
│   ├── build.rs                  # tauri_build::build()
│   ├── tauri.conf.json           # window, CSP, bundle (icons, data/ resources)
│   ├── capabilities/default.json # core:default for the main window
│   ├── icons/                    # generated with `cargo tauri icon` (ico, icns, png)
│   ├── gen/                      # generated schemas (gitignored)
│   └── src/
│       ├── main.rs               # entry; hides console on Windows release builds
│       └── lib.rs                # AppState, commands, data-dir resolution, run()
│
├── ui/                           # static frontend served by Tauri (no build step)
│   ├── index.html                # layout: toolbar, filters, list, preview, deck, status bar
│   ├── style.css                 # light/dark tokens, type colours, grid layout
│   └── app.js                    # state, ranking search, rendering, keyboard, invoke() calls
│
├── data/                         # card data store (Git-versioned)
│   └── de/SRD 5.2/
│       ├── spells/      (339)    # type: spell
│       ├── classes/     (233)    # type: class_feature
│       ├── rules/       (155)    # type: rule
│       ├── talents/      (17)    # type: talent
│       └── monsters/    (330)    # type: monster — not printable yet
│
├── decks/                        # user deck YAMLs (*.yaml gitignored)
├── scripts/                      # Python one-off SRD importers (need PyYAML)
│   ├── import_srd_data.py        # split SRDs/*.yaml into per-card files
│   └── convert_srd_spells.py     # convert raw spell extract into per-card files
├── SRDs/                         # SRD source text and raw YAML extracts
├── assets/                       # README example image
├── docs/                         # this documentation
├── .github/workflows/release.yml # tag-triggered release: Tauri installers + CLI archives
├── _bmad/, _bmad-output/         # BMAD config, planning and story artifacts (Python era)
├── target/                       # Cargo build output (gitignored)
└── output/                       # CLI default PDF output (gitignored)
```

---

## Critical Folders

| Folder | Why it matters |
|---|---|
| `crates/dnd-cards-core/src` | All business logic and PDF layout |
| `src-tauri/src` | The only code that touches dialogs, app paths and the OS opener |
| `ui/` | Entire desktop UI; edited files are picked up by `cargo tauri dev` on reload |
| `data/` | Card content; directory names define card types and languages |
| `src-tauri/tauri.conf.json` | Bundling (resources, icons), CSP, window size |

---

## Entry Points

| Entry | File |
|---|---|
| CLI `main()` | `crates/dnd-cards-cli/src/main.rs` |
| App `main()` → `dnd_cards_app::run()` | `src-tauri/src/main.rs` → `src-tauri/src/lib.rs` |
| UI bootstrap (IIFE at the end) | `ui/app.js` |
| Library API | `crates/dnd-cards-core/src/lib.rs` |

---

## File Counts

| Area | Files |
|---|---|
| Core crate sources | 9 |
| CLI sources | 1 |
| Tauri sources | 2 (+ config, capability, icons) |
| Frontend | 3 |
| Card YAML | 1074 |

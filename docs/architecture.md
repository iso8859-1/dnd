# dnd-cards — Architecture

**Updated:** 2026-11-21

---

## Executive Summary

A Cargo workspace with one library and two front-ends:

| Crate | Path | Kind | Purpose |
|---|---|---|---|
| `dnd-cards-core` | `crates/dnd-cards-core` | lib | Models, YAML I/O, scanning, PDF composition |
| `dnd-cards-cli` | `crates/dnd-cards-cli` | bin `dnd-cards` | Headless list / validate / generate |
| `dnd-cards-app` | `src-tauri` | bin + lib | Tauri 2 desktop deck builder (frontend in `ui/`) |

The core has no knowledge of Tauri, terminals or dialogs. It takes paths and data and
returns values, `Result`s or PDF bytes.

---

## Crate Architecture

```
                 ┌──────────────────────── dnd-cards-core ────────────────────────┐
                 │ scanner ──► loader ──► models ──► composer ──► pdf (Canvas)    │
                 │    │                     ▲            ▲                        │
                 │    └── config (constants, find_data_dir)  layout (plan, wrap) + metrics │
                 │ error (Error, exit_code)     lib (resolve_deck, generate)      │
                 └────────────────────────────────────────────────────────────────┘
                          ▲                                   ▲
        dnd-cards-cli (clap, exit codes)       dnd-cards-app (Tauri commands)
                                                              ▲ invoke()
                                                        ui/app.js + index.html + style.css
```

### Module responsibilities (core)

| Module | Responsibility |
|---|---|
| `models.rs` | `CardData`, `DeckProfile`, `Language`; serde derives; lenient scalar deserializers |
| `loader.rs` | Read + parse YAML; map errors to `YamlParse` / `Validation`; write decks; fast `load_name()` |
| `scanner.rs` | Walk `data/` (sorted), build `BTreeMap<key, CardRef>`; list language dirs |
| `layout.rs` | Width-based wrapping, title fitting, per-card layout plan (`PrintCard`s), `LayoutInfo` |
| `metrics.rs` | Helvetica / -Bold / -Oblique glyph widths (WinAnsi), `width()` |
| `composer.rs` | Draws planned cards: fold-strip and duplex pages, faces, back-face icons |
| `pdf.rs` | Private `Canvas`: ReportLab-like drawing API, page list, WinAnsi encoding, PDF assembly |
| `config.rs` | Layout constants (mm), `find_data_dir()`, `find_default_data_dir()` |
| `text.rs` | `slugify()` |
| `error.rs` | `Error` enum, `exit_code()` |
| `lib.rs` | Re-exports, `resolve_deck()`, `generate()` (scan + resolve + compose + write) |

---

## Data Flow

### CLI `generate`

```
dnd-cards generate --deck decks/x.yaml [--duplex] [--deck-order] [--output-dir output]
  │
  ├─ data dir = --data-dir │ $DND_CARDS_DATA │ ./data │ <exe dir and 2 parents>/data
  ├─ load_deck(path)                → DeckProfile { name, cards: IndexMap<key, qty> }
  ├─ scan_cards(data_dir)           → BTreeMap<"spells/feuerball", CardRef>
  ├─ resolve_deck(deck, index)      → Vec<CardData>, each card repeated qty times, deck order
  │     └─ unknown key → Error::CardNotFound
  ├─ compose_pdf / compose_pdf_duplex(&cards) → Vec<u8>
  └─ write <output-dir>/<deck stem>.pdf, print path
```

`generate` prints a note to stderr for every card that needs follow-on cards.
`validate` stops after `resolve_deck` and prints a summary
(`OK (n cards, m printed; x continue on the back, y with smaller text, z on several cards)`);
`--layout` lists every card that doesn't print as a plain single card.
`list` prints `stem [type]` for every indexed card, optionally filtered by `--type`.

### Desktop app

```
startup ─► setup(): data dir = saved source (settings.json) │ $DND_CARDS_DATA │ <resources>/data │ find_default_data_dir()
                    initial deck = first CLI arg if it is a file
ui start ─► invoke("data_sources")   → { sources[{id,name,description,path,kind}], active, datasets_dir }
         ─► invoke("catalog")        → { data_dir, source, languages, types, cards[{key,name,card_type,lang,level,layout,error}] }
                                        level = spell grade │ feature level │ feat min. level (UI level filter)
         ─► invoke("initial_deck")   → deck or null
select   ─► invoke("card_details", {key}) → CardData (cached per key in the UI)
Ctrl+O   ─► invoke("open_deck")      → native open dialog → { path, name, cards[[key,qty]] }
Ctrl+S   ─► invoke("save_deck", {path, saveAs, name, cards}) → dialog if no path / save-as
Ctrl+G/D ─► invoke("generate_pdf", {name, cards, duplex})
               resolve + compose in memory → native save dialog → write → open in default viewer
Data     ─► invoke("set_data_source", {id}) │ "add_data_source" (folder dialog) │ "remove_data_source" │
            "open_datasets_folder" → reload catalog, deck is kept
```

The deck in the UI is a `Map<key, qty>` whose insertion order is the deck order. It is
sent as `[[key, qty], …]` so the order survives into the YAML file and the PDF.

---

## Data Models

### `CardData`

```rust
pub struct CardData {
    pub id: String,
    #[serde(rename = "type")] pub card_type: String,   // spell | talent | rule | class_feature | …
    pub template: Option<String>,                      // legacy, kept for data compatibility
    pub name: String,
    pub lang: Language,                                // de | en
    pub level: Option<i64>,
    pub school, casting_time, range, components, duration: Option<String>,  // spells
    pub typ: Option<String>,                           // talent category
    pub description: String,                           // required
    pub edition, source_book: Option<String>,
    #[serde(rename = "class")] pub class_name: Option<String>,             // class features
    pub subclass: Option<String>,
}
```

- Unknown YAML keys are ignored (monster stat blocks parse past them, then fail on the
  missing `description`).
- Text fields accept any YAML scalar (`range: 18` → `"18"`).
- `class_feature` cards without `template` get `class-feature-v1` (legacy behaviour).
- Serialized with the same field names for the UI preview (`type`, `class`).

### `DeckProfile`

```rust
pub struct DeckProfile {
    pub name: String,                       // required
    pub cards: IndexMap<String, u32>,       // card key → quantity; missing/null → empty
}
```

On disk:

```yaml
name: Magier Stufe 5
cards:
  spells/feuerball: 2
  talents/bogenschiessen: 1
```

---

## Error Handling

```rust
pub enum Error {
    YamlParse(String),     // syntax error ("… at line N"), empty file, non-mapping → exit 1
    Validation(String),    // serde schema error, prefixed with the file path        → exit 1
    CardNotFound(String),  // deck references a key not in the index                 → exit 1
    Generation(String),    // writing output failed                                  → exit 2
}
```

- Core functions return `Result<T, Error>` and never print.
- The CLI prints `Display` to stderr and exits with `exit_code()`.
- Tauri commands convert errors to `String`; the UI shows them in the status bar.
- Cancelling a dialog is not an error: commands return `Ok(None)`.

---

## PDF Layout

All geometry is in points (1mm = 72/25.4pt); origin bottom-left as in PDF.

### Fold strips (`compose_pdf`)

```
A4 landscape (297×210mm), 4 strips per page, centred:
  4 × 63mm + 3 × 5mm gap = 267mm wide, 176mm tall

Each strip (63×176mm):
┌─────────────────┐  ← top
│ ███ name ██████ │  ← 7.5mm header band, white bold 9pt title
│ front content   │
│                 │
│ source (grey)   │
├ ─ ─ ─ ─ ─ ─ ─ ─ ┤  ← 88mm: double-width fold edge + dashed grey guide
│      [icon]     │  ← back face, drawn rotated 180°
│ ██████ eman ███ │
└─────────────────┘
```

Each half has its own rounded border (3mm radius, stroke = header height / 3) so the folded
card has rounded corners on both sides.

### Duplex (`compose_pdf_duplex`)

```
A4 portrait, 3 × 3 faces of 63×88mm, 5mm gaps, centred (199 × 274mm).
Per group of 9 cards: front page, then back page.
Back page: column c → (cols-1-c), so faces line up after a long-edge flip.
Slot 0 is the bottom-left (row 0 = lowest row).
```

### Front face content

| Card type | Under the header |
|---|---|
| `spell` | `Stufe N · school` (7pt), then `Zeit`, `Reichweite`, `Komp.`, `Dauer` (7pt, wrapped) |
| `class_feature` | `class · Stufe N` in oblique 7pt, optional `(subclass)` |
| other with `typ` | `typ` in oblique 7pt, wrapped |
| other | — |

Then the description; `source_book` is printed grey at the bottom if present.
All text is wrapped by measured width (`metrics.rs`, Adobe AFM widths) to the 57mm between
the paddings; words wider than a line are split. Titles shrink from 9pt to 6pt to fit the
header and are truncated with `…` only below that.

### Fitting long text (`layout.rs`)

Each card is planned once as one or more `PrintCard`s (front + back). The first option
that fits wins:

| Step | Description size | Where the text goes |
|---|---|---|
| 1 | 6pt | front only (back shows the icon) |
| 2 | 5.5pt | front only |
| 3 | 6pt | front, continued on the back face instead of the icon |
| 4 | 5.5pt | front + back |
| 5 | 5.5pt | front + back + follow-on cards with text on both faces, titled `Name (i/n)` |

No text is ever dropped. Body line pitch is `size × 4/3` (8pt at 6pt). In the fold-strip
mode the back text is drawn in the rotated half, so it reads correctly after folding.
`layout_info(card)` summarises the plan (`font_size`, `uses_back`, `cards`) for the CLI
and the app; `printed_count(cards)` gives the number of physical cards.

With the current data (743 printable cards): 619 plain, 51 at 5.5pt, 72 continue on the
back, 8 need a second card.

### Color coding

| Card type | RGB |
|---|---|
| `spell` | `(0.75, 0.62, 0.85)` pastel violet |
| `class_feature` | `(0.85, 0.75, 0.55)` warm amber |
| everything else | `(0.62, 0.62, 0.65)` pastel grey |

### Back-face icons

| Card type | Icon |
|---|---|
| `spell` | Spellbook with spine and page lines, sparkle above |
| `talent` | Pointed shield with white cross, sparkle below |
| `class_feature` | Sword with guard and grip, sparkle above |
| everything else | Rolled scroll, sparkle below |

### PDF writer (`pdf.rs`)

- `Canvas` collects one `pdf_writer::Content` per page; `show_page()` starts a new one.
- Rounded rectangles use ReportLab's construction (`t = 0.4472 · r`) for identical curves.
- Fonts `F1`–`F3` = Helvetica, Helvetica-Bold, Helvetica-Oblique as Type1 base-14 fonts
  with `/WinAnsiEncoding`; `encode_win_ansi()` maps Unicode to CP-1252.
- At least one page is always emitted (an empty deck yields a blank page).

---

## Card Scanner

`scan_cards(data_dir)` walks the tree sorted by file name and indexes every `*.yaml`:

- key = `{parent dir}/{file stem}` → `spells/feuerball`
- `card_type` = parent dir name (`spells`, `classes`, `rules`, `talents`, `monsters`)
- `lang` = first directory below `data_dir` (`de`)

No YAML is read. Keys must be unique across languages; a later file with the same key
replaces an earlier one. Note that the directory name (`spells`) differs from the YAML
`type` value (`spell`): filters use the directory, layout uses `type`.

---

## Desktop App

### Backend (`src-tauri/src/lib.rs`)

- `AppState { data_dir: Mutex<PathBuf>, initial_deck, last_dir }` managed by Tauri.
- `sources.rs`: data sources — `env` (`$DND_CARDS_DATA`), `bundled` (`<resources>/data`),
  `dataset:<folder>` (each folder in `<app data dir>/datasets/` with YAML below it, e.g. installed
  by a dataset installer) and `custom:<path>` (added in the UI). An optional `dataset.json`
  (`name`, `description`) in a source's root gives its display name. The selection and the
  custom folders are stored in `<app config dir>/settings.json`.
- Commands are `async` (run off the main thread); dialogs use the blocking API there.
- `bundle.resources` copies `../data/` to `data/` next to the binary (also in dev builds).
- Capability `default.json` grants only `core:default` to the `main` window.
- CSP: `default-src 'self'`.

### Frontend (`ui/`)

```
┌ toolbar: [deck name] [n cards] ●          [New] [Open…] [Save] │ [Generate PDF] [Duplex PDF] ┐
├ filters: [search……] (DE EN) (classes 233) (monsters 330) (rules) (spells) (talents) ☐ In deck only ┤
├───────────────────────────────────────────┬─────────────────────────────────┤
│ NAME                     TYPE        QTY  │  ┌ preview card ──────────────┐ │
│ Feuerball                • spells  − 2 +  │  │ header in type colour      │ │
│ …                                         │  └────────────────────────────┘ │
│                                           │  DECK                           │
│                                           │  • Feuerball            − 2 +   │
├───────────────────────────────────────────┴─────────────────────────────────┤
└ status message                                               keyboard hints ┘
```

- Search ranks results: name prefix → word prefix → substring → subsequence
  (`feurball` finds `Feuerball`), stable within a rank.
- Language chips appear only when more than one language exists; the first is preselected.
- Light/dark theme follows the OS (`prefers-color-scheme`).
- Deck entries whose key is not in the data store are shown struck through.
- `catalog` loads every card and includes its `LayoutInfo` (or the load error). The list
  and deck show a badge — `back`, `small`, `N cards`, or `not printable` (adding is
  disabled) — the preview shows the print layout, and the deck badge shows how many
  physical cards will be printed.

### Key bindings

| Key | Action |
|---|---|
| typing | focuses search and filters by name |
| `↑` `↓` `PgUp` `PgDn` | move selection |
| `+` `=` `Enter` / double-click | add one |
| `-` | remove one |
| `Del` | remove all copies (when the search box is empty or not focused) |
| `Esc` | clear search, then clear the type filter |
| `Alt+1`…`Alt+9` | toggle type filter |
| `Ctrl+N` / `Ctrl+O` | new / open deck (asks before discarding unsaved changes) |
| `Ctrl+S` / `Ctrl+Shift+S` | save / save as |
| `Ctrl+G` / `Ctrl+D` | fold-strip PDF / duplex PDF |

---

## Key Architectural Boundaries

1. `dnd-cards-core` has no UI, dialog, or process-exit code.
2. Only the CLI maps errors to exit codes; only the app maps errors to strings.
3. The webview never touches the filesystem; every file operation is a Rust command.
4. Page constants live in `config.rs`; what goes on a face is decided only in `layout.rs`,
   how it is drawn only in `composer.rs`.
5. The legacy `template` field is parsed but does not drive layout; layout dispatches on
   `card.card_type`.

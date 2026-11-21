# dnd-cards — Development Guide

**Updated:** 2026-11-21

---

## Prerequisites

- Rust stable (≥ 1.82) via [rustup](https://rustup.rs)
- Platform prerequisites for Tauri 2: <https://tauri.app/start/prerequisites/>
  - Windows: WebView2 (preinstalled on Windows 11), MSVC build tools
  - Linux: `libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf`
- Tauri CLI: `cargo install tauri-cli --version "^2" --locked`

No Node.js or npm is needed; the frontend is static files in `ui/`.

---

## Running

```bash
# Desktop app (debug build, opens a window; reload the window after editing ui/)
cargo tauri dev

# Open a deck on start
cargo run -p dnd-cards-app -- decks/mein-deck.yaml

# CLI
cargo run -p dnd-cards-cli -- list
cargo run -p dnd-cards-cli -- list --type spells
cargo run -p dnd-cards-cli -- validate --deck decks/mein-deck.yaml
cargo run -p dnd-cards-cli -- generate --deck decks/mein-deck.yaml
cargo run -p dnd-cards-cli -- generate --deck decks/mein-deck.yaml --duplex --output-dir out
cargo run -p dnd-cards-cli -- --data-dir path/to/data list
```

Data directory lookup:

| Binary | Order |
|---|---|
| CLI | `--data-dir` → `$DND_CARDS_DATA` → `./data` → `data/` next to the exe or up to two parents |
| App | `$DND_CARDS_DATA` → bundled resources `data/` → same fallback as the CLI |

CLI exit codes: `0` success, `1` YAML / validation / card-not-found, `2` output failure.

---

## Testing and Linting

```bash
cargo test --workspace                       # all unit tests
cargo test -p dnd-cards-core composer        # one module
cargo clippy --workspace --all-targets       # must be warning-free
cargo fmt --all                              # format
```

### Test structure

Tests are `#[cfg(test)] mod tests` at the bottom of each core module:

| Module | Covers |
|---|---|
| `loader` | valid card, missing field, malformed YAML with line, empty / non-mapping, bad `lang`, class-feature template default, numeric text fields, deck round-trip order, deck without name / cards, `load_name` fallback |
| `scanner` | key / type / lang derivation, non-YAML ignored, missing dir |
| `composer` | page counts (strip and duplex), every card type with and without optional fields, duplex column mirroring |
| `pdf` | WinAnsi encoding of umlauts, quotes, dashes, unmappable chars |
| `text` | `slugify`, `wrap` |

The frontend has no automated tests. To check it in a browser, serve `ui/` with a stub
`window.__TAURI__ = { core: { invoke } }` that returns catalog data.

### Visual check of PDF output

Generate a deck with the CLI and render the PDF (any viewer, or `pypdfium2`). Layout
changes should be compared against a known-good render, since unit tests only check
structure.

---

## Adding a New Card Type

1. Create `data/<lang>/<book>/<new-dir>/` and add YAML files with `type: <new_type>`,
   `id`, `name`, `lang`, `description` (+ any optional fields).
2. Without code changes the cards are listed, previewed and printed with the generic
   layout (grey colour, `typ` line if present, scroll icon).
3. For a custom look, edit `crates/dnd-cards-core/src/composer.rs`:
   - `card_color()` — header / border colour
   - `draw_front_face()` — type-specific lines under the header
   - `draw_back_icon()` — dispatch to a new icon function
4. New YAML fields: add them to `CardData` in `models.rs` (use `opt_scalar_string` for
   text) and to the preview in `ui/app.js` (`showPreview`).
5. Optional: add a dot colour for the directory name in `ui/style.css` (`.dot.<dir>`).
6. Add a case to `composer::tests::all_card_types_render`.

Monster stat blocks are the obvious next type: they need their own model (nested
`attribute`, `merkmale`, `aktionen` lists) and layout before they can be printed.

---

## Adding Card Data via Scripts

The importers are standalone Python scripts and need only PyYAML:

```bash
uv run --no-project --with pyyaml python scripts/import_srd_data.py
uv run --no-project --with pyyaml python scripts/convert_srd_spells.py
```

`import_srd_data.py` contains a copy of `slugify()` that must stay in sync with
`dnd_cards_core::text::slugify` (file names are card keys).

---

## Deck Profile YAML Format

```yaml
name: Magier Stufe 5          # required
cards:                        # card key → quantity; order = print order
  spells/feuerball: 2
  spells/magisches-geschoss: 1
  talents/bogenschiessen: 1
```

Keys are `{data subdirectory}/{file stem}`. The app removes entries with quantity 0 on
save and suggests `<slugified name>.yaml` as the file name.

---

## Project Configuration

| File | What to change there |
|---|---|
| `Cargo.toml` (root) | workspace version, shared dependency versions, MSRV |
| `crates/*/Cargo.toml`, `src-tauri/Cargo.toml` | per-crate dependencies |
| `src-tauri/tauri.conf.json` | product name, identifier, window, CSP, bundle resources/icons |
| `src-tauri/capabilities/default.json` | webview permissions (keep minimal) |
| `crates/dnd-cards-core/src/config.rs` | card / page dimensions, grid sizes, gaps, radius |

Icons: `cargo tauri icon path/to/1024x1024.png` in `src-tauri/`, then delete the
generated `android/`, `ios/` and `Square*` / `StoreLogo` files (desktop only).

---

## Building and Distribution

```bash
cargo tauri build                         # installers under target/release/bundle/
cargo build --release -p dnd-cards-cli    # target/release/dnd-cards(.exe)
```

The app bundle contains `data/` as a resource. The CLI must ship with a `data/` folder
next to the binary (or use `--data-dir` / `$DND_CARDS_DATA`).

### Releases

Pushing a tag `v*` runs `.github/workflows/release.yml`:

1. **app** — on Windows, Ubuntu 22.04 and macOS, `tauri-apps/tauri-action` builds the
   installers and creates the GitHub release.
2. **cli** — on Windows and Ubuntu, runs the core / CLI tests, builds `dnd-cards`, and
   uploads `dnd-cards-cli-windows.zip` / `dnd-cards-cli-linux.tar.gz` (binary + `data/`).

Bump `version` in the root `Cargo.toml` before tagging; the app version is read from it.

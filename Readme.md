# DnD Cards

![Kartenbeispiel](assets/card%20example.jpeg)

DnD Cards ist ein Versuch, Regel, Spruch und Talent-Karten für Dungeons & Dragons 5.5E auf deutsch zu erstellen. Da ich kein Designer bin, sind die Karten nicht besonders schön.

## Lizenz

Die Texte die aus dem SRD extrahiert wurden, stehen unter der CC-BY 4.0, der rest des Codes unter der MIT license.

## Benutzung

### Release

Lade einen Release aus der Release-Sektion herunter:

- **Desktop-App** (Installer für Windows, macOS, Linux) – enthält die Kartendaten aus dem SRD.
- **Kommandozeile** (`dnd-cards-cli-*.zip`/`.tar.gz`) – `dnd-cards` plus `data/`-Ordner.

### Desktop-App

- Datenquelle oben rechts unter *Data* wählen (wird gespeichert):
    - das mitgelieferte SRD
    - installierte Datensätze (siehe [Weitere Datensätze](#weitere-datensätze))
    - einen eigenen Ordner mit Kartendaten (*Add folder…*)
    - `$DND_CARDS_DATA`, falls gesetzt
- Karten auswählen
    - tippen sucht nach Name (unscharf, z.B. `feurball`)
    - Typ-Chips oder `Alt`+`1`–`9` filtern nach Kategorie
    - `↑`/`↓` wählt eine Karte, rechts erscheint eine Vorschau
    - `+`/`Enter` und `-` fügen Karten hinzu bzw. entfernen sie, `Entf` entfernt alle Exemplare
- Deck benennen, mit `Strg+S` speichern (`Strg+O` öffnet ein Deck, `Strg+N` beginnt ein neues)
- `Strg+G` erzeugt das Falt-PDF (4 Karten pro A4 quer), `Strg+D` das Duplex-PDF (9 Karten pro Blattpaar, beidseitig drucken)
- Lange Texte werden etwas kleiner gesetzt, auf der Rückseite fortgesetzt oder auf eine
  Folgekarte verteilt (Markierung `back`, `small`, `2 cards` in der Liste) – es wird nichts abgeschnitten
- PDF drucken
- Karten ausschneiden und falten

Optional:
- laminieren und erneut ausschneiden

### Kommandozeile

```
dnd-cards list [--type spells]
dnd-cards validate --deck decks/mein-deck.yaml [--layout]
dnd-cards generate --deck decks/mein-deck.yaml [--duplex] [--output-dir output]
```

Die Kartendaten werden in `$DND_CARDS_DATA`, `./data` oder `data/` neben der Programmdatei gesucht
(oder explizit per `--data-dir`).

### Weitere Datensätze

Zusätzliche Kartendaten (z.B. aus eigenen Büchern, die nicht veröffentlicht werden dürfen) werden
als eigener Datensatz installiert – per eigenem Installer oder durch Entpacken in den Ordner

| OS | Ordner |
|---|---|
| Windows | `%APPDATA%\io.github.dnd-cards\datasets\<name>` |
| macOS | `~/Library/Application Support/io.github.dnd-cards/datasets/<name>` |
| Linux | `~/.local/share/io.github.dnd-cards/datasets/<name>` |

(*Data* → *Open datasets folder* öffnet ihn). Ein Datensatz hat denselben Aufbau wie `data/`
(`<sprache>/<buch>/<typ>/*.yaml`); eine optionale `dataset.json` legt den angezeigten Namen fest:

```json
{ "name": "Mein Buch", "description": "…", "version": "1.0.0" }
```

Gleiche Kartenschlüssel (`spells/feuerball`) in verschiedenen Datensätzen sind gewollt: ein Deck
funktioniert dann mit jeder Datenquelle, die diese Karten enthält.

### Aus den Sourcen bauen

Voraussetzungen: [Rust](https://rustup.rs) (stable) und die
[Tauri-Voraussetzungen](https://tauri.app/start/prerequisites/) des Betriebssystems.

```
cargo install tauri-cli --version "^2" --locked   # einmalig

cargo tauri dev                    # Desktop-App im Entwicklungsmodus starten
cargo tauri build                  # Installer bauen (landen in target/release/bundle/)
cargo run -p dnd-cards-cli -- list # Kommandozeile
cargo test --workspace             # Tests
```

Aufbau:

- `crates/dnd-cards-core` – Datenmodell, YAML-Laden, PDF-Layout
- `crates/dnd-cards-cli` – Kommandozeilenprogramm `dnd-cards`
- `src-tauri` + `ui` – Desktop-App (Tauri 2, HTML/CSS/JS ohne Build-Schritt)
- `data` – Kartendaten (YAML), `scripts` – Import-Skripte für die SRD-Daten

## Mitmachen

Ihr könnt gerne mitmachen

- Issues auf github erstellen
- PRs schicken

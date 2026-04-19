"""Interactive TUI deck builder — Textual-based full-screen terminal app."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.coordinate import Coordinate
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Input, Label

from dnd_cards.config import DEFAULT_DATA_DIR
from dnd_cards.scanner import CardRef, scan_cards

__all__ = ["DeckBuilderApp", "run_tui", "slugify"]

# ---------------------------------------------------------------------------
# Slug helper (shared with scripts/import_srd_data.py)
# ---------------------------------------------------------------------------


_UMLAUT: dict[str, str] = {
    "ä": "a", "ö": "o", "ü": "u",
    "Ä": "a", "Ö": "o", "Ü": "u",
    "ß": "ss",
}
_UMLAUT_TABLE = str.maketrans(_UMLAUT)


def slugify(name: str) -> str:
    """Lowercase slug: transliterate German umlauts, spaces->hyphens, strip specials."""
    s = name.translate(_UMLAUT_TABLE).lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return re.sub(r"-+", "-", s).strip("-")


# ---------------------------------------------------------------------------
# Pure helpers (no Textual dependency — easy to unit-test)
# ---------------------------------------------------------------------------

def _fuzzy_match(query: str, text: str) -> bool:
    """Case-insensitive subsequence match — 'feurball' matches 'Feuerball'."""
    if not query:
        return True
    q = query.lower()
    t = text.lower()
    if q in t:
        return True  # fast path: direct substring
    it = iter(t)
    return all(c in it for c in q)  # subsequence match


def _discover_languages(data_dir: Path) -> list[str]:
    """Return sorted first-level subdirectory names of data_dir (language codes)."""
    return sorted(d.name for d in data_dir.iterdir() if d.is_dir())


def _discover_types(index: dict[str, CardRef]) -> list[str]:
    """Return sorted unique card_type values from the scan index."""
    return sorted({ref.card_type for ref in index.values()})


def _load_name(path: Path) -> str:
    """Read only the `name` field from a card YAML (fast, no full validation)."""
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return str(raw.get("name", path.stem))
    return path.stem


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TuiCard:
    """In-memory representation of one card entry in the TUI."""

    key: str        # '{card_type}/{stem}' — same as scan index key
    name: str       # display name from YAML `name` field
    card_type: str  # "spells", "talents", "rules"
    lang: str       # "de", "en"
    qty: int = field(default=0)


# ---------------------------------------------------------------------------
# Save modal
# ---------------------------------------------------------------------------

class SaveModal(ModalScreen[str | None]):
    """Prompt the user for a deck name before saving."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", show=True)]

    CSS = """
    SaveModal {
        align: center middle;
    }
    #save-dialog {
        width: 60;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: tall $primary;
    }
    #save-label {
        margin-bottom: 1;
    }
    """

    def __init__(self, default_name: str) -> None:
        super().__init__()
        self._default_name = default_name

    def compose(self) -> ComposeResult:
        with Vertical(id="save-dialog"):
            yield Label(
                "Save deck as  (Enter = confirm  Escape = cancel):",
                id="save-label",
            )
            yield Input(value=self._default_name, id="save-input")

    def on_mount(self) -> None:
        self.query_one("#save-input", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else None)


# ---------------------------------------------------------------------------
# Textual app
# ---------------------------------------------------------------------------

class DeckBuilderApp(App[None]):
    """Full-screen TUI deck builder.

    All printable a-z input is routed to the card-name filter; no Input widget
    holds focus, so every other key (digits, F-keys, +/-,ctrl+s, q …) is
    handled directly by the app bindings or on_key.
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", show=True),
        Binding("q", "quit_app", "Quit", show=True),
        Binding("escape", "clear_search", "Clear search", show=False),
        Binding("plus", "increment_qty", "+", show=True, priority=True),
        Binding("minus", "decrement_qty", "-", show=False, priority=True),
    ]

    CSS = """
    #filter-label {
        dock: top;
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text;
    }
    #footer-label {
        dock: bottom;
        background: $panel;
        color: $text-muted;
        padding: 0 1;
        height: 1;
    }
    DataTable { height: 1fr; }
    """

    def __init__(
        self,
        data_dir: Path,
        deck_name: str = "",
        deck_file: Path | None = None,
    ) -> None:
        super().__init__()
        self._data_dir = data_dir
        self._deck_name = deck_name
        self._deck_file = deck_file
        self._cards: list[TuiCard] = []
        self._filtered: list[TuiCard] = []
        self._search: str = ""
        self._active_lang: str | None = None
        self._active_type: str | None = None
        self._lang_keys: dict[str, str] = {}   # e.g. {"f1": "de", "f2": "en"}
        self._type_keys: dict[str, str] = {}   # e.g. {"1": "rules", "2": "spells"}
        self._saved_path: Path | None = None
        self._save_count: int = 0

    # ------------------------------------------------------------------
    # Compose
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Label("Filter: (type a-z to search)", id="filter-label")
        yield DataTable(id="card-table", cursor_type="row")
        yield Label("", id="footer-label")
        yield Footer()

    # ------------------------------------------------------------------
    # Mount / startup
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        index = scan_cards(self._data_dir)

        # Derive language from path: data/<lang>/...
        self._cards = []
        for key, ref in sorted(index.items()):
            try:
                lang = str(ref.path.relative_to(self._data_dir).parts[0])
            except (ValueError, IndexError):
                lang = "?"
            name = _load_name(ref.path)
            self._cards.append(
                TuiCard(key=key, name=name, card_type=ref.card_type, lang=lang)
            )

        # Pre-populate quantities from existing deck file
        if self._deck_file and self._deck_file.exists():
            self._load_deck_file(self._deck_file)

        # Build filter key maps
        langs = _discover_languages(self._data_dir)
        self._lang_keys = {f"f{i + 1}": lang for i, lang in enumerate(langs[:4])}
        types = _discover_types(index)
        self._type_keys = {str(i + 1): t for i, t in enumerate(types[:9])}

        # Default language filter to first language
        if langs:
            self._active_lang = langs[0]

        # Set up DataTable columns
        table = self.query_one("#card-table", DataTable)
        table.add_columns("Name", "Type", "Qty")

        self._refresh_table()
        self._update_header()
        self._update_footer()
        # DataTable holds focus — all keys are handled at App level
        table.focus()

    def _load_deck_file(self, path: Path) -> None:
        try:
            raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return
        if not isinstance(raw, dict):
            return
        cards_raw = raw.get("cards", {})
        if not isinstance(cards_raw, dict):
            return
        qty_map: dict[str, int] = {
            str(k): int(v) for k, v in cards_raw.items()
        }
        for card in self._cards:
            if card.key in qty_map:
                card.qty = qty_map[card.key]
        if not self._deck_name and isinstance(raw.get("name"), str):
            self._deck_name = str(raw["name"])

    # ------------------------------------------------------------------
    # Filter & render
    # ------------------------------------------------------------------

    def _visible_cards(self) -> list[TuiCard]:
        result: list[TuiCard] = []
        for card in self._cards:
            if self._active_lang and card.lang != self._active_lang:
                continue
            if self._active_type and card.card_type != self._active_type:
                continue
            if self._search and not _fuzzy_match(self._search, card.name):
                continue
            result.append(card)
        return result

    def _refresh_table(self) -> None:
        table = self.query_one("#card-table", DataTable)
        table.clear()
        self._filtered = self._visible_cards()
        for card in self._filtered:
            qty_str = f"×{card.qty}" if card.qty > 0 else ""
            table.add_row(card.name, card.card_type, qty_str, key=card.key)
        if self._filtered:
            table.move_cursor(row=0)

    def _update_filter_label(self) -> None:
        label = self.query_one("#filter-label", Label)
        if self._search:
            label.update(f"Filter: {self._search}")
        else:
            label.update("Filter: (type a-z to search)")

    def _update_header(self) -> None:
        total = sum(c.qty for c in self._cards)
        name = self._deck_name or "untitled"
        self.title = f"{name} · {total} cards"

    def _update_footer(self) -> None:
        parts: list[str] = []
        for fkey, lang in self._lang_keys.items():
            marker = "●" if lang == self._active_lang else " "
            parts.append(f"{fkey.upper()}={marker}{lang}")
        for nkey, t in self._type_keys.items():
            marker = "●" if t == self._active_type else " "
            parts.append(f"{nkey}={marker}{t}")
        parts += ["+/-  qty", "ctrl+s  save", "q  quit"]
        label = self.query_one("#footer-label", Label)
        label.update("  |  ".join(parts))

    # ------------------------------------------------------------------
    # Input handling — all keys land here; only a-z go to the filter
    # ------------------------------------------------------------------

    def on_key(self, event: events.Key) -> None:
        key = event.key

        if key in self._lang_keys:
            selected = self._lang_keys[key]
            self._active_lang = None if self._active_lang == selected else selected
            self._refresh_table()
            self._update_footer()
            event.stop()
        elif key in self._type_keys:
            selected = self._type_keys[key]
            self._active_type = None if self._active_type == selected else selected
            self._refresh_table()
            self._update_footer()
            event.stop()
        elif key == "backspace":
            if self._search:
                self._search = self._search[:-1]
                self._refresh_table()
                self._update_filter_label()
            event.stop()
        elif (
            event.character is not None
            and len(event.character) == 1
            and event.character.isalpha()
            and event.character.isascii()
        ):
            self._search += event.character.lower()
            self._refresh_table()
            self._update_filter_label()
            event.stop()

    def _change_qty(self, delta: int) -> None:
        table = self.query_one("#card-table", DataTable)
        if table.cursor_row < 0 or table.cursor_row >= len(self._filtered):
            return
        card = self._filtered[table.cursor_row]
        card.qty = max(0, card.qty + delta)
        qty_str = f"×{card.qty}" if card.qty > 0 else ""
        table.update_cell_at(Coordinate(table.cursor_row, 2), qty_str)
        self._update_header()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_increment_qty(self) -> None:
        self._change_qty(+1)

    def action_decrement_qty(self) -> None:
        self._change_qty(-1)

    def action_clear_search(self) -> None:
        self._search = ""
        self._refresh_table()
        self._update_filter_label()

    def action_save(self) -> None:
        default = self._deck_name or "deck"
        self.push_screen(SaveModal(default), callback=self._on_save_name)

    def _on_save_name(self, result: str | None) -> None:
        if result is not None:
            self._deck_name = result
            self._save()
            self._update_header()

    def action_quit_app(self) -> None:
        self._quit()

    def _save(self) -> None:
        name = self._deck_name or "deck"
        if self._deck_file:
            out_path = self._deck_file
        else:
            Path("decks").mkdir(parents=True, exist_ok=True)
            out_path = Path("decks") / f"{slugify(name)}.yaml"
        data: dict[str, Any] = {
            "name": name,
            "cards": {
                card.key: card.qty
                for card in self._cards
                if card.qty > 0
            },
        }
        out_path.write_text(
            yaml.dump(data, allow_unicode=True, default_flow_style=False,
                      sort_keys=False),
            encoding="utf-8",
        )
        self._saved_path = out_path
        self._save_count = sum(card.qty for card in self._cards if card.qty > 0)

    def _quit(self) -> None:
        self.exit()

    # ------------------------------------------------------------------
    # Post-exit message
    # ------------------------------------------------------------------

    def on_unmount(self) -> None:
        if self._saved_path:
            import builtins
            builtins.print(
                f"Saved -> {self._saved_path} ({self._save_count} cards)"
            )
        else:
            import builtins
            builtins.print("Quit without saving.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_tui(
    data_dir: Path | None = None,
    deck_file: Path | None = None,
) -> None:
    """Launch the TUI deck builder."""
    resolved_data_dir = data_dir if data_dir is not None else Path(DEFAULT_DATA_DIR)
    deck_name = deck_file.stem if deck_file else ""
    app = DeckBuilderApp(
        data_dir=resolved_data_dir,
        deck_name=deck_name,
        deck_file=deck_file,
    )
    app.run()

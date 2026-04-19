"""CLI entry point — Typer app with generate, validate, list subcommands."""

import importlib.metadata
import traceback
from pathlib import Path
from typing import NoReturn, Optional

import typer

from dnd_cards.composer import compose_pdf, register_fonts
from dnd_cards.config import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR
from dnd_cards.errors import (
    CardNotFoundError,
    GenerationError,
    ValidationError,
    YamlParseError,
)
from dnd_cards.loader import load_card, load_deck
from dnd_cards.models import CardData
from dnd_cards.scanner import scan_cards

__all__ = ["app"]

app = typer.Typer(
    name="dnd-cards",
    help="Generate print-ready PDF reference cards for DnD 5.5e.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dnd-cards {importlib.metadata.version('dnd-cards')}")
        raise typer.Exit()


def _handle_dnd_error(exc: BaseException) -> NoReturn:
    """Route exception to stderr and raise typer.Exit with correct code."""
    if isinstance(exc, (YamlParseError, ValidationError, CardNotFoundError)):
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    if isinstance(exc, GenerationError):
        typer.echo(str(exc), err=True)
        raise typer.Exit(2)
    # Unexpected exception — full traceback to stderr
    typer.echo(traceback.format_exc(), err=True)
    raise typer.Exit(2)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version.",
    ),
) -> None:
    """dnd-cards — German DnD 5.5e reference card generator."""
    register_fonts()


@app.command()
def generate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Output directory for generated PDF."
    ),
) -> None:
    """Generate a print-ready PDF from a deck profile."""
    try:
        _generate_impl(deck, output_dir)
    except Exception as exc:
        _handle_dnd_error(exc)


def _generate_impl(deck: str, output_dir: Optional[str] = None) -> None:
    deck_path = Path(deck)
    card_index = scan_cards(Path(DEFAULT_DATA_DIR))
    deck_profile = load_deck(deck_path)

    cards: list[CardData] = []
    for entry in deck_profile.entries:
        if entry.card_key not in card_index:
            raise CardNotFoundError(
                f"Card not found: {entry.card_key} (deck: {deck_path})"
            )
        card = load_card(card_index[entry.card_key].path)
        cards.extend([card] * entry.quantity)

    out_dir = Path(output_dir) if output_dir else Path(DEFAULT_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{deck_path.stem}.pdf"

    compose_pdf(cards, out_path)
    typer.echo(str(out_path))


@app.command()
def validate(
    deck: str = typer.Option(..., "--deck", help="Path to deck profile YAML file."),
) -> None:
    """Validate a deck profile without generating a PDF."""
    try:
        _validate_impl(deck)
    except Exception as exc:
        _handle_dnd_error(exc)


def _validate_impl(deck: str) -> None:
    """Implementation in Story 3.2."""
    raise NotImplementedError


@app.command()
def tui(
    deck: Optional[str] = typer.Argument(
        None, help="Path to existing deck YAML to edit (optional)."
    ),
) -> None:
    """Interactively build or edit a deck YAML in a terminal UI."""
    from dnd_cards.tui import run_tui  # lazy import — avoids loading Textual at startup

    run_tui(deck_file=Path(deck) if deck else None)


@app.command(name="list")
def list_cards(
    card_type: Optional[str] = typer.Option(
        None, "--type", help="Filter by card type."
    ),
) -> None:
    """List available cards in the data store."""
    try:
        _list_cards_impl(card_type)
    except Exception as exc:
        _handle_dnd_error(exc)


def _list_cards_impl(card_type: Optional[str]) -> None:
    data_dir = Path(DEFAULT_DATA_DIR)
    if not data_dir.is_dir():
        return
    index = scan_cards(data_dir)
    entries = sorted(
        (ref.path.stem, ref.card_type)
        for ref in index.values()
        if card_type is None or ref.card_type == card_type
    )
    for stem, ct in entries:
        typer.echo(f"{stem} [{ct}]")

"""File system scanner for card data store discovery."""

from pathlib import Path
from typing import NamedTuple

__all__ = ["CardRef", "scan_cards"]


class CardRef(NamedTuple):
    """Reference to a discovered card file."""

    path: Path
    card_type: str


def scan_cards(data_dir: Path) -> dict[str, CardRef]:
    """Scan data_dir tree recursively and return card index.

    Keys are '{card_type}/{stem}' (e.g. 'spells/fireball').
    card_type is the immediate parent directory of each .yaml file.
    No YAML content is read — type is derived from directory name only.
    """
    result: dict[str, CardRef] = {}
    for yaml_file in data_dir.rglob("*.yaml"):
        card_type = yaml_file.parent.name
        key = f"{card_type}/{yaml_file.stem}"
        result[key] = CardRef(path=yaml_file, card_type=card_type)
    return result

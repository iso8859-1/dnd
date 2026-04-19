#!/usr/bin/env python
"""One-time import: split bulk SRD YAML files into individual card YAML files.

Usage (from project root):
    uv run python scripts/import_srd_data.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from dnd_cards.tui import slugify

SRD_DIR = Path("SRDs")
DATA_BASE = Path("data") / "de" / "SRD 5.2"


def _write_card(out_dir: Path, card: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{card['id']}.yaml"
    with out_path.open("w", encoding="utf-8") as fh:
        yaml.dump(card, fh, allow_unicode=True, default_flow_style=False,
                  sort_keys=False)
    print(f"  {out_path}")


def import_talents(source: Path, out_dir: Path) -> int:
    """Read a talente: bulk YAML and write one card YAML per entry."""
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    count = 0
    for entry in data["talente"]:
        card: dict[str, Any] = {
            "id": slugify(entry["name"]),
            "type": "talent",
            "template": "talent-v1",
            "name": entry["name"],
            "lang": "de",
            "description": entry["beschreibung"],
            "source_book": entry.get("Regelbuch"),
        }
        if entry.get("typ"):
            card["typ"] = entry["typ"]
        _write_card(out_dir, card)
        count += 1
    return count


def import_rules(source: Path, out_dir: Path) -> int:
    """Read a regelglossar: bulk YAML and write one card YAML per entry."""
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    count = 0
    for entry in data["regelglossar"]:
        card: dict[str, Any] = {
            "id": slugify(entry["name"]),
            "type": "rule",
            "template": "rule-v1",
            "name": entry["name"],
            "lang": "de",
            "description": entry["beschreibung"],
            "source_book": entry.get("Regelbuch"),
        }
        _write_card(out_dir, card)
        count += 1
    return count


if __name__ == "__main__":
    talents_dir = DATA_BASE / "talents"
    rules_dir = DATA_BASE / "rules"
    total = 0

    for fname in (
        "allgemeine_talente.yaml",
        "herkunftstalente.yaml",
        "kampfstiltalente.yaml",
        "epische_gabe_talente.yaml",
    ):
        print(f"Importing {fname}…")
        total += import_talents(SRD_DIR / fname, talents_dir)

    print("Importing regelglossar.yaml…")
    total += import_rules(SRD_DIR / "regelglossar.yaml", rules_dir)

    print(f"\nDone — {total} files written.")

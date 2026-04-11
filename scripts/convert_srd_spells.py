"""One-off conversion: SRDs/zauberbeschreibungen.yaml → data/spells/<slug>.yaml"""

import re
import sys
import unicodedata
from pathlib import Path

import yaml

SRC = Path("SRDs/zauberbeschreibungen.yaml")
DEST = Path("data/spells")
SOURCE_BOOK = "SRD 5.2 DE"


def slugify(text: str) -> str:
    # Replace German-specific characters before NFD decomposition
    text = text.replace("ß", "ss")
    normalized = unicodedata.normalize("NFD", text)
    ascii_only = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def parse_level(grad: str) -> int:
    if grad == "Zaubertrick":
        return 0
    m = re.match(r"(\d+)\.", grad)
    if m:
        return int(m.group(1))
    raise ValueError(f"Unknown grad value: {grad!r}")


def convert(spell: dict) -> dict:
    return {
        "id": slugify(spell["name"]),
        "type": "spell",
        "template": "spell",
        "name": spell["name"],
        "lang": "de",
        "level": parse_level(spell["grad"]),
        "school": spell["schule"],
        "casting_time": spell["zeitaufwand"],
        "range": spell["reichweite"],
        "components": spell["komponenten"],
        "duration": spell["wirkungsdauer"],
        "description": spell["beschreibung"],
        "source_book": SOURCE_BOOK,
    }


def main() -> None:
    if not SRC.exists():
        print(f"ERROR: {SRC} not found", file=sys.stderr)
        sys.exit(1)

    DEST.mkdir(parents=True, exist_ok=True)

    with SRC.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    spells = data["zauber"]
    written = 0
    skipped = 0

    for spell in spells:
        try:
            card = convert(spell)
        except (KeyError, ValueError) as exc:
            print(f"SKIP {spell.get('name', '?')}: {exc}", file=sys.stderr)
            skipped += 1
            continue

        out_path = DEST / f"{card['id']}.yaml"
        with out_path.open("w", encoding="utf-8") as f:
            yaml.dump(card, f, allow_unicode=True, sort_keys=False, width=120)
        written += 1

    print(f"Written: {written}  Skipped: {skipped}  ->  {DEST}/")


if __name__ == "__main__":
    main()

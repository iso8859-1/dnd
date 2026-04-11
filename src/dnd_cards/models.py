"""Pydantic v2 data models: CardData, DeckProfile, DeckEntry, Language."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict

__all__ = ["Language", "CardData", "DeckProfile", "DeckEntry"]


class Language(str, Enum):
    """Language codes matching data/ directory names."""

    DE = "de"
    EN = "en"


class CardData(BaseModel):
    """Parsed and validated card data from a YAML file."""

    model_config = ConfigDict(frozen=True)

    id: str
    type: str
    template: str
    name: str
    lang: Language
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    edition: Optional[str] = None
    source_book: Optional[str] = None


class DeckEntry(BaseModel):
    """A single card entry in a deck profile."""

    model_config = ConfigDict(frozen=True)

    card_key: str   # format: "{card_type}/{id}", e.g. "spells/feuerball"
    quantity: int   # ≥1


class DeckProfile(BaseModel):
    """A deck profile loaded from YAML."""

    model_config = ConfigDict(frozen=True)

    name: str
    entries: list[DeckEntry]

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
    # Spell-specific — None for talent/rule cards
    level: Optional[int] = None
    school: Optional[str] = None
    casting_time: Optional[str] = None
    range: Optional[str] = None
    components: Optional[str] = None
    duration: Optional[str] = None
    # Shared optional fields
    typ: Optional[str] = None          # talent category string
    description: str                   # required for all types
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

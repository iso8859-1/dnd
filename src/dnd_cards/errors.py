"""DndCardsError exception hierarchy."""

__all__ = [
    "DndCardsError",
    "YamlParseError",
    "ValidationError",
    "CardNotFoundError",
    "GenerationError",
]


class DndCardsError(Exception):
    """Base class for all dnd-cards errors."""


class YamlParseError(DndCardsError):
    """YAML syntax error — exit 1. Include file path and line number."""


class ValidationError(DndCardsError):
    """Schema validation error — exit 1. Include file path and field name."""


class CardNotFoundError(DndCardsError):
    """Card key not found in data store — exit 1."""


class GenerationError(DndCardsError):
    """PDF composition failure — exit 2."""

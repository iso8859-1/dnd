"""Tests for errors module."""

from dnd_cards.errors import (
    CardNotFoundError,
    DndCardsError,
    GenerationError,
    ValidationError,
    YamlParseError,
)


def test_error_hierarchy() -> None:
    assert issubclass(YamlParseError, DndCardsError)
    assert issubclass(ValidationError, DndCardsError)
    assert issubclass(CardNotFoundError, DndCardsError)
    assert issubclass(GenerationError, DndCardsError)


def test_error_instantiation_and_message() -> None:
    for cls in (YamlParseError, ValidationError, CardNotFoundError, GenerationError):
        exc = cls("test message")
        assert isinstance(exc, DndCardsError)
        assert str(exc) == "test message"

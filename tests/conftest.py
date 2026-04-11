"""Shared pytest fixtures."""

from pathlib import Path

import pytest

from dnd_cards.models import CardData, Language


@pytest.fixture
def fixture_path() -> Path:
    """Path to tests/fixtures/ directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_card_data() -> CardData:
    """A valid CardData instance for testing."""
    return CardData(
        id="fireball",
        type="spell",
        template="zauber-v1",
        name="Fireball",
        lang=Language.EN,
        level=3,
        school="Evocation",
        casting_time="1 action",
        range="150 ft",
        components="V, S, M",
        duration="Instantaneous",
        description="A bright streak flashes from your pointing finger...",
        edition="5e",
        source_book="SRD 5.1",
    )

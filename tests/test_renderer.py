"""Tests for renderer module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from dnd_cards.errors import GenerationError
from dnd_cards.models import CardData, Language
from dnd_cards.renderer import render_card


@pytest.fixture
def spell_card() -> CardData:
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
        description="A bright streak flashes from your pointing finger.",
        edition="5e",
        source_book="SRD 5.1",
    )


@pytest.fixture
def templates_dir(tmp_path: Path) -> Path:
    """Create a temp templates dir with zauber-v1.jinja2."""
    (tmp_path / "zauber-v1.jinja2").write_text(
        "{{ name }} Level {{ level }} {{ school }}", encoding="utf-8"
    )
    return tmp_path


def test_render_card_returns_dict(spell_card: CardData, templates_dir: Path) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", templates_dir):
        result = render_card(spell_card, "zauber-v1")
    assert isinstance(result, dict)


def test_render_card_context_has_correct_values(
    spell_card: CardData, templates_dir: Path
) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", templates_dir):
        ctx = render_card(spell_card, "zauber-v1")
    assert ctx["name"] == "Fireball"
    assert ctx["level"] == 3
    assert ctx["school"] == "Evocation"
    assert ctx["casting_time"] == "1 action"
    assert ctx["range"] == "150 ft"
    assert ctx["components"] == "V, S, M"
    assert ctx["duration"] == "Instantaneous"
    assert ctx["description"] == "A bright streak flashes from your pointing finger."
    assert ctx["edition"] == "5e"
    assert ctx["source_book"] == "SRD 5.1"
    assert ctx["lang"] == "en"


def test_render_card_preserves_german_text(tmp_path: Path) -> None:
    (tmp_path / "zauber-v1.jinja2").write_text("{{ name }}", encoding="utf-8")
    german_card = CardData(
        id="feuerball",
        type="spell",
        template="zauber-v1",
        name="Feuerball — Zerstörungszauber",
        lang=Language.DE,
        level=3,
        school="Verwandlung",
        casting_time="1 Aktion",
        range="45 m",
        components="V, S, M",
        duration="Sofort",
        description="Ein heller Streifen schießt aus deinem Finger. Äther und Ödland.",
    )
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        ctx = render_card(german_card, "zauber-v1")
    # Characters must NOT be HTML-escaped (autoescape=False)
    assert "Feuerball — Zerstörungszauber" in ctx["name"]
    assert "Äther" in ctx["description"]
    assert "schießt" in ctx["description"]
    assert ctx["lang"] == "de"


def test_render_card_missing_template_raises_generation_error(
    spell_card: CardData, tmp_path: Path
) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        with pytest.raises(GenerationError) as exc_info:
            render_card(spell_card, "nonexistent-template")
    assert "nonexistent-template" in str(exc_info.value)


def test_render_card_contains_all_required_fields(
    spell_card: CardData, templates_dir: Path
) -> None:
    with patch("dnd_cards.renderer._TEMPLATES_DIR", templates_dir):
        ctx = render_card(spell_card, "zauber-v1")
    required = {
        "id", "type", "template", "name", "lang", "level", "school",
        "casting_time", "range", "components", "duration", "description",
        "edition", "source_book",
    }
    assert required.issubset(ctx.keys())


def test_render_card_talent_context(tmp_path: Path) -> None:
    """render_card for a talent card includes typ; spell fields are None."""
    (tmp_path / "talent-v1.jinja2").write_text(
        "{{ name }}\n{{ description }}\n", encoding="utf-8"
    )
    card = CardData(
        id="ringer",
        type="talent",
        template="talent-v1",
        name="Ringer",
        lang=Language.DE,
        description="Vorzüge.",
        typ="Allgemeines Talent",
    )
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        ctx = render_card(card, "talent-v1")

    assert ctx["typ"] == "Allgemeines Talent"
    assert ctx["level"] is None
    assert ctx["school"] is None
    assert ctx["casting_time"] is None
    assert ctx["range"] is None
    assert ctx["components"] is None
    assert ctx["duration"] is None


def test_render_card_optional_fields_none_when_absent(tmp_path: Path) -> None:
    (tmp_path / "zauber-v1.jinja2").write_text("{{ name }}", encoding="utf-8")
    minimal_card = CardData(
        id="shield",
        type="spell",
        template="zauber-v1",
        name="Shield",
        lang=Language.EN,
        level=1,
        school="Abjuration",
        casting_time="1 reaction",
        range="Self",
        components="V, S",
        duration="1 round",
        description="A shimmering field appears.",
    )
    with patch("dnd_cards.renderer._TEMPLATES_DIR", tmp_path):
        ctx = render_card(minimal_card, "zauber-v1")
    assert ctx["edition"] is None
    assert ctx["source_book"] is None

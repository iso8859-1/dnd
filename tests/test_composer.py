"""Tests for composer module."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dnd_cards.composer import compose_pdf, register_fonts
from dnd_cards.models import CardData, Language


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
        description="A bright streak flashes from your pointing finger to a point.",
    )


def _fake_ctx(card: CardData, template_name: str) -> dict[str, object]:  # noqa: ARG001
    return {
        "id": card.id,
        "type": card.type,
        "template": card.template,
        "name": card.name,
        "lang": card.lang.value,
        "level": card.level,
        "school": card.school,
        "casting_time": card.casting_time,
        "range": card.range,
        "components": card.components,
        "duration": card.duration,
        "typ": card.typ,
        "description": card.description,
        "edition": card.edition,
        "source_book": card.source_book,
    }


def test_register_fonts_does_not_raise() -> None:
    register_fonts()  # no .ttf files present — must not raise


def test_compose_pdf_single_card_produces_output(spell_card: CardData) -> None:
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card], buf)
    assert buf.tell() > 0, "PDF buffer should be non-empty after save()"


def test_compose_pdf_four_cards_no_error(spell_card: CardData) -> None:
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card] * 4, buf)
    assert buf.tell() > 0


def test_compose_pdf_five_cards_produces_larger_output(spell_card: CardData) -> None:
    """5 cards spans 2 pages — output should be larger than 4-card single page."""
    buf4 = BytesIO()
    buf5 = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card] * 4, buf4)
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card] * 5, buf5)
    assert buf5.tell() > buf4.tell(), "5-card PDF should be larger than 4-card PDF"


def test_compose_pdf_empty_list_no_error() -> None:
    buf = BytesIO()
    compose_pdf([], buf)
    assert buf.tell() > 0  # ReportLab still writes PDF header/trailer


def test_compose_pdf_calls_render_card_per_card(spell_card: CardData) -> None:
    buf = BytesIO()
    mock_render = MagicMock(side_effect=_fake_ctx)
    with patch("dnd_cards.composer.render_card", mock_render):
        compose_pdf([spell_card, spell_card, spell_card], buf)
    assert mock_render.call_count == 3


def test_compose_pdf_uses_card_template_name(spell_card: CardData) -> None:
    buf = BytesIO()
    mock_render = MagicMock(side_effect=_fake_ctx)
    with patch("dnd_cards.composer.render_card", mock_render):
        compose_pdf([spell_card], buf)
    mock_render.assert_called_once_with(spell_card, "zauber-v1")


def test_compose_pdf_path_output(spell_card: CardData, tmp_path: Path) -> None:
    out = tmp_path / "test.pdf"
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([spell_card], out)
    assert out.exists()
    assert out.stat().st_size > 0


def test_compose_pdf_talent_card_no_error(tmp_path: Path) -> None:
    """Talent card (no spell fields) renders without error."""
    talent = CardData(
        id="ringer",
        type="talent",
        template="talent-v1",
        name="Ringer",
        lang=Language.EN,
        description="Du erhältst folgende Vorzüge.",
        typ="Allgemeines Talent",
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([talent], buf)
    assert buf.tell() > 0


def test_compose_pdf_rule_card_no_error(tmp_path: Path) -> None:
    """Rule card renders without error."""
    rule = CardData(
        id="abenteuer",
        type="rule",
        template="rule-v1",
        name="Abenteuer",
        lang=Language.EN,
        description="Ein Abenteuer ist eine Serie von Begegnungen.",
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([rule], buf)
    assert buf.tell() > 0

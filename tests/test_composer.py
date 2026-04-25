"""Tests for composer module."""

from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from dnd_cards.composer import compose_pdf, compose_pdf_duplex, register_fonts
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
        "class_name": card.class_name,
        "subclass": card.subclass,
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


def test_compose_pdf_class_feature_no_error(tmp_path: Path) -> None:
    """Class feature card renders without error."""
    feat = CardData(
        id="barbar-kampfrausch",
        type="class_feature",
        template="class-feature-v1",
        name="Kampfrausch",
        lang=Language.DE,
        description="Eine Urmacht namens Kampfrausch...",
        class_name="Barbar",
        level=1,
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([feat], buf)
    assert buf.tell() > 0


def test_compose_pdf_class_feature_with_subclass_no_error(tmp_path: Path) -> None:
    """Class feature with subclass renders without error."""
    feat = CardData(
        id="barbar-raserei",
        type="class_feature",
        template="class-feature-v1",
        name="Raserei",
        lang=Language.DE,
        description="...",
        class_name="Barbar",
        level=3,
        subclass="Pfad des Berserkers",
    )
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf([feat], buf)
    assert buf.tell() > 0


# ── Story 4.5: compose_pdf_duplex tests ─────────────────────────────────────


def test_compose_pdf_duplex_produces_output(spell_card: CardData) -> None:
    """compose_pdf_duplex writes bytes to output for a single card."""
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf_duplex([spell_card], buf)
    assert buf.tell() > 0


def test_compose_pdf_duplex_back_mirrors_columns(spell_card: CardData) -> None:
    """Back page draws each card's back at the horizontally mirrored column position."""
    cards = [spell_card, spell_card, spell_card]  # 3 cards fill row 0

    front_xs: list[float] = []
    back_xs: list[float] = []

    def capture_front(c: Any, ctx: Any, x: float, y: float, w: float, h: float) -> None:
        front_xs.append(x)

    def capture_back(c: Any, ctx: Any, x: float, y: float, w: float, h: float) -> None:
        back_xs.append(x)

    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx), \
         patch("dnd_cards.composer._draw_front_face", side_effect=capture_front), \
         patch("dnd_cards.composer._draw_back_face", side_effect=capture_back):
        compose_pdf_duplex(cards, BytesIO())

    assert len(front_xs) == 3
    assert len(back_xs) == 3
    # col 0 front → col 2 back; col 1 stays; col 2 front → col 0 back
    assert back_xs[0] == pytest.approx(front_xs[2])
    assert back_xs[1] == pytest.approx(front_xs[1])
    assert back_xs[2] == pytest.approx(front_xs[0])


def test_compose_pdf_duplex_multi_group_no_error(spell_card: CardData) -> None:
    """10 cards (> 9 per page) generates output without error."""
    buf = BytesIO()
    with patch("dnd_cards.composer.render_card", side_effect=_fake_ctx):
        compose_pdf_duplex([spell_card] * 10, buf)
    assert buf.tell() > 0

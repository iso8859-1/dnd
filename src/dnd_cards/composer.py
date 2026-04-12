"""ReportLab PDF layout: A4 landscape 4×1 grid of portrait 63×176mm fold-strips."""

import importlib.resources
import math
from io import BytesIO
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

from dnd_cards.config import (
    CARD_CORNER_RADIUS_MM,
    CARD_FOLDED_HEIGHT_MM,
    CARD_GAP_MM,
    CARD_STRIP_HEIGHT_MM,
    CARD_STRIP_WIDTH_MM,
    CARDS_PER_ROW,
)
from dnd_cards.models import CardData
from dnd_cards.renderer import render_card

__all__ = ["register_fonts", "compose_pdf"]

_MM_TO_PT: float = 72.0 / 25.4
_CARDS_PER_PAGE: int = CARDS_PER_ROW  # 4 strips per A4 landscape page

# Design tokens
_VIOLET: tuple[float, float, float] = (0.75, 0.62, 0.85)  # pastel violet
_HEADER_MM: float = 7.5   # header band height
_BORDER_PT: float = 2.0   # border stroke width

# Approximate characters per line inside usable strip width (63mm − 2×3mm padding)
_WRAP_7PT: int = 40
_WRAP_6PT: int = 48

# Field rows drawn in the front-face content area
_FIELDS: list[tuple[str, str]] = [
    ("Zeit", "casting_time"),
    ("Reichweite", "range"),
    ("Komp.", "components"),
    ("Dauer", "duration"),
]


def _mm(mm: float) -> float:
    """Convert millimetres to ReportLab points."""
    return mm * _MM_TO_PT


def _wrap(text: str, max_chars: int) -> list[str]:
    """Split text into lines of at most max_chars by breaking on word boundaries."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def register_fonts() -> None:
    """Register custom TTF fonts from src/dnd_cards/assets/fonts/.

    No-op if no .ttf files are present — built-in Helvetica is used as fallback.
    """
    try:
        fonts_pkg = importlib.resources.files("dnd_cards.assets.fonts")
        for item in fonts_pkg.iterdir():
            if item.name.endswith(".ttf"):
                pdfmetrics.registerFont(TTFont(item.name[:-4], str(item)))
    except Exception:  # noqa: BLE001
        pass  # No custom fonts; Helvetica fallback in use


def compose_pdf(cards: list[CardData], output_path: Path | BytesIO) -> None:
    """Compose a print-ready PDF from a list of CardData.

    Strips are 63×176mm portrait, arranged 4 per A4 landscape page with 5mm gaps.
    Each half of the strip has its own rounded border so both ends of the folded
    card have rounded corners.  Fold guide at 88mm marks the horizontal fold axis.
    """
    dest: Any = output_path if isinstance(output_path, BytesIO) else str(output_path)
    page_size = landscape(A4)
    c = rl_canvas.Canvas(dest, pagesize=page_size)

    page_w, page_h = page_size
    strip_w = _mm(CARD_STRIP_WIDTH_MM)    # 178.58 pt
    strip_h = _mm(CARD_STRIP_HEIGHT_MM)   # 498.90 pt
    gap = _mm(CARD_GAP_MM)               # 14.17 pt

    total_w = _CARDS_PER_PAGE * strip_w + (_CARDS_PER_PAGE - 1) * gap
    x_origin = (page_w - total_w) / 2
    y_origin = (page_h - strip_h) / 2

    try:
        for i, card in enumerate(cards):
            page_pos = i % _CARDS_PER_PAGE
            if i > 0 and page_pos == 0:
                c.showPage()
            x = x_origin + page_pos * (strip_w + gap)
            ctx = render_card(card, card.template)
            _draw_strip(c, ctx, x, y_origin, strip_w, strip_h)
    finally:
        c.save()


# ── Drawing helpers ────────────────────────────────────────────────────────────

def _fill_header(
    c: Any, x: float, y_top: float, w: float, h: float, r: float
) -> None:
    """Fill a header band in pastel violet with rounded top corners.

    The bottom edge is kept straight by overdrawing the rounded bottom corners
    of the roundRect with a plain rect of height r.
    """
    rv, gv, bv = _VIOLET
    c.setFillColorRGB(rv, gv, bv)
    # Rounded rect gives rounded corners on all 4 sides of the band
    c.roundRect(x, y_top - h, w, h, r, stroke=0, fill=1)
    # Fill in the rounded BOTTOM corners → straight bottom edge
    c.rect(x, y_top - h, w, r, stroke=0, fill=1)


def _half_border(
    c: Any, x: float, y: float, w: float, h: float, r: float
) -> None:
    """Draw the 2pt pastel-violet rounded border for one card half."""
    rv, gv, bv = _VIOLET
    c.setLineWidth(_BORDER_PT)
    c.setStrokeColorRGB(rv, gv, bv)
    c.roundRect(x, y, w, h, r, stroke=1, fill=0)


def _draw_sparkle(c: Any, cx: float, cy: float, r: float) -> None:
    """Draw a 4-pointed star in pastel violet at (cx, cy) with outer radius r."""
    rv, gv, bv = _VIOLET
    c.setFillColorRGB(rv, gv, bv)
    p = c.beginPath()
    inner = r * 0.38
    for i in range(8):
        angle = math.pi / 4 * i - math.pi / 2
        radius = r if i % 2 == 0 else inner
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        if i == 0:
            p.moveTo(px, py)
        else:
            p.lineTo(px, py)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def _draw_spellbook_icon(c: Any, cx: float, cy: float, size: float) -> None:
    """Draw a stylised spellbook in pastel violet, centred at (cx, cy)."""
    rv, gv, bv = _VIOLET
    dv = rv * 0.72, gv * 0.72, bv * 0.72  # darker shade for spine / outline

    bw = size * 0.68
    bh = size * 0.82
    bx = cx - bw / 2
    by = cy - bh / 2
    spine_w = bw * 0.22

    # Spine (slightly darker fill)
    c.setFillColorRGB(*dv)
    c.rect(bx, by, spine_w, bh, stroke=0, fill=1)

    # Book cover fill
    c.setFillColorRGB(rv, gv, bv)
    c.rect(bx + spine_w, by, bw - spine_w, bh, stroke=0, fill=1)

    # Outline
    c.setLineWidth(1.2)
    c.setStrokeColorRGB(*dv)
    c.roundRect(bx, by, bw, bh, size * 0.05, stroke=1, fill=0)

    # Horizontal page lines (white) on cover face
    c.setStrokeColorRGB(1.0, 1.0, 1.0)
    c.setLineWidth(0.8)
    lx0 = bx + spine_w + bw * 0.07
    lx1 = bx + bw - bw * 0.07
    for frac in (0.30, 0.50, 0.70):
        py = by + bh * frac
        c.line(lx0, py, lx1, py)

    # Sparkle above book
    _draw_sparkle(c, cx, by + bh + size * 0.20, size * 0.15)


# ── Main strip drawing ─────────────────────────────────────────────────────────

def _draw_strip(
    c: Any, ctx: dict[str, Any], x: float, y: float, w: float, h: float
) -> None:
    """Draw both card faces onto the portrait strip.

    Top half    (y+fold_h → y+h): front face — violet header with title,
                                   then spell fields, then description.
    Bottom half (y → y+fold_h):   back face — drawn rotated 180° so it
                                   reads correctly after a forward fold.
                                   Contains a matching violet header and a
                                   centred spellbook icon.

    Two separate rounded borders (one per half) ensure all four corners of
    the folded card are rounded after the plotter cuts each half.

    Back-face rotation logic:
      translate(x+w, y+fold_h) + rotate(180°) maps local (lx, ly) to
      page (x+w-lx, y+fold_h-ly).  drawString at local (pad, fold_h-offset)
      places text at page (x+w-pad, y+offset); the text extends page-leftward
      which, after the forward fold's left-right mirror, reads left-to-right.
    """
    fold_h = _mm(CARD_FOLDED_HEIGHT_MM)   # 249.45 pt
    r = _mm(CARD_CORNER_RADIUS_MM)
    pad = _mm(3)
    header_h = _mm(_HEADER_MM)            # ≈ 21.26 pt
    line7 = 11.0                          # line height for 7 pt text
    line6 = 8.0                           # line height for 6 pt text

    level_school = f"Stufe {ctx['level']} \u00b7 {ctx['school']}"

    # ── Front face ─────────────────────────────────────────────────────────────
    front_top = y + h
    front_bottom = y + fold_h

    _fill_header(c, x, front_top, w, header_h, r)
    _half_border(c, x, front_bottom, w, fold_h, r)

    # Title — white text centred vertically in header
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + pad, front_top - header_h / 2 - 3, str(ctx["name"]))

    # Content fields — black text below header
    c.setFillColorRGB(0.0, 0.0, 0.0)
    line_y = front_top - header_h
    c.setFont("Helvetica", 7)
    line_y -= 10
    c.drawString(x + pad, line_y, level_school)

    for label, key in _FIELDS:
        for line in _wrap(f"{label}: {ctx[key]}", _WRAP_7PT):
            line_y -= line7
            if line_y < front_bottom + 4:
                break
            c.drawString(x + pad, line_y, line)

    c.setFont("Helvetica", 6)
    line_y -= 6
    for dl in _wrap(str(ctx["description"]), _WRAP_6PT):
        line_y -= line6
        if line_y < front_bottom + 4:
            break
        c.drawString(x + pad, line_y, dl)

    # ── Fold guide ─────────────────────────────────────────────────────────────
    c.setLineWidth(0.25)
    c.setDash(3, 3)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.line(x, y + fold_h, x + w, y + fold_h)
    c.setDash()
    c.setStrokeColorRGB(0.0, 0.0, 0.0)

    # ── Back face (rotated 180°, anchored at physical bottom of strip) ──────────
    # In local coords after translate+rotate:
    #   "top" of back face (after fold) = local y = fold_h  → page y = y
    #   "bottom" of back face           = local y = 0       → page y = y+fold_h
    c.saveState()
    c.translate(x + w, y + fold_h)
    c.rotate(180)

    _fill_header(c, 0.0, fold_h, w, header_h, r)
    _half_border(c, 0.0, 0.0, w, fold_h, r)

    # Title in back header
    c.setFillColorRGB(1.0, 1.0, 1.0)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(pad, fold_h - header_h / 2 - 3, str(ctx["name"]))

    # Spellbook icon centred in the back content area
    _draw_spellbook_icon(c, w / 2, (fold_h - header_h) / 2, _mm(22))

    c.restoreState()

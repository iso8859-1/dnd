# Deferred Work

## Deferred from: code review of 1-1-project-scaffold-and-cli-entry-point (2026-04-11)

- `Optional[str]` legacy typing form in Python 3.11+ codebase — style, switch to `str | None` when ruff UP rules are enabled
- `DeckEntry.quantity` has no `ge=1` Pydantic constraint despite comment saying ≥1 — add `Field(ge=1)` in Story 3.x validators pass
- `DeckProfile.entries` field name doesn't match fixture `cards:` key — YAML alias or field rename needed before `load_deck` is implemented in Story 2.1
- `register_fonts()` called on every command including `list` which needs no fonts — consider lazy init or call only in commands that use the PDF canvas
- `load_card` only surfaces first Pydantic validation error — collect all errors and raise together for better UX
- Cross-language key collision in scanner (`en/spells/fireball` and `de/spells/fireball` both produce key `spells/fireball`) — documented known gap, address in later epic when multi-language support is formalized
- Grid layout constants resolved 2026-04-12: strip is 176mm×63mm (landscape on A4), 1×4 grid = 4 cards/page. Magic card 63×88mm, fold at 88mm. config.py updated.

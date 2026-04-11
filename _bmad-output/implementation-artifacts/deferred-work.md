# Deferred Work

## Deferred from: code review of 1-1-project-scaffold-and-cli-entry-point (2026-04-11)

- `Optional[str]` legacy typing form in Python 3.11+ codebase — style, switch to `str | None` when ruff UP rules are enabled
- `DeckEntry.quantity` has no `ge=1` Pydantic constraint despite comment saying ≥1 — add `Field(ge=1)` in Story 3.x validators pass
- `DeckProfile.entries` field name doesn't match fixture `cards:` key — YAML alias or field rename needed before `load_deck` is implemented in Story 2.1
- `register_fonts()` called on every command including `list` which needs no fonts — consider lazy init or call only in commands that use the PDF canvas
- `load_card` only surfaces first Pydantic validation error — collect all errors and raise together for better UX
- Cross-language key collision in scanner (`en/spells/fireball` and `de/spells/fireball` both produce key `spells/fireball`) — documented known gap, address in later epic when multi-language support is formalized
- Grid layout constants don't fit A4 (2×126mm=252mm > 210mm; 4×88mm=352mm > 297mm) — resolve actual strip dimensions and page grid when implementing PDF composer in Story 2.3

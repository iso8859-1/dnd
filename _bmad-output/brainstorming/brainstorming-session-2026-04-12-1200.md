---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'TUI for interactive deck YAML building inside the dnd-cards CLI'
session_goals: 'Expand feature spec, discover interaction patterns, explore UX beyond the minimum'
selected_approach: 'ai-recommended'
techniques_used: ['SCAMPER Method', 'Alien Anthropologist', 'Reverse Brainstorming']
ideas_generated: [19]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Tobias
**Date:** 2026-04-12

## Session Overview

**Topic:** TUI for interactive deck YAML building inside the dnd-cards CLI
**Goals:** Expand feature spec, discover interaction patterns, explore UX beyond the minimum

### Session Setup

Minimum spec given: card list filterable by name, `+`/`−` for quantity, output is deck YAML.
Goal: discover interaction patterns and features beyond the stated minimum.

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Concrete product design with a defined minimum spec needing enrichment.

**Recommended Techniques:**
- **SCAMPER Method:** Systematically enrich the stated feature set through 7 lenses
- **Alien Anthropologist:** Question assumptions about what a deck builder UX should feel like
- **Reverse Brainstorming:** Stress-test through inversion to surface failure modes

## Technique Execution Results

### Key Design Decisions (User Confirmed)

- `+`/`−` sufficient for quantity — no alternative input needed
- Language filter = session-level (F-keys); type filter = query-level (number keys)
- Filter key bindings derived from directory structure at runtime — no hardcoding
- Cursor stays in catalog (Option A) — deck panel is passive read-out
- Deck summary panel eliminated — counts live inline in catalog rows
- Sort order irrelevant — name search is fast enough for 500+ cards
- Core usage pattern: hold PHB, type card name, hit `+` → transcription-first design

## Idea Inventory (19 ideas)

### Theme 1 — The Core Loop

**[Philosophy #1]**: Transcription-First Design
_Concept:_ The user already knows what they want from the PHB. The TUI is a fast transcription interface, not a discovery tool. The optimal flow is: open → type 3 chars → `+` → repeat. Everything optimises for confirmation speed.
_Novelty:_ Most deck builders optimise for browsing. This one optimises for the user whose mental model is already loaded.

**[Navigation #5]**: Search-First Focus
_Concept:_ Search field focused on launch — no click or tab required. Every keystroke immediately filters. `Esc` clears search and resets list.
_Novelty:_ Zero-friction entry into the core loop.

**[Navigation #6]**: Auto-Select Top Match
_Concept:_ First result auto-highlighted as you type. If search is specific enough for one result, `+` adds it immediately. Search clears after `+` — ready for next card.
_Novelty:_ Type → `+` → clear in under a second per card.

**[Search #1]**: Fuzzy Matching
_Concept:_ fzf-style fuzzy search — "feurball" still surfaces "Feuerball". Typos are noise, intent is signal.
_Novelty:_ PHB-in-hand means half-reading — typos are inevitable. Fuzzy matching makes them irrelevant.

**[Interaction #2]**: Tactile Confirmation Flash
_Concept:_ Row briefly highlights (inverted colour, one frame) when `+` fires. Visual "click" confirming the action registered.
_Novelty:_ Feedback that matches the physical sensation of picking up a card.

**[Interaction #1]**: Command-Palette Mode (`--fast`)
_Concept:_ No list visible on launch — just a search prompt. Type, get matches in a small dropdown, `+` to add, search clears. Pure transcription with zero visual noise.
_Novelty:_ For experienced users who never browse, faster than any list-based UI.

### Theme 2 — Filter & Navigation

**[Navigation #1]**: Directory-Driven Filter Keys
_Concept:_ On startup, scan `data/` tree: first-level subdirs → language slots (F1=de, F2=en…), third-level → type slots (1=rules, 2=spells, 3=talents…). Add a new type by creating a folder — TUI needs zero changes.
_Novelty:_ The filesystem is the configuration.

**[Navigation #2]**: Live Key Legend
_Concept:_ Footer bar always shows current bindings derived from the scan: `F1 de  F2 en  |  1 rules  2 spells  3 talents  |  +/−  qty  |  type to filter`. Updates automatically when new dirs appear.
_Novelty:_ Self-documenting UI — the legend is generated, not written.

**[Navigation #3]**: Sticky Session Filters
_Concept:_ Language is session-level — chosen once, stable for the session. Type is query-level — fast to switch but still one keypress. Name search is the only ephemeral filter.
_Novelty:_ Matches actual usage: you build a German spell deck in one sitting.

**[Navigation #4]**: Persisted Language Default
_Concept:_ On first run, prompt once for default language. Write to `~/.config/dnd-cards/tui.yaml`. Subsequent runs skip the question. Override with F-key during session.
_Novelty:_ Zero friction for the common case after first use.

**[Search #2]**: No-Results Diagnosis
_Concept:_ "No results" shows why: `No spells matching "ringer" — found 1 talent`. One keypress jumps to it.
_Novelty:_ TUI diagnoses the miss rather than just reporting it.

**[Search #3]**: Search on `name` Field
_Concept:_ Search matches on the `name` field in the YAML, not the filename. The slug is invisible to the user.
_Novelty:_ Filename is an implementation detail, never a user-facing concept.

### Theme 3 — Layout

**[Layout #3]**: Single-Panel Full-Width Catalog
_Concept:_ Entire terminal width is the card list. Each row: `card name ·····×3` — name left-aligned, quantity right-aligned, blank when 0. Header shows deck name + total card count.
_Novelty:_ No split, no focus management, no panel borders. Maximum rows visible.

**[Layout #2]**: Inline Count Badge
_Concept:_ Each row shows right-aligned quantity: blank if unselected, `×2` if added twice. Deck composition visible without any secondary panel.
_Novelty:_ The catalog is the deck editor.

~~**[Eliminated #1]**: Sheet/page count preview — too much detail~~
~~**[Eliminated #2]**: Right deck-summary panel — redundant with inline counts~~

### Theme 4 — Deck Lifecycle

**[Workflow #6]**: Inline Deck Naming
_Concept:_ If no filename given (`dnd tui` with no arg), prompt for deck name on launch. Output writes to `decks/{slug}.yaml` automatically.
_Novelty:_ Deck is named before it's built — sets intent for the session.

**[Workflow #5]**: Exit Confirmation with Path
_Concept:_ On save/quit, one-line confirmation: `Saved → decks/feuerball-deck.yaml (12 cards)`. Then exit.
_Novelty:_ Closes the feedback loop that every silent file-write leaves open.

**[Workflow #2]**: Unsaved Changes Indicator
_Concept:_ `●` before deck name in header when in-memory state differs from file on disk.
_Novelty:_ Prevents "did I save that?" anxiety.

**[Workflow #1]**: Load-and-Edit Mode
_Concept:_ `dnd tui decks/my-deck.yaml` opens TUI with that deck's quantities pre-populated in catalog badges. Save overwrites; exit prompts for name if deck is unnamed.
_Novelty:_ TUI becomes a deck editor, not just a deck builder.

### Theme 5 — Power Features (later)

**[Workflow #3]**: Deck Preview Mode
_Concept:_ `dnd tui --preview decks/x.yaml` opens read-only — shows deck composition and counts. Zero interaction.
_Novelty:_ Same tool, zero-cost second use case.

**[Workflow #4]**: Deck Diff
_Concept:_ `dnd tui decks/v1.yaml decks/v2.yaml` shows cards added, removed, quantity changes between two versions.
_Novelty:_ Turns saved YAMLs into an inspectable version history.

**[Workflow #7]**: Not-Found Escape Hatch
_Concept:_ When search finds nothing: `Card not found. Create stub? (y/n)`. Writes minimal YAML, opens `$EDITOR`, returns to TUI on save.
_Novelty:_ Turns a dead end into a data contribution workflow.

## Idea Organisation and Prioritisation

**MVP — build this first:**
Search-First Focus · Auto-Select Top Match · Fuzzy Matching · Directory-Driven Filters · Single-Panel + Inline Counts · Inline Deck Naming · Exit Confirmation · Live Key Legend

**v1.1 — low effort, high polish:**
Persisted Language Default · Unsaved Changes Indicator · Load-and-Edit Mode · No-results Diagnosis · Tactile Confirmation Flash

**Later / opt-in:**
Command-Palette `--fast` · Deck Preview · Deck Diff · Not-Found Stub Creator

## Session Summary

19 ideas across 3 techniques. The central breakthrough was the **Transcription-First Design** principle — the user arrives with the PHB already read, the TUI's only job is to keep up. This reframes every layout and interaction decision: single panel, search-first focus, fuzzy match, auto-select. The directory-driven filter system was the other key insight: let the filesystem be the config.

Next step: story `5-1-deck-builder-tui`.

---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'DnD 5.5e German spell card printing app'
session_goals: 'Explore features, UX, technical approaches, and future extensions for a German DnD 5.5e card printing application'
selected_approach: 'ai-recommended'
techniques_used: ['SCAMPER', 'What If Scenarios', 'Cross-Pollination']
ideas_generated: [20]
context_file: ''
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Facilitator:** Tobias
**Date:** 2026-04-10

## Session Overview

**Topic:** DnD 5.5e German spell card printing app
**Goals:** Explore features, UX, technical approaches, and future extensions for a German DnD 5.5e card printing application

### Session Setup

User wants to build a CLI/desktop tool that:
- Contains all DnD 5.5e spells with German text (manually entered from physical books)
- Allows selection and printing of spell cards for players
- Designed so players can use the cards at the table instead of consulting the Spielerhandbuch
- Output: A4 PDF with crop marks for plotter cutting and lamination
- Future extension: condition cards, feat cards, rules reminder cards, DM reference cards

### Key Constraints
- Personal use only — Ulisses Spiele license uncertainty means no data distribution
- CLI-first tool, preparation-phase use (character creation / level-up), not session-time
- No OCR, no double-sided printing — fold-and-laminate approach
- Gradual data entry as characters grow, not upfront bulk entry

---

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** Concrete product design challenge with clear core function and extensibility goals

**Recommended Techniques:**
- **SCAMPER:** Systematic feature landscape via 7 creative lenses
- **What If Scenarios:** Break constraints, explore unexpected directions
- **Cross-Pollination:** Borrow proven patterns from adjacent domains

---

## Idea Inventory

### SCAMPER — Substitute

**[SCAMPER-S #1]**: Laminate-Ready Format
*Concept*: Cards designed to print on standard paper sizes that survive lamination — clear layout margins, no bleed-critical elements. Players annotate with wet-erase markers on laminated surface.
*Novelty*: The card becomes a reusable physical token, not just a reference.

**[SCAMPER-S #2]**: Per-Spell-Preparation Copies
*Concept*: Print multiple copies of the same spell card — one per prepared slot. Physical copies on the table represent prepared spells; crossing one out marks it expended.
*Novelty*: The card stack is the spell tracking system. No separate tracker needed.

**[SCAMPER-S #3]**: Icons as Visual Shorthand, Text Primary
*Concept*: Standardized icons (damage type, casting time, concentration, ritual) as quick-scan glyphs above the German rules text.
*Novelty*: Utility symbols only — no illustration skill required.

**[SCAMPER-S #4]**: Class-Driven Spell Filtering
*Concept*: Filter the full spell list by class so a player sees only relevant spells, further filterable by level/school.
*Novelty*: Reduces 300+ spells to ~30-60 relevant ones per character.

**[SCAMPER-S #5]**: Preparation-Phase Workflow
*Concept*: App is a "print session" tool used during character creation or level-up, not at the table. Output is the physical artifact.
*Novelty*: Removes real-time performance pressure; enables richer print/layout options.

**[SCAMPER-S #6]**: Hybrid Data Model — Curated + User-Entered
*Concept*: App ships with whatever spells can be populated, plus a template-based entry form for missing spells or homebrew.
*Novelty*: User-extensible without touching code.

### SCAMPER — Combine

**[SCAMPER-C #1]**: Multi-Template Card System
*Concept*: Each card type (Zauber, Zustand, Talent, Regelreferenz) has its own template with type-specific fields.
*Novelty*: Adding a new card type = defining a new template, not rebuilding the app.

**[SCAMPER-C #2]**: Visual Identity by Card Type
*Concept*: Distinct border color/pattern per card type. Instantly identifiable in a mixed deck.
*Novelty*: Players build a color-coded physical reference deck.

**[SCAMPER-C #3]**: Rules Reminder Cards
*Concept*: Short-form cards for frequently misremembered rules — grappling, cover, opportunity attacks, action economy, death saves.
*Novelty*: Solves "we always forget how grappling works" without opening a book.

### SCAMPER — Adapt

**[SCAMPER-A #1]**: PDF-First Output with Print Marks
*Concept*: Multi-page A4 PDF with cards in 2×4 grid, crop marks for plotter. 8 cards per page.
*Novelty*: Consistent layout across any printer; plotter-ready.

**[SCAMPER-A #2]**: Saved Character Print Profiles (Deck Files)
*Concept*: Named deck files per character. At level-up, open the profile, add new spells, regenerate PDF.
*Novelty*: Never re-select from scratch across sessions.

**[SCAMPER-A #3]**: Desktop App with Local Data Store
*Concept*: All card data in local files (YAML/JSON). No internet, no account, no cloud.
*Novelty*: Preparation-phase tool that works offline, data stays private.

### SCAMPER — Modify

**[SCAMPER-M #1]**: Fold-and-Laminate Two-Sided Card
*Concept*: Each card prints as a double-width strip (126×88mm). Fold in half, laminate. Front = key stats, back = full German rules text. No duplex printer needed.
*Novelty*: Solves the home-printer double-sided alignment problem entirely.

**[SCAMPER-M #2]**: Fixed Font, Full Text, Magic Card Size
*Concept*: 63×88mm, fixed typography, full German rules text. Template designed once, generator fills in fields.
*Novelty*: No dynamic text reflow engine needed.

### SCAMPER — Put to Other Uses

**[SCAMPER-P #1]**: DM Reference Deck
*Concept*: Same card format for monster abilities, legendary actions, lair actions. DM prep artifact.
*Novelty*: Extends the tool to the DM side without new infrastructure.

**[SCAMPER-P #2]**: Teaching Tool for New Players
*Concept*: Print a "starter deck" of rule reminder cards for a new player's first session.
*Novelty*: Physical onboarding artifact that lives in the new player's hands.

**[SCAMPER-P #3]**: Other TTRPG Systems
*Concept*: The card template system is system-agnostic. Pathfinder, Das Schwarze Auge users could define their own card types.
*Novelty*: General German TTRPG card tool.

### SCAMPER — Eliminate

**[SCAMPER-E #1]**: File-Based Data, CLI Generation
*Concept*: Card data in YAML files. CLI command reads a deck profile and outputs a PDF. Zero UI to build initially.
*Novelty*: Entire working tool in ~200 lines of code.

**[SCAMPER-E #2]**: Deck Profile Files
*Concept*: A deck file is a list of card IDs. Save one per character. `generate --deck gandalf` prints exactly those cards.
*Novelty*: Selection problem solved with simplest possible mechanism. Human-readable, version-controllable.

### What If Scenarios

**[What-If #1]**: ~~OCR-Assisted Data Entry~~ — Rejected (too complex, gradual manual entry preferred)

**[What-If #2]**: User-Editable Card Templates
*Concept*: Layout template files (HTML/CSS or DSL) per card type, editable without touching code. Template reference stored in card YAML.
*Novelty*: Change card look by editing a template file, not the generator.

**[What-If #3]**: Edition + Source Metadata per Card
*Concept*: `edition`, `source_book`, optional `errata_date` fields rendered as card footer.
*Novelty*: Distinguishes 5e from 5.5e cards unambiguously in a mixed collection.

**[What-If #4]**: Interactive TUI Deck Builder
*Concept*: `dnd-cards select` opens an interactive terminal checklist — browse by type/class/level, toggle cards, save deck file. Uses inquirer (Node) or questionary (Python).
*Novelty*: Card browsing without a GUI framework. Deck file is the output.

**[What-If #5]**: English SRD as Shareable Reference Implementation
*Concept*: App ships with English SRD spell data (openly licensed). German data lives in user's private data folder. Tool is open-source; proprietary content stays private.
*Novelty*: Sidesteps the Ulisses Spiele license issue entirely.

**[What-If #6]**: Language-Agnostic Architecture
*Concept*: `language` field in card data files. Same card IDs across languages (`feuerball` / `fireball`). Multiple language data folders coexist.
*Novelty*: French, Spanish, Italian DMs can use the same tool with their localized books.

### Cross-Pollination

**[Cross-P #1]**: Anki-Inspired Data Folder Structure
*Concept*: `data/de/spells/feuerball.yaml`, `data/en/spells/fireball.yaml`, `data/de/conditions/vergiftet.yaml`. Generator discovers cards by scanning the folder tree.
*Novelty*: No database. Adding a card = dropping a file. Deleting = removing a file.

**[Cross-P #2]**: Quantities in Deck Profiles
*Concept*: Deck entries support quantity — `feuerball: 1`, `magisches-geschoss: 2`. Handles "prepared multiple times" use case.
*Novelty*: Deck file is single source of truth for what gets printed and how many copies.

**[Cross-P #3]**: Template Reference in Card YAML
*Concept*: Each card YAML declares `template: zauber-v1`. Generator looks up the template file and renders.
*Novelty*: Cards and templates loosely coupled. Multiple layout variants possible.

**[Cross-P #4]**: Deck File as Universal Interface
*Concept*: Deck file is the stable contract between any frontend and the PDF generator. CLI, TUI, future GUI all produce deck files. Generator is a pure function: deck file in → PDF out.
*Novelty*: Generator is immune to UI changes. Any future frontend is just a deck file editor.

---

## Idea Organization and Prioritization

### Thematic Clusters

**Theme 1 — Physical Card Design**
Fold-and-laminate format, magic card size (63×88mm), visual identity by type, edition metadata, icons as shorthand.

**Theme 2 — Card Type System**
Multi-template system, rules reminder cards, DM reference cards, template reference in YAML.

**Theme 3 — Data Architecture**
Anki-inspired folder structure, language-agnostic design, user-editable templates, hybrid data model (English SRD public / German data private).

**Theme 4 — Selection & Generation Workflow**
Deck profile files with quantities, class-driven filtering, deck file as universal interface, TUI deck builder, PDF with crop marks.

### Prioritization Results

**Core v1 — Must Have:**
1. Folder-based data store (`data/{lang}/{type}/{id}.yaml`)
2. Template files per card type (Zauber, Zustand at minimum)
3. Deck profile YAML files with quantities
4. CLI generator → A4 PDF with crop marks, fold-and-laminate card strips
5. English SRD data as seed content and test data

**Quick Wins — Add Early:**
6. Class-driven filter for spell browsing
7. Edition + source metadata rendered on cards
8. Interactive TUI deck builder (`dnd-cards select`)

**Later / Nice to Have:**
9. DM reference card type
10. Additional card types (feats, rules reminders)
11. Alternate template variants (compact vs. full)

### Breakthrough Concepts

- **Fold-and-Laminate** — eliminates the duplex printing problem elegantly
- **Deck File as Interface Contract** — future-proofs the architecture against any UI change
- **English SRD as Reference Implementation** — resolves the license problem while enabling community sharing of the tool itself

---

## Session Summary

**Ideas Generated:** 20+ across SCAMPER, What If Scenarios, and Cross-Pollination
**Key Decision Made:** CLI-first, file-based, PDF output, personal data stays private
**Architecture Crystallized:**

```
data/
  de/spells/feuerball.yaml       # template: zauber-v1, lang: de
  en/spells/fireball.yaml        # template: zauber-v1, lang: en
  de/conditions/vergiftet.yaml   # template: zustand-v1
templates/
  zauber-v1.html
  zustand-v1.html
decks/
  mira-stufe7.yaml               # feuerball: 1, magisches-geschoss: 2
```

`dnd-cards generate --deck decks/mira-stufe7.yaml` → PDF with crop marks

**Recommended Next Step:** Create PRD (`bmad-create-prd`) using these findings as input.

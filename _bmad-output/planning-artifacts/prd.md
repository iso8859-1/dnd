---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: ['_bmad-output/brainstorming/brainstorming-session-2026-04-10-2035.md']
workflowType: 'prd'
classification:
  projectType: cli_tool
  domain: tabletop_gaming_utilities
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - dnd

**Author:** Tobias
**Date:** 2026-04-10

## Executive Summary

A personal CLI tool that generates print-ready PDF reference cards for DnD 5.5e in German. Designed for German-speaking gaming groups with a single Spielerhandbuch, the tool eliminates mid-session lookup bottlenecks by giving each player a set of printed, lamination-ready cards covering their character's spells and relevant rules. Data is entered manually from physical books and managed as version-controlled YAML files. Output is an A4 PDF with crop marks ready for plotter cutting and folding into Magic card-sized (63×88mm) cards.

**Target user:** A German DM preparing reference materials for their group before sessions — specifically groups where players (including younger or less fluent English speakers) cannot rely on English-language resources.

**Core job-to-be-done:** Before the session, each player picks up their character's card deck and can prepare and reference their spells independently — no PHB required at the table.

### What Makes This Special

German DnD 5.5e spell cards do not exist commercially. This tool fills that gap with a self-print workflow: *"Deutsche Spruchkarten zum selber drucken."*

Unlike English card products, this tool is character-specific (deck profiles list exactly which cards to print and in what quantity), language-controlled (German data private to the user, English SRD data included as openly licensed reference), and physically optimized for home production (fold-and-laminate format, plotter crop marks).

The architecture cleanly separates concerns: card data (YAML files, Git-versioned), card layout (template files per card type), and print selection (deck profile files). Any future UI is simply a deck file editor — the generator remains a stable pure function.

**Project Type:** CLI tool | **Domain:** Tabletop gaming utilities (personal) | **Complexity:** Medium | **Deployment:** Personal use only, not distributed

## Success Criteria

### User Success

- A player picks up their printed card deck before a session and reads their spells in German without opening the Spielerhandbuch
- Cards are physically usable — fold cleanly, survive lamination, crop marks align with the plotter cutter
- A new character's cards can be printed within one prep session (data entered, deck file created, PDF generated)

### Personal Utility Success

- The tool becomes a regular part of session prep workflow
- Card data grows organically between sessions without feeling like a maintenance burden

### Technical Success

- PDF output requires zero manual adjustment after generation — plotter-ready as produced
- Adding a new card type requires only a new template file and YAML schema, no code changes
- A deck profile referencing a missing card ID fails with a clear error, never silently

### Measurable Outcomes

- At least 2 spell cards print correctly, fold cleanly, and survive lamination (MVP gate)
- Full A4 page layout with 8 card strips, crop marks present and accurate
- Generator runs without errors on a valid deck profile and produces a valid PDF

## User Journeys

### Journey 1: Adding a New Spell (Data Entry)

Tobias sits down between sessions. His Wizard player just hit level 5 and wants *Feuerball*. He opens his data folder, copies an existing spell YAML, fills in the German text from the Spielerhandbuch, and saves it. The card is immediately available for the next generate run.

**Emotional arc:** Routine, low-friction. Should feel like editing a text file, not operating a database.

### Journey 2: Building a Character Deck (Deck Creation)

It's Thursday evening, session is Saturday. Tobias creates `lena-stufe5-zauberin.yaml`, lists the spells Lena has prepared with quantities (`magisches-geschoss: 2`, `feuerball: 1`, `schild: 1`), and runs `dnd-cards generate --deck decks/lena-stufe5-zauberin.yaml`. The PDF opens. He verifies it looks correct.

**Emotional arc:** Quick and satisfying — a 5-minute task that produces a tangible artifact.

### Journey 3: Physical Production (Print, Cut, Fold, Laminate)

Saturday morning. Tobias prints the PDF, runs the plotter over the crop marks, folds each strip in half, laminates. Lena receives her card stack before the session. At the table, a question about *Feuerball* comes up — she reads her card without interrupting anyone or hunting for the PHB.

**Emotional arc:** The payoff. The moment the tool justifies itself.

### Journey 4: Level-Up — Updating an Existing Deck

After session 6, Lena levels up to 6. Tobias copies the deck file, renames it `lena-stufe6-zauberin.yaml`, adds two new spell IDs. Runs generate. Only the new cards need printing — existing laminated cards remain valid.

**Emotional arc:** Incremental, low-effort. The deck grows with the character.

### Journey 5: Error Recovery

Tobias runs generate and gets an error — a card ID in the deck file doesn't match any data file (typo: `feuerbaal` instead of `feuerball`). The tool prints: *"Card not found: feuerbaal (deck: lena-stufe6-zauberin.yaml, line 3)"*. He corrects the typo and reruns successfully.

**Emotional arc:** Brief frustration → immediate resolution. The tool helps rather than confuses.

### Journey Requirements Summary

| Journey | Key Capabilities Required |
|---|---|
| Data entry | Predictable YAML schema with example, clear malformed-file errors |
| Deck creation | Simple deck file format, card ID validation with actionable errors |
| Physical production | Precise crop marks, exact 126×88mm fold-strip layout, print-safe A4 output |
| Level-up update | Stable card IDs, trivially editable deck files |
| Error recovery | Pre-generation validation, fail-fast with file/line-level error messages |

## Innovation & Novel Patterns

### Detected Innovation Areas

**Market gap:** German DnD 5.5e spell cards do not exist commercially. This tool is the only known solution for German-speaking groups who cannot rely on English-language physical card products.

**Architectural pattern — Deck file as interface contract:** The deck profile YAML is the stable boundary between any user interface and the PDF generator. The generator is a pure function (deck file in → PDF out) and never changes regardless of what UI is built in front of it. CLI, TUI, or future GUI are all just deck file editors.

### Risk Mitigation

- **IP risk:** Mitigated by personal-use-only deployment; German card data is never distributed
- **Architecture risk:** Deck file format must be stable from v1 — changes that break existing deck files require explicit versioning

## CLI Tool Specification

### Command Structure

```
dnd-cards generate --deck <path>    # Generate PDF from deck profile
dnd-cards validate --deck <path>    # Validate deck profile without generating PDF
dnd-cards list [--type <type>]      # List available cards, optionally filtered by type
```

- Single entry point: `dnd-cards`
- Subcommands: `generate`, `validate`, `list`
- Shell completion for subcommands and `--deck` file paths (bash/zsh/fish)
- Non-interactive by default — all input via arguments and files
- Exit codes: 0 = success, 1 = validation error, 2 = generation error
- Errors → stderr with file path and line number; success → stdout with PDF path

### Configuration Schema

Three file types, all YAML:

| File type | Location | Purpose |
|---|---|---|
| Card data | `data/{lang}/{type}/{id}.yaml` | Card content + template reference |
| Template | `templates/{name}.html` (or similar) | Card layout per card type |
| Deck profile | `decks/{name}.yaml` | Card IDs + quantities to print |

### Output Format

- **PDF only** — A4, portrait, 2×4 fold-strip grid per page
- Each card strip: 126×88mm (folds to 63×88mm Magic card size)
- Plotter-ready crop marks on all strips
- 100% scale — no printer scaling required

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Problem-solving MVP — deliver the core job-to-be-done with zero extras.
**Validation gate:** At least 2 spell cards print correctly, fold cleanly, and survive lamination.

### Phase 1 — MVP

- YAML card data schema for spells + working template (`zauber-v1`)
- `dnd-cards generate`, `validate`, `list` subcommands
- Deck profile YAML with card IDs + quantities
- A4 PDF output with fold-strip layout and crop marks
- Git-versioned folder structure (`data/{lang}/{type}/{id}.yaml`)
- English SRD spell data as test/reference content
- Shell completion + exit codes + stderr error messages

### Phase 2 — Growth

- Additional card types: Zustände (conditions), Regelreferenz (rules reminders), feats
- Visual icons as shorthand on cards (damage type, casting time, concentration, ritual)
- Class-based filtering in `list` subcommand
- TUI deck builder (`dnd-cards select`)

### Phase 3 — Vision

- Full German DnD 5.5e spell database populated
- Multiple template variants per type (compact vs. full-text)
- DM reference cards (monster abilities, legendary actions, lair actions)
- Starter deck for new players: curated rule reminder cards for a first session
- Additional card types as the group's needs evolve

### Risk Mitigation

- **PDF precision:** Validate against physical output early — print and fold the first card before building the full system
- **Data integrity:** `validate` subcommand catches malformed YAML and missing IDs before PDF generation
- **Scope:** One template per card type in MVP — no dynamic layout logic

## Functional Requirements

### Card Data Management

- **FR1:** User can define a card by creating a YAML file with type-specific fields
- **FR2:** User can organize card data files in a folder hierarchy by language and card type (`data/{lang}/{type}/{id}.yaml`)
- **FR3:** User can reference a named template within a card YAML file
- **FR4:** User can include edition and source metadata fields in a card YAML file
- **FR5:** User can add a new card to the data store without modifying any other file

### Deck Profile Management

- **FR6:** User can define a print selection by creating a deck profile YAML file listing card IDs
- **FR7:** User can specify print quantity per card ID in a deck profile
- **FR8:** User can create multiple named deck profiles for different characters or purposes
- **FR9:** User can update a deck profile by editing its YAML file

### PDF Generation

- **FR10:** User can generate a print-ready PDF from a deck profile via a CLI command
- **FR11:** System renders each card as a fold-strip (126×88mm) on the output page
- **FR12:** System arranges card strips in a 2×4 grid per A4 page
- **FR13:** System includes plotter-ready crop marks on each card strip
- **FR14:** System produces PDF output at 100% scale, requiring no printer scaling adjustment
- **FR15:** System applies the template referenced in each card's YAML when rendering that card
- **FR16:** System writes the generated PDF path to stdout on successful generation

### Validation & Error Handling

- **FR17:** User can validate a deck profile against available card data without generating a PDF
- **FR18:** System reports each missing card ID with the deck file path and the missing ID
- **FR19:** System reports malformed YAML with the affected file path and line number
- **FR20:** System exits with distinct exit codes: 0 (success), 1 (validation error), 2 (generation error)
- **FR21:** System writes all error messages to stderr, never to stdout

### Card Discovery

- **FR22:** User can list all available cards in the data store
- **FR23:** User can filter the card list by card type

### Template System

- **FR24:** User can define a card layout by creating a template file
- **FR25:** User can assign different templates to different card types
- **FR26:** User can modify card appearance by editing a template file without changing card data files or generator code

### CLI Interface & Shell Integration

- **FR27:** User can invoke PDF generation via `dnd-cards generate --deck <path>`
- **FR28:** User can invoke validation via `dnd-cards validate --deck <path>`
- **FR29:** User can list available cards via `dnd-cards list [--type <type>]`
- **FR30:** User can use shell tab-completion for subcommands and `--deck` file path arguments

### Language & Content Support

- **FR31:** User can maintain card data in multiple languages within the same data store
- **FR32:** System generates a PDF using only the cards referenced in the deck profile — no "print all" mode

## Non-Functional Requirements

### Performance

- PDF generation for a typical deck (10–20 cards) completes in under 10 seconds on a standard desktop machine
- `validate` completes in under 2 seconds for any deck profile
- `list` returns results in under 1 second regardless of data store size

### Reliability

- Generation either succeeds fully or fails with a clear error — no silent partial or corrupted PDF output
- Card data and deck profile files are plain text YAML — human-readable, diff-friendly, and recoverable without tooling

### Maintainability

- Adding a new card type requires no changes to the generator code — only a new template file and YAML schema
- The deck profile format must remain stable from v1; schema changes that break existing deck files require explicit versioning

### Portability

- The tool runs on Windows, macOS, and Linux without platform-specific configuration
- Generated PDFs render identically across standard PDF viewers and A4 printers

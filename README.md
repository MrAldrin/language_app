# Language Learning App (MVP)

This project is a Marimo-based language learning app focused on fast, targeted grammar and vocabulary practice.  
Question content is JSON-driven, and the runtime adapts interaction behavior from each question type.  
The current implementation prioritizes a functional MVP: filterable practice sessions, clear answer feedback, and lightweight session-level scoring.

## What The App Currently Supports

- Source and target language selection from available pair data
- Question set selection (`sentence_builder`, `word_translation`, `cloze`)
- Difficulty filtering with mapped bands:
  - `1-3`: easy
  - `4-7`: medium
  - `8-10`: hard
- Direction control (`Both`, `L1 -> L2`, `L2 -> L1`) for non-cloze sets
- Family/subtype tag filtering when `family:*` tags exist in the selected dataset
- Question navigation (`Previous` / `Next`) inside a session
- In-question `Check`, `Clear`, and `Reveal answer` interaction flow
- Session summary with total questions, attempts, correct/incorrect, and accuracy

## Question Types And Interaction Model

- `sentence_builder_multiple_choice`
  - Learner builds a full answer from a token pool
  - Selected tokens can be reordered in the answer area
- `word_translation`
  - Learner selects a single token answer from a pool
  - Uses the same check/reveal flow as other sets
- `cloze_word_choice`
  - Learner fills one blank in a sentence from a token pool
  - Direction selector is disabled/not applicable for this type

## Question Data Files (Current Inventory)

Data is stored under `apps/public/` in two layouts:

- Pair files: `apps/public/<lang1>_<lang2>/`
- Language files: `apps/public/<lang>/`

Current inventory in this repo:

- `sentence_builder`: 6 files x 50 questions each
  - `de_en`, `de_nl`, `de_no`, `en_nl`, `en_no`, `nl_no`
- `word_translation`: 2 files
  - `apps/public/de_no/word_translation_questions.json` (62)
  - `apps/public/nl_no/word_translation_questions.json` (60)
- `cloze_word_choice`: 2 files
  - `apps/public/de/cloze_word_choice_questions.json` (105)
  - `apps/public/nl/cloze_word_choice_questions.json` (105)

## Data Schema Snapshot (Schema v2)

Each question object uses the shared schema:

- `id`: integer identifier
- `schema_version`: current schema version (`2`)
- `question_type`: interaction discriminator
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced labels in `namespace:value` format
- `content`: type-specific interaction settings (for example `response_mode`)
- `translations`: per-language payload with prompt/answer/accepted/word pool (+ optional hint)

## How To Run

Run locally:

```bash
uv run apps/language_app.py
```

This repository also includes a GitHub Pages export/deploy workflow inherited from the template. That workflow builds marimo notebooks/apps into `_site` via `.github/scripts/build.py`, but the primary project here is the language app in `apps/language_app.py`.

## Roadmap

Short term:
- Content expansion
  - Add more question files, expand language coverage, and increase per-set question volume
- Authoring and tooling
  - Strengthen validation and generation workflows for question quality and schema consistency

Long term:
- Persistence and analytics
  - Move beyond in-memory session stats to stored session history and progress tracking
- UX and learning flow
  - Add review mode, adaptive repeats, and error-driven practice loops

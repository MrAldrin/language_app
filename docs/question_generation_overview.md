# Question Generation Overview

This is the shared, high-level ruleset for all question generation in the language app.

## Core Contract (All Question Types)

Each question object must include:

- `id`: sequential integer
- `schema_version`: `2`
- `question_type`: discriminator for interaction type
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced labels (`namespace:value`)
- `content`: type-specific interaction settings
- `translations`: language payload(s) used by that question type

Common translation payload fields:

- `text`: canonical text in that language
- `accepted`: alternative correct texts (full sentence or single token, depending on question type)
- `distractors`: extra tokens used to build the selectable pool for choice-style interactions

Type-specific payload fields may also exist (examples):

- `hint` (display-only disambiguation, used by `word_translation`)
- `hidden_word_index` (used by `cloze_word_choice`)

Legacy compatibility during migration:

- `primary` may still exist, but is deprecated.

## Canonical Tag System

All tags must follow:

- `namespace:value`

Recommended namespaces:

- `family:*` (for broad families, e.g. `family:pronoun`)
- `pronoun_type:*` (e.g. `pronoun_type:personal`)
- `case:*`, `person:*`, `number:*`, `role:*`, `gender:*`, `register:*`, `deixis:*`
- `tense:*`, `pos:*`, `grammar:*`
- `topic:*` (domain/theme labels)
- `feature:*` (non-topic semantic distinctions)

Tag policy notes:

- Do not use unscoped legacy tags like `pronoun`, `relative`, `food`, `past_tense`.
- Keep tags concise and high-signal; avoid redundant synonyms when one canonical tag already captures meaning.

## Tagging By Question Type

Use the same canonical system across all files, but prioritize different namespaces by interaction type:

- `cloze_word_choice`:
  - Primary focus: `family:*`, `pronoun_type:*`, plus grammar slices like `case:*`, `role:*`, `number:*`, `gender:*`, `register:*`.
  - Typical example: `["family:pronoun", "pronoun_type:relative", "case:genitive"]`
- `word_translation`:
  - Primary focus: `family:*`, `pronoun_type:*`, with disambiguators such as `person:*`, `number:*`, `role:*`, `gender:*`, `case:*`, `deixis:*`.
  - Optional semantic refiners can use `feature:*` when they materially improve targeting.
- `sentence_builder_multiple_choice`:
  - Primary focus: `topic:*` for scenario/theme, optionally combined with `pos:*`, `grammar:*`, and `tense:*`.
  - Tense/time labeling must use only `tense:*` (map legacy `past`/`future` to `tense:past`/`tense:future`).
  - Do not use low-signal broad tags like `basics`.

General namespace intent:

- `topic:*` = scenario/domain context (`topic:travel`, `topic:family`)
- `pos:*` = part-of-speech focus (`pos:verb`, `pos:adjective`, `pos:pronoun`)
- `grammar:*` = grammar intent (`grammar:question`, `grammar:negation`)
- `tense:*` = tense dimension (`tense:present`, `tense:past`, `tense:future`)
- `feature:*` = non-topic semantic distinctions used when they add targeting value

## Shared Authoring Rules

- Keep grammar and spelling correct in every language.
- Use correct written characters and orthography for each language (for example `kjørte`, not `kjorte`; `fløy`, not `floy`).
- Do not replace language-specific characters with ASCII approximations.
- Prefer natural, modern phrasing.
- Keep distractors plausible (near-miss, not nonsense).
- Prefer controlling the selectable pool via `distractors` over growing `accepted`.
- Keep `accepted` small and avoid free-form paraphrases; put type-specific acceptance rules in the corresponding type spec.
- Never use display-only hint fields for correctness checks.

## File Families and Naming

### Pair-based files (bilingual)

Stored under `apps/public/<lang1>_<lang2>/`:

- `sentence_builder_questions.json`
- `word_translation_questions.json`

### Language-based files (monolingual)

Stored under `apps/public/<lang>/`:

- `cloze_word_choice_questions.json`

For cloze, rows should use one translation language only and set `content.practice_language` to that same language.

## Type-Specific Specs

- Sentence builder: `docs/content_generation_rules.md`
- Word translation: `docs/targeted_questions.md`
- Cloze word choice: `docs/cloze_questions.md`

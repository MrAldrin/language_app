# Question Generation Overview (Schema v2)

This is the shared, high-level ruleset for all question generation in the language app.

## Core Contract (All Question Types)

Each question object must include:

- `id`: sequential integer
- `schema_version`: `2`
- `question_type`: discriminator for interaction type
- `difficulty`: integer `1-10`
- `tags`: grammar/topic labels
- `content`: type-specific interaction settings
- `translations`: keyed by language code

Each `translations.<lang>` object should use:

- `prompt`: text shown to learner
- `answer`: canonical correctness target
- `accepted`: alternative correct answers
- `word_pool`: options used by selection-style interactions
- `hint` (optional): display-only disambiguation

Legacy compatibility during migration:

- `primary` may still exist, but is deprecated.

## Shared Authoring Rules

- Keep grammar and spelling correct in every language.
- Keep translations aligned in meaning across language directions.
- Prefer natural, modern phrasing.
- Keep distractors plausible (near-miss, not nonsense).
- Never use `hint` for correctness checks.

## File Naming Convention

Use one file per question family in each language-pair directory:

- `sentence_builder_questions.json`
- `word_translation_questions.json`
- `cloze_word_choice_questions.json` (when added)

## Type-Specific Specs

- Sentence builder: `docs/content_generation_rules.md`
- Word translation: `docs/targeted_questions.md`
- Cloze word choice: `docs/cloze_questions.md`

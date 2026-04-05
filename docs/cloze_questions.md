# Cloze Question Rules (Schema v2)

This document defines rules for generating `cloze_word_choice` questions.

## 1. Purpose

Cloze questions are target-language production drills.
The learner sees one sentence in the practice language with one blank and selects the correct token from a word pool in that same language.

## 2. File Layout

Cloze uses one file per language (not per language pair):

- `apps/public/<lang>/cloze_word_choice_questions.json`

Examples:

- `apps/public/nl/cloze_word_choice_questions.json`
- `apps/public/no/cloze_word_choice_questions.json`

## 3. Schema

Each question object must contain:

- `id`: sequential integer
- `schema_version`: must be `2`
- `question_type`: must be `cloze_word_choice`
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced tags (`namespace:value`), following shared rules in `docs/question_generation_overview.md`
- `content`:
  - `response_mode`: must be `single_token_choice`
  - `blank_token`: placeholder string, default `___`
  - `practice_language`: language code for this file (for example `nl`)
- `translations`: a dictionary of language codes. Must contain at least one language entry matching `content.practice_language`. Other languages can optionally be added to provide translated hints.

For the `translations.<lang>` object matching the `practice_language` (the target learning language), it must contain:

- `prompt`: sentence containing exactly one blank token (for example `Ik zie ___ hond in het park.`)
- `answer`: expected missing token
- `accepted`: optional alternative valid tokens
- `word_pool`: includes `answer`, all `accepted`, and distractors

For other languages in `translations` (the user's source language hints), they only require:
- `hint_translation` to show the full translated sentence.

Optional fields:

- `hint`: display-only guidance
- `primary`: legacy compatibility field (deprecated)

## 4. Authoring Rules

- Exactly one blank per prompt.
- `answer` must be selectable from `word_pool`.
- `word_pool` should contain plausible near-miss distractors.
- Keep prompts natural and pedagogically focused.
- Cloze should never require filling blanks in the learner's mother tongue.
- For pronoun-focused cloze files, include `family:pronoun` and at least one discriminative subtype/slice (for example `pronoun_type:*`, `case:*`, or `role:*`).

## 5. Validation Rules

- Correctness compares selected token to `answer` or a value in `accepted`.
- `hint` must never affect correctness.
- `blank_token` must appear exactly once in `prompt`.
- `content.practice_language` must map to a valid language key inside `translations` (this key defines the primary exercise).

## 6. Examples

### Dutch practice cloze with multiple language hints

```json
{
  "id": 5001,
  "schema_version": 2,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["topic:animals", "number:singular"],
  "content": {
    "response_mode": "single_token_choice",
    "blank_token": "___",
    "practice_language": "nl"
  },
  "translations": {
    "nl": {
      "prompt": "Ik zie ___ hond in het park.",
      "answer": "een",
      "accepted": [],
      "word_pool": ["een", "de", "het", "die", "dat"]
    },
    "no": {
      "hint_translation": "Jeg ser en hund i parken."
    },
    "en": {
      "hint_translation": "I see a dog in the park."
    }
  }
}
```

### Norwegian practice cloze (no hints)

```json
{
  "id": 6001,
  "schema_version": 2,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["topic:animals", "number:singular"],
  "content": {
    "response_mode": "single_token_choice",
    "blank_token": "___",
    "practice_language": "no"
  },
  "translations": {
    "no": {
      "prompt": "Jeg ser ___ hund i parken.",
      "answer": "en",
      "accepted": [],
      "word_pool": ["en", "ei", "et", "den", "det"]
    }
  }
}
```

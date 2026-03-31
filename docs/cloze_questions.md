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
- `tags`: grammar/topic tags
- `content`:
  - `response_mode`: must be `single_token_choice`
  - `blank_token`: placeholder string, default `___`
  - `practice_language`: language code for this file (for example `nl`)
- `translations`: exactly one language entry, matching `content.practice_language`

Each `translations.<lang>` object must contain:

- `prompt`: sentence containing exactly one blank token (for example `Ik zie ___ hond in het park.`)
- `answer`: expected missing token
- `accepted`: optional alternative valid tokens
- `word_pool`: includes `answer`, all `accepted`, and distractors

Optional fields:

- `hint`: display-only guidance
- `primary`: legacy compatibility field (deprecated)

## 4. Authoring Rules

- Exactly one blank per prompt.
- `answer` must be selectable from `word_pool`.
- `word_pool` should contain plausible near-miss distractors.
- Keep prompts natural and pedagogically focused.
- Cloze should never require filling blanks in the learner's mother tongue.

## 5. Validation Rules

- Correctness compares selected token to `answer` or a value in `accepted`.
- `hint` must never affect correctness.
- `blank_token` must appear exactly once in `prompt`.
- `content.practice_language` must match the single language key inside `translations`.

## 6. Examples

### Dutch-only cloze row

```json
{
  "id": 5001,
  "schema_version": 2,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["articles", "singular", "animals"],
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
    }
  }
}
```

### Norwegian-only cloze row

```json
{
  "id": 6001,
  "schema_version": 2,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["articles", "singular", "animals"],
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

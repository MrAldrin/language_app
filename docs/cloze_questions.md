# Cloze Question Rules (Schema v2)

This document defines rules for generating `cloze_word_choice` questions.

## 1. Purpose

Cloze questions show a sentence with one missing token. The learner picks the correct token from a word pool.

## 2. Schema

Each question object must contain:

- `id`: sequential integer
- `schema_version`: must be `2`
- `question_type`: must be `cloze_word_choice`
- `difficulty`: integer 1-10
- `tags`: grammar/topic tags
- `content`:
  - `response_mode`: `single_token_choice`
  - `blank_token`: placeholder string, default `___`
- `translations`: keyed by language code

Each `translations.<lang>` object must contain:

- `prompt`: sentence containing exactly one blank token (for example `Jeg ser ___ hund.`)
- `answer`: the expected missing token
- `accepted`: alternative valid tokens (optional)
- `word_pool`: includes `answer`, all `accepted`, and distractors

Optional fields:

- `hint`: display-only guidance
- `primary`: legacy compatibility field (deprecated)

## 3. Authoring Rules

- One blank only per prompt.
- `answer` should be a token selectable from `word_pool`.
- Distractors should be plausible within the same grammar context.
- Keep bidirectional symmetry when possible (if pair supports both directions).
- Use natural sentences, not isolated grammar fragments.

## 4. Validation Rules

- Correctness compares user choice to `answer` or any value in `accepted`.
- `hint` must not affect correctness.
- `blank_token` must appear exactly once in each prompt.

## 5. v2 Example

```json
{
  "id": 5001,
  "schema_version": 2,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["articles", "singular", "animals"],
  "content": {
    "response_mode": "single_token_choice",
    "blank_token": "___"
  },
  "translations": {
    "no": {
      "prompt": "Jeg ser ___ hund i parken.",
      "answer": "en",
      "accepted": [],
      "word_pool": ["en", "ei", "et", "den", "det"]
    },
    "nl": {
      "prompt": "Ik zie ___ hond in het park.",
      "answer": "een",
      "accepted": [],
      "word_pool": ["een", "de", "het", "die", "dat"]
    }
  }
}
```

# Targeted Word Translation Rules (Schema v2)

This document defines rules for generating `word_translation` questions for the language app.

## Schema (v2)

Each question object must contain:

- `id`: integer
- `schema_version`: must be `2`
- `question_type`: must be `word_translation`
- `difficulty`: integer 1-10
- `tags`: list of grammar/topic tags
- `content`: type-specific interaction config
  - `response_mode`: for this type, use `single_token_choice`
- `translations`: keyed by language code (`en`, `de`, `no`, `nl`)

Each `translations.<lang>` object must contain:

- `prompt`: text shown to the learner
- `answer`: canonical text used for answer checking
- `accepted`: list of additional accepted answers
- `word_pool`: selectable tokens (must include all correct forms)

Optional fields:

- `hint`: display-only disambiguation (never used in answer checking)
- `primary`: legacy compatibility field (deprecated; keep only during migration window)

## Disambiguation Rule

If the visible source form is ambiguous (gender, number, formality, grammatical role), put the disambiguation in `hint`, not in `answer`.

Example:

- `prompt`: `zij`
- `hint`: `enkelvoud`
- `answer`: `zij`

Do not store `zij (enkelvoud)` in `answer`.

## Linguistic & Pedagogy Rules

- Grammar & capitalization: always correct in each language.
- Natural distractors: choose near-miss alternatives from the same pronoun/grammar family.
- Bidirectional symmetry: ensure entries work in both directions where intended.

## Technical Constraints

- File type: JSON
- Encoding: UTF-8
- One file per language pair under `apps/public/<pair>/`

## v2 Example

```json
{
  "id": 1001,
  "schema_version": 2,
  "question_type": "word_translation",
  "difficulty": 1,
  "tags": ["pronoun", "plural"],
  "content": {
    "response_mode": "single_token_choice"
  },
  "translations": {
    "en": {
      "prompt": "you",
      "hint": "plural",
      "answer": "you",
      "accepted": [],
      "word_pool": ["you", "your", "yours", "we", "they"]
    },
    "no": {
      "prompt": "dere",
      "answer": "dere",
      "accepted": [],
      "word_pool": ["du", "deg", "din", "de", "vi", "dere"]
    }
  }
}
```

## Note for Sentence Question Files

For `sentence_builder_multiple_choice` in `questions.json`, use the same text separation:

- `prompt`: text displayed to learner
- `answer`: canonical correct sentence
- `accepted`: alternatives
- `content.response_mode`: `token_sequence_choice`

This keeps all question types aligned and makes future additions (for example cloze) easier.

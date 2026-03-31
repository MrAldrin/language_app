# Sentence Builder Question Rules (Schema v2)

This document is the type-specific spec for `sentence_builder_multiple_choice`.
For shared rules across all question types, see `docs/question_generation_overview.md`.

## Schema

Each question object must contain:

- `id`: sequential integer
- `schema_version`: must be `2`
- `question_type`: must be `sentence_builder_multiple_choice`
- `difficulty`: integer `1-10`
- `tags`: relevant grammar/topic tags
- `content`:
  - `response_mode`: must be `token_sequence_choice`
- `translations`: keyed by language code

Each `translations.<lang>` object must contain:

- `prompt`: source text shown to learner
- `answer`: canonical target text for checking
- `accepted`: natural alternative correct answers
- `word_pool`: answer tokens + distractors

Optional fields:

- `hint`: display-only metadata (rare for this type)
- `primary`: legacy field, deprecated

## Type-Specific Authoring Rules

- Keep sentence pairs directly equivalent in meaning.
- Include enough distractors to make word order and grammar meaningful.
- Avoid clues from punctuation/capitalization in `word_pool`.
- Distractors should be plausible alternatives from same concept cluster.

## Example

```json
{
  "id": 1,
  "schema_version": 2,
  "question_type": "sentence_builder_multiple_choice",
  "difficulty": 1,
  "tags": ["basics", "question"],
  "content": {
    "response_mode": "token_sequence_choice"
  },
  "translations": {
    "no": {
      "prompt": "Hvor er boka?",
      "answer": "Hvor er boka?",
      "accepted": ["Hvor er boken?"],
      "word_pool": ["hva", "hvem", "når", "var", "brevet", "avisa", "hvor", "er", "boka"]
    },
    "de": {
      "prompt": "Wo ist das Buch?",
      "answer": "Wo ist das Buch?",
      "accepted": [],
      "word_pool": ["was", "wer", "wann", "Zeitung", "bist", "bin", "wo", "ist", "das", "Buch"]
    }
  }
}
```

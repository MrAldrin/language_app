# Word Translation Question Rules (Schema v2)

This document is the type-specific spec for `word_translation`.
For shared rules across all question types, see `docs/question_generation_common_rules.md`.

## Schema

Each question object must contain:

- `id`: integer
- `schema_version`: must be `2`
- `question_type`: must be `word_translation`
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced tags (`namespace:value`), following shared rules in `docs/question_generation_common_rules.md`
- `content`:
  - `response_mode`: must be `single_token_choice`
- `translations`: keyed by language code (`en`, `de`, `no`, `nl`)

Each `translations.<lang>` object must contain:

- `prompt`: text shown to learner
- `answer`: canonical text used for checking
- `accepted`: alternative accepted answers
- `word_pool`: selectable options

Optional fields:

- `hint`: display-only disambiguation
- `primary`: legacy field, deprecated

## Type-Specific Authoring Rules

- If form is ambiguous (gender/number/formality/case), put clarification in `hint`.
- Do not include disambiguation markers inside `answer`.
- Distractors should be near-miss variants in same pronoun/grammar family.
- Preserve bidirectional symmetry where intended.
- Prefer structured pronoun tagging that combines family + subtype + useful disambiguators (for example `person:*`, `number:*`, `role:*`, `gender:*`, `case:*`).

## Example

```json
{
  "id": 1001,
  "schema_version": 2,
  "question_type": "word_translation",
  "difficulty": 1,
  "tags": ["family:pronoun", "pronoun_type:personal", "person:2", "number:plural", "role:subject"],
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

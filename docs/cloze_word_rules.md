# Cloze Question Rules

This document defines rules for generating `cloze_word_choice` questions.

## 1. Purpose

Cloze questions are target-language production drills.
The learner sees one sentence in the practice language with one blank and selects the correct token from a word pool in that same language.

## 2. File Layout

Cloze uses one file per language (not per language pair):

- `apps/public/<lang>/cloze_word_choice_questions.json`

Examples:

- `apps/public/nl/cloze_word_choice_questions.json`
- `apps/public/de/cloze_word_choice_questions.json`

## 3. Schema

Each question object must contain:

- `id`: sequential integer
- `question_type`: must be `cloze_word_choice`
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced tags (`namespace:value`), following shared rules in `docs/question_generation_common_rules.md`
- `content`:
  - `response_mode`: must be `single_token_choice`
  - `practice_language`: language code for this file (for example `nl`)
- `translations`: a dictionary of language codes. Must contain at least one language entry matching `content.practice_language`. Other languages can optionally be added to provide translated hints.

For the `translations.<lang>` object matching the `practice_language` (the target learning language), it must contain:

- `text`: full sentence in the practice language
- `hidden_word_index`: zero-based index of the hidden token in the practice-language sentence
- `accepted`: optional alternative valid tokens
- `distractors`: selectable distractor tokens shown as alternatives

For other languages in `translations` (the user's source language hints), they only require:
- `text` to show the translated sentence.

## 4. Authoring Rules

- The hidden token is defined by `hidden_word_index` inside `translations.<practice_language>.text`.
- `hidden_word_index` must point to a valid token position in the practice-language sentence.
- `distractors` should contain plausible near-miss options from the same grammar family when possible.
- Keep prompts natural and pedagogically focused.
- Cloze should never require filling blanks in the learner's mother tongue.
- For pronoun-focused cloze files, include `family:pronoun` and at least one discriminative subtype/slice (for example `pronoun_type:*`, `case:*`, or `role:*`).

## 5. Validation Rules

- Correctness compares selected token to the hidden token from `text` or a value in `accepted`.
- `content.practice_language` must map to a valid language key inside `translations` (this key defines the primary exercise).
- `hidden_word_index` must be present for the practice-language translation object.

## 6. Examples

### Dutch practice cloze with multiple language hints

```json
{
  "id": 5001,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["topic:animals", "number:singular"],
  "content": {
    "response_mode": "single_token_choice",
    "practice_language": "nl"
  },
  "translations": {
    "nl": {
      "text": "Ik zie een hond in het park.",
      "hidden_word_index": 2,
      "accepted": [],
      "distractors": ["de", "het", "die", "dat"]
    },
    "no": {
      "text": "Jeg ser en hund i parken."
    },
    "en": {
      "text": "I see a dog in the park."
    }
  }
}
```

### German practice cloze with language hints

```json
{
  "id": 7002,
  "question_type": "cloze_word_choice",
  "difficulty": 2,
  "tags": ["case:dative", "family:pronoun", "pronoun_type:personal", "role:object"],
  "content": {
    "response_mode": "single_token_choice",
    "practice_language": "de"
  },
  "translations": {
    "de": {
      "text": "Kannst du mir bitte helfen? Ich verstehe das nicht.",
      "hidden_word_index": 2,
      "accepted": [],
      "distractors": ["mich", "dir", "dich", "uns"]
    },
    "en": {
      "text": "Can you please help me? I don't understand this."
    },
    "no": {
      "text": "Kan du vær så snill å hjelpe meg? Jeg forstår ikke dette."
    }
  }
}
```

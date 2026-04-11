# Cloze Question Rules

This document defines rules for generating `cloze_word_choice` questions.

## Purpose

Cloze questions are target-language production drills.
The learner sees one sentence in the practice language with one blank and selects the correct token from a word pool in that same language.

## File Layout

Cloze uses one file per language (not per language pair):

- `apps/public/<lang>/cloze_word.json`


## Specific schema rules

Each question object must contain:

- `question_type`: must be `cloze_word_choice`
- `content`:
  - `response_mode`: must be `single_token_choice`
  - `practice_language`: language code for this file
- `translations`: a dictionary of language codes. Must contain at least one language entry matching `content.practice_language`.

The `translations.<lang>` object matching the `practice_language` must contain:

- `text`: full sentence in the practice language
- `hidden_word_index`: zero-based index of the hidden token in the practice-language sentence
- `accepted`: is not used and is always empty

Other languages in `translations` only require:
- `text` to show the translated sentence.


## Generationg logic:
When generating this type of question, follow these steps:
  1. Create a sentence targeting the wanted topic or learning issue
  2. Identify the word to be removed with the "hidden_word_index". This word should be the  focuse of the task.
  3. Create distractors in "distractors" that are not valid as alternatives in the given sentense
  

## Type-Specific Authoring Rules

- The hidden token is defined by `hidden_word_index` inside `translations.<practice_language>.text`.
- `hidden_word_index`:
  - must point to a valid token position in the practice-language sentence.
  - should only be used for the practice_language


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

# Targeted Word Translation Rules

This document defines the rules for generating word translation questions for the language app. This question type focuses on individual words, pronouns, and grammatical nuances.

## Data Schema

- **`id`**: Sequential integer.
- **`question_type`**: Must be `word_translation`.
- **`difficulty`**: Integer 1–10.
- **`tags`**: Relevant grammatical tags (e.g., `pronoun`, `possessive`, `formal_address`, `number`, `adjective`, `foods`, `animals`).
- **`translations`**: A dictionary keyed by language code (`en`, `de`, `no`, `nl`). Each entry contains:
    - **`primary`**: The word or short phrase. Use [Context Hints](#2-context-hints) for disambiguation.
    - **`accepted`**: List of valid synonyms (e.g., `boka` and `boken` for Norwegian).
    - **`word_pool`**: A list of all words that appear in either primary or accepted and then another 4-6 extra distractor words from the same grammatical category.

## Context Hints (Disambiguation)

### The Rule of Ambiguity:
If a word in the source language could translate into multiple distinct words in the target language based on context (gender, number, formality, case), you **must** include a hint in parentheses in the `primary` field.

- **Purpose**: To ensure the user has enough information to pick the correct word from the pool.
- **Language**: The hint should be in the language of the `primary` field it is attached to.

#### Examples of Ambiguity:
- **Formality/Number (English -> German)**: 
  - `primary` for EN: `you (singular)` -> DE: `du`
  - `primary` for EN: `you (plural)` -> DE: `ihr`
  - `primary` for EN: `you (formal)` -> DE: `Sie`
- **Gender/Number (German -> English)**:
  - `primary` for DE: `sie (sing.)` -> EN: `she`
  - `primary` for DE: `sie (plur.)` -> EN: `they`
- **Gendered Nouns (English -> Spanish/German)**:
  - `primary` for EN: `the teacher (female)` -> DE: `die Lehrerin`
  - `primary` for EN: `the teacher (male)` -> DE: `der Lehrer`
- **Case/Function (English -> German)**:
  - `primary` for EN: `her (possessive)` -> DE: `ihr`
  - `primary` for EN: `her (object)` -> DE: `sie`


## Linguistic & Pedagogy Rules

- Grammar & Capitalization: Always use correct grammar and spelling in that language.
- Natural Distractors: Distractors should be "near-misses" (e.g., different person/number/gender of the same pronoun group).
- Bidirectional Symmetry: The `word_translation` should work both ways. If `you (plural)` -> `dere`, then `dere` -> `you`.


## Technical Constraints
- File type: json
- Encoding: UTF-8
- The questions should be generated in pairs of languages (one JSON file per language pair) and placed in their respective folders in apps/public/. 


## Schema Example:

```json
{
  "id": 1001,
  "question_type": "word_translation",
  "difficulty": 1,
  "tags": ["pronoun", "plural"],
  "translations": {
    "en": {
      "primary": "you (plural)",
      "accepted": [],
      "word_pool": ["you", "your", "yours", "we", "they"]
    },
    "no": {
      "primary": "dere",
      "accepted": [],
      "word_pool": ["du", "deg", "din", "de", "vi", "dere"]
    }
  }
}
```

### Another Example (Possessives):
```json
{
  "id": 1002,
  "question_type": "word_translation",
  "difficulty": 2,
  "tags": ["possessive", "singular"],
  "translations": {
    "en": {
      "primary": "his",
      "accepted": [],
      "word_pool": ["his", "he", "him", "her", "hers", "my", "our"]
    },
    "de": {
      "primary": "sein",
      "accepted": ["seine"],
      "word_pool": ["sein", "seine", "er", "ihm", "ihr", "ihre", "mein", "unser"]
    }
  }
}
```

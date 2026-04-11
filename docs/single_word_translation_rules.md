# Word Translation Question Rules

This document is the type-specific spec for `word_translation`.
For shared rules across all question types, see `docs/question_generation_common_rules.md`.


## Schema

Question object must contain:

- `question_type`: must be `word_translation`

Each question could contain:

- `hint`: to help if there are more than one answer due to language differences. (Like you meaning plural and sinuglar in english) 

## Generating logic:
When generating this type of question, follow these steps:
  1. Create a translation pair in the "text" fields
  2. Create distractors in "distractors" that are no valid translations.
  

## Type-Specific Authoring Rules

- Never use "accepted" for this question type
- Treat the two `text` fields as the main translation pair. Each `text` should be the most direct, standard form we want the learner to choose.
- Word translation is bidirectional. Each side should be reviewed against the other side.
- Use `hint` only if needed to make it clear for the learner what we want from them. Like clarify ambiguity such as gender, number, formality, or case when the displayed form alone is not specific enough.



## Example

```json
{
  "id": 3002,
  "question_type": "word_translation",
  "difficulty": 1,
  "tags": ["family:pronoun", "person:2", "number:singular", "pronoun_type:personal", "role:subject"],
  "translations": {
    "nl": {
      "text": "jij",
      "accepted": [],
      "distractors": ["je", "jou", "ik", "hij", "u", "jullie"]
    },
    "no": {
      "text": "du",
      "accepted": [],
      "distractors": ["deg", "din", "jeg", "han", "dere", "vi"]
    }
  }
}
```

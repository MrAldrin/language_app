# Sentence Builder Question Rules

This document is the type-specific spec for `sentence_builder_multiple_choice`.
For shared rules across all question types, see `docs/question_generation_common_rules.md`.


## Specific schema rules

Question object must contain:

- `question_type`: must be `sentence_builder_multiple_choice`


## Generationg logic:
When generating this type of question, follow these steps:
  1. Create a translation pair in the "text" fields
  2. Create distractors in "distractors"
  3. Extract all words from "text" and combine them with "distractors"
  4. Check the if there are any meaningfull translations in that set of words that is not the sentence in "text"
      - Often reordering of the "text" words will also yield a valid translation. If this is the case, add them to "accepted"
      - If there are other valid translations due to the use of the "distractors", replace that distractor
  5. Repeat step 4 until there are no other valid translations


## Type-Specific Authoring Rules

- Treat the two `text` fields as the main translation pair. Each `text` should be the most direct natural translation of the paired `text`.
- Sentence builder is bidirectional. Each side should be reviewed against the other side.

Distractors:
- should challenge both grammar and meaning when possible.
- should be plausible, but should not create many extra valid full-sentence translations.
- Prefer replacing a distractor over expanding `accepted`.


## Example

```json
{
  "id": 1,
  "question_type": "sentence_builder_multiple_choice",
  "difficulty": 1,
  "tags": ["grammar:question", "topic:school"],
  "content": {
    "response_mode": "token_sequence_choice"
  },
  "translations": {
    "en": {
      "text": "They often travel to Spain",
      "accepted": ["They travel to Spain often"],
      "distractors": ["Germany", "never", "drove", "flew", "we", "car"]
    },
    "no": {
      "text": "De reiser ofte til Spania",
      "accepted": [],
      "distractors": ["Tyskland", "aldri", "kjørte", "fløy", "vi", "bil"]
    }
  }
}
```

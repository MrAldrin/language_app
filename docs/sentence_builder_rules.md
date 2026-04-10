# Sentence Builder Question Rules

This document is the type-specific spec for `sentence_builder_multiple_choice`.
For shared rules across all question types, see `docs/question_generation_common_rules.md`.

These rules should work across the language pairs used in the app, especially Norwegian, English, Dutch, and German.

## Schema

Each question object must contain:

- `id`: sequential integer
- `question_type`: must be `sentence_builder_multiple_choice`
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced tags (`namespace:value`), following shared rules in `docs/question_generation_common_rules.md`
- `content`:
  - `response_mode`: must be `token_sequence_choice`
- `translations`: keyed by language code

Each `translations.<lang>` object must contain:

- `text`: canonical sentence for that language
- `accepted`: other accepted full-sentence answers
- `distractors`: extra tokens added to test the learner

Optional fields:

- `hint`: display-only metadata (rare for this type)

## Type-Specific Authoring Rules

- Treat the two `text` fields as the main translation pair. Each `text` should be the most direct natural translation of the paired `text`.
- Sentence builder is bidirectional. Each side should be reviewed against the other side.
- The selectable words for one language are the tokens from that language's `text` plus that language's `distractors`.
- Include enough distractors to make this a real language decision task, not just word shuffling.
- Distractors should challenge both grammar and meaning when possible.
- Avoid clues from punctuation or capitalization in the available token set.
- Distractors should be plausible, but should not create many extra valid full-sentence translations.
- Prefer replacing a distractor over expanding `accepted`.
- For sentence-builder tagging, prioritize `topic:*` and add `pos:*`, `grammar:*`, and `tense:*` only when they improve targeting precision.

## Rules For `distractors`

Distractors should mainly test:

- tense
- agreement
- pronouns
- noun choice
- adjective choice
- adverb choice
- time or place phrases
- semantic-category meaning distinctions when relevant (for example same-category alternatives)

Distractors should usually avoid:

- near-synonyms of target words
- equally natural paraphrases
- alternate lexical choices that would also be good translations
- contraction variants when the non-contracted form is already used
- misspellings or orthographic trap options

General rule:

- if we do not want to accept a wording, we should not include the needed replacement token in `distractors`

## Rules For `accepted`

`accepted` is derived from the available token set on the other side.

For language B, `accepted` should only contain other meaningful translations of language A `text` that can be built from:

- language B `text`
- language B `distractors`

In practice, `accepted` should usually be limited to:

- valid alternate word order
- intentional direct-valid alternates that are less common but still acceptable (and fully token-pool-supported)

`accepted` should usually not include:

- synonym swaps
- tense or aspect changes
- contraction vs non-contraction
- register shifts
- alternate lexical choices introduced by distractors

Every non-empty `accepted` entry should be classifiable as one of:

- `word_order`
- `direct_alt`

If an accepted item cannot be justified by one of these reasons, remove it or adjust distractors.


## Review Check

For each question and each language:

1. Is `text` the most direct natural translation of the paired `text`?
2. Do the available words create another meaningful translation?
3. If yes, is it a case we intentionally want to accept?
4. If not, should a distractor be replaced or removed?
5. If `accepted` is non-empty, can each item be labeled `word_order` or `direct_alt`?


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

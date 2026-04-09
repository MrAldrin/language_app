# Word Translation Question Rules

This document is the type-specific spec for `word_translation`.
For shared rules across all question types, see `docs/question_generation_common_rules.md`.

These rules should work across the language pairs used in the app, especially Norwegian, German, and Dutch.

## Schema

Use the current JSON file schema in `apps/public/*/single_word_translation.json`.

Each question object must contain:

- `id`: sequential integer
- `question_type`: must be `word_translation`
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced tags (`namespace:value`), following shared rules in `docs/question_generation_common_rules.md`
- `content`:
  - `response_mode`: must be `single_token_choice`
- `translations`: keyed by language code

Each `translations.<lang>` object should usually contain:

- `text`: canonical target word or short form for that language
- `accepted`: other intentionally accepted single-token answers
- `distractors`: extra selectable tokens used to test the learner

Optional fields:

- `hint`: display-only disambiguation when the form is ambiguous


## Type-Specific Authoring Rules

- Treat the two `text` fields as the main translation pair. Each `text` should be the most direct, standard form we want the learner to choose.
- Word translation is bidirectional. Each side should be reviewed against the other side.
- The selectable options for one language are that language's `text` plus its `distractors`.
- Use `hint` only to clarify ambiguity such as gender, number, formality, or case when the displayed form alone is not specific enough.
- Do not put display-only clarification inside `text` or `accepted`.
- Distractors should be plausible near-misses from the same grammar family when possible.
- `text` is the preferred answer. `accepted` is only for other forms we intentionally want to allow from the available token pool.
- For word-translation tagging, prioritize `family:*`, `pronoun_type:*`, and the most useful disambiguators such as `person:*`, `number:*`, `role:*`, `gender:*`, `case:*`, and `deixis:*`.

## Rules For `distractors`

Distractors should mainly test:

- pronoun role or case
- person
- number
- gender
- deixis
- closely related inflectional contrasts

Distractors should usually avoid:

- tokens that create many equally good accepted answers unless that ambiguity is intentional
- loose synonyms that change the teaching target
- register variants we do not want to accept
- spelling or style variants when one canonical form is preferred
- alternate lexical choices that would force us to grow `accepted` just to compensate for the pool

General rule:

- if we do not want to accept a token, we should not include the needed replacement token in `distractors`

## Rules For `accepted`

`accepted` should stay small and intentional.

For language B, `accepted` should only contain other valid answers to language A `text` that can be built from:

- language B `text`
- language B `distractors`

In practice, `accepted` is appropriate for:

- equally valid surface variants we intentionally want to accept
- tightly related inflectional forms when the item is teaching a lemma-level correspondence
- standard short or unstressed variants that are common and genuinely interchangeable for this item
- a very small set of canonical alternates that the available token pool makes unavoidably correct and that we explicitly want to allow

`accepted` should usually not include:

- broad synonym sets
- alternate lexical choices introduced by distractors
- paraphrases that change the target meaning or usage
- tense, case, gender, number, register, or role changes unless that contrast is the point of the item
- extra variants added only to compensate for an overly broad distractor pool

If too many alternatives become correct, prefer replacing a distractor over expanding `accepted`.

This follows the same cleanup principle used for sentence builder:

- `text` is the main answer
- `accepted` is not a catch-all for every plausible alternative
- distractors should not create extra correct answers unless we intentionally want them

## Review Check

For each question and each language:

1. Is `text` the clearest canonical answer for this item?
2. Do the available tokens create another valid answer?
3. If yes, is it a variant we intentionally want to teach or allow?
4. If not, should a distractor be replaced or removed?
5. If a variant is accepted, does `hint` still clearly communicate the intended distinction?

## Example

```json
{
  "id": 3002,
  "question_type": "word_translation",
  "difficulty": 1,
  "tags": ["family:pronoun", "person:2", "number:singular", "pronoun_type:personal", "role:subject"],
  "content": {
    "response_mode": "single_token_choice"
  },
  "translations": {
    "nl": {
      "text": "jij",
      "accepted": ["je"],
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

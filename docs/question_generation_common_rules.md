# Question Generation Common Rules

This is the shared, high-level ruleset for all question generation in the language app.


## Schema

Each question object must include:

- `id`: sequential integer
- `question_type`: discriminator for interaction type
- `difficulty`: integer `1-10`
- `tags`: canonical namespaced labels (`namespace:value`)
- `translations`: language payload(s) used by that question type

Common translation payload fields:

Each `translations.<lang>` object must contain:
- `text`: canonical text in that language
- `accepted`: alternative correct translations that are never used as questions
- `distractors`: 3-6 in clearly wrong-but-plausible distractors

Type-specific payload fields:

- `hint`: used by `word_translation`
- `content`: used by `cloze_word_choice`
- `hidden_word_index`: used by `cloze_word_choice`


## General authoring Rules

- Keep grammar and spelling correct in every language.
- Use correct written characters and orthography for each language (for example `kjørte`, not `kjorte`; `fløy`, not `floy`).
- Do not replace language-specific characters with ASCII approximations.
- Prefer natural, modern phrasing.


## Definitions:
- Token set: All the possible words the user can choose from.
  - sentence building and word translation: all the words of "text" and "distractors"
  - cloze: the word in the sentence with the index listed + "distractors"


## Detailed description of the fields
This part explains the intent of the fields and the rules they have to follow


### distractors:
Distractors are:
  - extra tokens so to make the learner chose the correct answer among other alternatives. 
  - Should be 3-6 in total
  - Should contain alternatives that tests the users knowledge of the words in the "tags". 
  - Should always contain clearly wrong-but-plausible distractors
  - Avoid clues from punctuation or capitalization in the available token set.

Distractors should NEVER contain:

- misspellings 
- synonyms
- contractions
- orthographic trap options


### accepted:

Valid translations of the "text" field in the other language that can be created from the token set.

This should only be due to:
- valid alternate word order
- a subset of the words from "text" could also be a valid translation


## Canonical Tag System

All tags must follow:

- `namespace:value`

Recommended namespaces:

- `family:*` (for broad families, e.g. `family:pronoun`)
- `pronoun_type:*` (e.g. `pronoun_type:personal`)
- `case:*`, `person:*`, `number:*`, `role:*`, `gender:*`, `register:*`, `deixis:*`
- `tense:*`, `pos:*`, `grammar:*`
- `topic:*` (domain/theme labels)
- `feature:*` (non-topic semantic distinctions)

Tag policy notes:

- Keep tags concise and high-signal; avoid redundant synonyms when one canonical tag already captures meaning.


General namespace intent:

- `topic:*` = scenario/domain context (`topic:travel`, `topic:family`)
- `pos:*` = part-of-speech focus (`pos:verb`, `pos:adjective`, `pos:pronoun`)
- `grammar:*` = grammar intent (`grammar:question`, `grammar:negation`)
- `tense:*` = tense dimension (`tense:present`, `tense:past`, `tense:future`)
- `feature:*` = non-topic semantic distinctions used when they add targeting value


## File Families and Naming

### Pair-based files (bilingual)

Stored under `apps/public/<lang1>_<lang2>/`:

- `sentence_builder.json`
- `single_word_translation.json`


### Language-based files (monolingual)

Stored under `apps/public/<lang>/`:

- `cloze_word.json`


## Type-Specific Specs

- Sentence builder: `docs/sentence_builder_rules.md`
- Word translation: `docs/single_word_translation_rules.md`
- Cloze word choice: `docs/cloze_word_rules.md`

# Sentence Builder Translation Cleanup Plan

## Goal

For sentence builder questions, each language should have:

- one canonical `text`
- one direct and natural translation pair
- a small `accepted` list used only when the available words allow another valid answer

To keep this simple:

- `text` is the main answer
- `accepted` is mostly for valid alternate word order
- `distractors` should test the learner without creating lots of extra correct sentences

This should work across the languages we use in the app:

- Norwegian
- English
- Dutch
- German

So the rules should stay as language-agnostic as possible, with only a few language-specific defaults when they are truly needed.

## Main Problems In The Current File

In [sentence_builder.json](/home/hsa/projects/language_app_workspace_2/apps/public/en_no/sentence_builder.json), `accepted` is currently doing too many jobs.

Good use:

- question `14` English
- `text`: `They often travel to Spain`
- `accepted`: `They travel to Spain often`
- This should stay, because the same words can form more than one correct sentence.

Problematic uses:

- synonym swap
  - question `1` English
  - `happy` vs `glad`
- tense/aspect shift
  - question `2` English
  - `She reads...` vs `She is reading...`
- contraction variant
  - question `20` English
  - `do not` vs `don't`

These alternatives make the dataset harder to maintain and make the target less clear for the learner.

## Rules

### 1. `text` is the preferred sentence

For each language, `text` should be:

- the most direct translation of the paired `text`
- natural in that language
- the version we most want the learner to build

### 2. Distractors define the answer space

Distractors should test:

- tense
- agreement
- pronouns
- noun choice
- adjective choice
- adverb choice
- time or place phrases

But they should avoid:

- near-synonyms
- equally natural paraphrases
- contraction variants

General rule:

- if we do not want to accept a wording, we should not include the needed replacement word in the pool

Language-specific rules should be kept to a minimum.

Example:

- prefer non-contracted forms in `text`
- do not include the contracted variant in the same pool

This kind of language-specific rule should only be added when it clearly simplifies authoring across the dataset.

### 3. `accepted` is derived from `text` + `distractors`

`accepted` should only contain other meaningful translations of language 1 `text` that can be built from all words in language 2 `text` plus language 2 `distractors`.

In practice, this usually means:

- valid alternate word order

It usually should not include:

- synonym swaps
- tense or aspect changes
- contraction vs non-contraction
- alternate lexical choices created by distractors

## Bidirectional Review Logic

Sentence builder is bidirectional, so each question should be checked from both sides.

For one language at a time:

1. Start with that language's `text`.
2. Look at the paired `text` in the other language.
3. Combine the target-side `text` words with its `distractors`.
4. Ask: can those available words form another valid translation of the source-side `text`?

If yes:

- keep it in `accepted` only if it is a valid alternative we intentionally want, usually word order
- otherwise replace or remove the distractor that made it possible

## What To Update

review [sentence_builder.json](/home/hsa/projects/language_app_workspace_2/apps/public/en_no/sentence_builder.json) using the bidirectional check above

## Review Checklist

For each question and each language:

1. Is `text` the most direct natural translation of the paired `text`?
2. Does any `accepted` item exist only because of word order?
3. Does any `accepted` item introduce a synonym, contraction, or tense shift?
4. Does any distractor make another good full-sentence translation possible?
5. Can we simplify the pool instead of growing `accepted`?

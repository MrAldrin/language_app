# Tag Canonicalization Master Checklist

## Summary

This document tracks the full hard-cutover migration to canonical namespaced tags.
Work is done file-by-file in small batches.
A file is only marked complete after mapping, validation, and app filter sanity checks pass.

Default migration order:
1. `de` cloze
2. `nl` cloze
3. word translation files
4. sentence builder files
5. docs

## 1. Canonical Tag Model

All tags must use the format `namespace:value`.

Allowed canonical namespaces and typical values:

- `family:*` (e.g. `family:pronoun`)
- `pronoun_type:*` (e.g. `pronoun_type:personal`, `pronoun_type:relative`)
- `case:*` (`case:nominative`, `case:accusative`, `case:dative`, `case:genitive`, `case:locative`)
- `person:*` (`person:1`, `person:2`, `person:3`)
- `number:*` (`number:singular`, `number:plural`, `number:dual`)
- `role:*` (`role:subject`, `role:object`, `role:independent`)
- `gender:*` (`gender:masculine`, `gender:feminine`, `gender:neuter`)
- `register:*` (`register:formal`)
- `deixis:*` (`deixis:proximal`, `deixis:distal`)
- `tense:*` (`tense:present`, `tense:past`, `tense:future`)
- `pos:*` (`pos:verb`, `pos:adjective`, `pos:pronoun`)
- `grammar:*` (`grammar:question`, `grammar:negation`)
- `topic:*` (domain/theme tags such as `topic:travel`, `topic:food`, `topic:weather`)
- `feature:*` (non-redundant semantics, e.g. `feature:quantity`, `feature:reason`)

Hard-cutover rule:
- No backward-compatible legacy tags retained in data files.

Deprecated helper tags to remove:
- `ownership`
- `questioning`
- `pointing`
- `linking`
- `self-reference`

## 2. Deterministic Mapping Table (Legacy -> Canonical)

Core pronoun/family mapping:

- `pronoun` -> `family:pronoun`
- `pronouns` -> `family:pronoun`
- `personal` -> `pronoun_type:personal`
- `possessive` -> `pronoun_type:possessive`
- `reflexive` -> `pronoun_type:reflexive`
- `demonstrative` -> `pronoun_type:demonstrative`
- `relative` -> `pronoun_type:relative`
- `interrogative` -> `pronoun_type:interrogative`
- `indefinite` -> `pronoun_type:indefinite`
- `reciprocal` -> `pronoun_type:reciprocal`
- `distributive` -> `pronoun_type:distributive`
- `emphatic` -> `pronoun_type:emphatic`

Grammar mapping:

- `accusative` -> `case:accusative`
- `dative` -> `case:dative`
- `genitive` -> `case:genitive`
- `nominative` -> `case:nominative`
- `locative` -> `case:locative`
- `1st_person` -> `person:1`
- `2nd_person` -> `person:2`
- `3rd_person` -> `person:3`
- `singular` -> `number:singular`
- `plural` -> `number:plural`
- `dual` -> `number:dual`
- `subject` -> `role:subject`
- `object` -> `role:object`
- `independent` -> `role:independent`
- `masculine` -> `gender:masculine`
- `feminine` -> `gender:feminine`
- `neuter` -> `gender:neuter`
- `formal` -> `register:formal`
- `small` -> `deixis:proximal`
- `large` -> `deixis:distal`
- `distance` -> `deixis:distal`
- `distancing` -> `deixis:distal`
- `present_tense` -> `tense:present`
- `past_tense` -> `tense:past`
- `future_tense` -> `tense:future`
- `verbs` -> `pos:verb`
- `adjectives` -> `pos:adjective`
- `questions` -> `grammar:question`
- `negation` -> `grammar:negation`

Legacy semantic/theme mapping notes:

- Use `topic:*` for lexical themes (e.g. `travel`, `food`, `weather`, `work`, `family`).
- Use `feature:*` for non-topic semantic distinctions (e.g. `quantity`, `reason`, `manner`, `selection`, `person`, `thing`, `choice`, `partial`, `totality`).
- Any unmapped legacy tag blocks completion and must be added here before migration continues.

## 3. File-by-File Checklist

### Data Files

#### `apps/public/de/cloze_word_choice_questions.json`
- [x] mapped
- [x] validated (schema/tag format)
- [x] app filter sanity checked
- [x] docs/examples updated if impacted (not impacted in this phase)

#### `apps/public/nl/cloze_word_choice_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/de_no/word_translation_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/nl_no/word_translation_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/de_en/sentence_builder_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/de_nl/sentence_builder_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/de_no/sentence_builder_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/en_nl/sentence_builder_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/en_no/sentence_builder_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

#### `apps/public/nl_no/sentence_builder_questions.json`
- [ ] mapped
- [ ] validated (schema/tag format)
- [ ] app filter sanity checked
- [ ] docs/examples updated if impacted

### Docs to Update After Data Migration

#### `docs/question_generation_overview.md`
- [ ] mapped to canonical terminology
- [ ] validated examples
- [ ] app filter sanity checked (if examples referenced in tests)
- [ ] docs/examples updated if impacted

#### `docs/cloze_questions.md`
- [ ] mapped to canonical terminology
- [ ] validated examples
- [ ] app filter sanity checked (if examples referenced in tests)
- [ ] docs/examples updated if impacted

#### `docs/targeted_questions.md`
- [ ] mapped to canonical terminology
- [ ] validated examples
- [ ] app filter sanity checked (if examples referenced in tests)
- [ ] docs/examples updated if impacted

#### `docs/content_generation_rules.md`
- [ ] mapped to canonical terminology
- [ ] validated examples
- [ ] app filter sanity checked (if examples referenced in tests)
- [ ] docs/examples updated if impacted

## 4. Per-File Validation Checklist (Completion Gate)

A file can only be marked complete when all checks below pass:

1. All tags are namespaced and valid: `namespace:value`.
2. No deprecated helper tags remain:
   - `ownership`
   - `questioning`
   - `pointing`
   - `linking`
   - `self-reference`
3. No unmapped legacy tags remain.

Suggested commands/checks:
- JSON parse succeeds.
- Regex check for tag format.
- Tag inventory check confirms only canonical namespaces.

## 5. Batch and Final Test Scenarios

Batch-level checks (after each 1-2 files):
1. App starts successfully.
2. Focus-tag dropdown shows expected canonical tags for edited file.
3. Filtering by canonical tags returns expected subsets.

Final checks:
1. All checklist boxes completed.
2. Docs reflect canonical taxonomy and examples.

## 6. Rollup Progress

Data files total: 10
- Completed: 1
- Remaining: 9

Docs total: 4
- Completed: 0
- Remaining: 4

Overall total items: 14
- Completed: 1
- Remaining: 13

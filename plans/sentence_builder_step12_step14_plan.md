# Sentence Builder Step 12 + Step 14 Plan

This plan extends `plans/sentence_builder_execution_checklist.md` with a practical workflow for:

- Step 12: manual language-quality review
- Step 14: lexical-substitution heuristic redesign

## Step 12: Manual Language-Quality Review

## Goal

Validate that aggressive cleanup did not remove intentional, high-value alternates and that each item still follows current authoring rules.

## Scope

Review all 6 files:

- `apps/public/de_en/sentence_builder.json`
- `apps/public/de_nl/sentence_builder.json`
- `apps/public/de_no/sentence_builder.json`
- `apps/public/en_nl/sentence_builder.json`
- `apps/public/en_no/sentence_builder.json`
- `apps/public/nl_no/sentence_builder.json`

## Review Strategy

Use a two-pass approach:

1. Fast pass (coverage): scan all questions for obvious regressions.
2. Deep pass (quality): review flagged candidates in detail.

## What To Check Per Question

For each language side (`translations.<lang>`):

1. `text` quality
- Is it the most direct natural translation of the paired `text`?
- Is register/word choice appropriate for beginner/intermediate learners?

2. `accepted` necessity
- Is every accepted item still intentionally allowed?
- Does it represent word-order flexibility rather than lexical/tense drift?

3. `distractors` quality
- Are distractors plausible but not enabling unwanted full alternatives?
- Are any distractors now too weak or too easy after cleanup?

4. Bidirectional consistency
- If side A is canonical, does side B remain pedagogically aligned?
- Avoid hidden asymmetry where one side became overly strict vs the other.

## Sampling + Prioritization

Prioritize in this order:

1. Items recently edited by cleanup script.
2. Items with previously high warning density (tense/contraction clusters).
3. Remaining items by random sample, then full sweep.

Recommended batching:

- Batch A: 10 questions per file (60 total)
- Batch B: next 10 per file
- Continue until full coverage

## Step 12 Deliverables

Create:

- `plans/reports/sentence_builder_manual_review_log.md`

Log format per reviewed item:

- file path
- question id
- language side
- decision: `keep`, `restore_alt`, `adjust_distractor`, `rewrite_text`
- rationale (1-2 lines)
- status: `done`

If a fix is needed, apply immediately in small commits/checkpoints and rerun audit.

## Step 12 Exit Criteria

- Full dataset manually reviewed.
- Any intentional alternates that were wrongly removed are restored.
- No reintroduced audit errors/warnings.
- Review log complete and traceable.

## Step 14: Lexical-Substitution Heuristic Redesign

## Goal

Re-enable lexical-substitution detection with high precision so warnings are useful (low false positives).

## Current Problem

The first lexical heuristic over-flagged heavily because token-difference alone cannot separate:

- acceptable style/register variation
- acceptable lexical alternates
- true unintended synonym/paraphrase drift

## Redesign Principles

1. Precision over recall
- Better to miss some cases than flood warnings.

2. Language-aware gating
- Apply per-language patterns/rules where needed.

3. Multi-signal detection
- Do not warn based on a single token-set diff.

## Proposed Detection Pipeline

Only emit lexical warning when all gates pass:

1. Constructibility gate
- `accepted` must be token-pool-valid.

2. Not word-order gate
- normalized bag-of-words differs from `text`.

3. Not tense/contraction gate
- candidate not already explained by tense/contraction detector.

4. Lexical-change gate
- at least one content-word substitution (noun/verb/adj/adv), not only function words.

5. Confidence gate
- substitution confidence score above threshold.

## Implementation Plan (Step 14)

1. Build small gold set
- Create `plans/reports/lexical_heuristic_goldset.json`.
- Include true positives and true negatives from real dataset examples.

2. Add explainable scoring output
- For each candidate warning, store why it fired (rules matched).

3. Add `--enable-lexical-heuristic` flag
- Keep default OFF until calibrated.

4. Tune threshold on gold set
- target: high precision (for example >= 0.85) before enabling by default.

5. Reintroduce as warning only
- Keep severity as warning.
- Reassess after several content update cycles.

## Step 14 Deliverables

- Update `scripts/audit_sentence_builder.py` with gated lexical heuristic.
- Add optional flag and debug reason output in JSON report.
- Add calibration notes in:
  - `plans/reports/lexical_heuristic_calibration.md`

## Step 14 Exit Criteria

- Lexical heuristic is re-enabled in controlled mode.
- Warning volume remains actionable.
- False-positive rate is demonstrably lower than the first version.

## Suggested Execution Order

1. Finish Step 12 manual review first.
2. Lock dataset state.
3. Execute Step 14 redesign/calibration.
4. Re-run full audit and record final metrics.

# Sentence Builder Step 12 + Step 14 Plan

This plan extends `plans/sentence_builder_execution_checklist.md` with a practical workflow for:

- Step 12: manual language-quality review
- Step 14: lexical-substitution heuristic redesign

## Data Policy Baseline

Before executing Step 12 and Step 14, use this contract:

1. `text` policy
- `text` is the preferred answer.
- `text` should be the most direct and natural translation of the paired sentence.

2. `distractors` policy
- Distractors should make the task a real language decision task, not only token reordering.
- Distractors should increase difficulty without tricking users.
- Do not rely on misspellings, orthographic traps, or noisy decoys.
- Prefer plausible alternatives that test grammar and meaning.
- Where appropriate, prefer distractors from the same semantic class as target words, so learners must identify correct meaning (not just grammar shape).

3. `accepted` policy (only two allowed reasons)
- Primary reason: alternative valid sentence from the same token pool, most often alternate word order.
- Secondary reason: intentional direct-valid alternate phrasing that is less common but still acceptable, with required tokens present in the pool.
- If an accepted variant does not fit one of these reasons, remove it.

## Future-Proof Tracking (Accepted Complexity)

Because `accepted` entries are highest-risk during cleanup, every run must produce explicit accepted-complexity metrics.

## Metrics To Record Each Run

For each file and total dataset:

- `questions_total`
- `questions_with_accepted`
- `accepted_coverage_pct` = questions with non-empty accepted / total
- `accepted_items_total`
- `avg_accepted_items_per_question`
- `questions_with_2plus_accepted`
- `question_ids_by_accepted_count`:
  - IDs with exactly 1 accepted item
  - IDs with exactly 2 accepted items
  - IDs with exactly 3 accepted items
  - continue for higher counts if present
- `accepted_by_reason`:
  - `word_order`
  - `direct_alt`
  - `unknown` (must be reviewed)

## Artifacts

Create and maintain:

- `plans/reports/sentence_builder_accepted_inventory.json`
- `plans/reports/sentence_builder_accepted_inventory.md`

These become standard outputs so future cleanups start from measured complexity instead of manual rediscovery.

## Step 12: Manual Language-Quality Review

## Goal

Validate that cleanup did not remove needed alternates and that remaining data follows the policy baseline.

## Scope

Review all 6 files:

- `apps/public/de_en/sentence_builder.json`
- `apps/public/de_nl/sentence_builder.json`
- `apps/public/de_no/sentence_builder.json`
- `apps/public/en_nl/sentence_builder.json`
- `apps/public/en_no/sentence_builder.json`
- `apps/public/nl_no/sentence_builder.json`

## Review Strategy

Use two passes:

1. Coverage pass: fast scan across all questions for obvious regressions.
2. Accepted-focused pass: full review of all non-empty `accepted` entries with explicit reason labeling.

## What To Check Per Question

For each language side (`translations.<lang>`):

1. `text` quality
- Is this the best direct-natural translation of the paired sentence?
- Is register level appropriate for the target learner level?

2. `accepted` validity
- Is each accepted item explicitly `word_order` or `direct_alt`?
- Is each accepted item constructible from `text + distractors`?
- If not, either remove accepted item or repair token pool.

3. `distractors` quality
- Do distractors test grammar and/or meaning without introducing confusion?
- Do distractors avoid creating many unintended full-sentence alternatives?

4. Bidirectional consistency
- Are strictness and naturalness balanced across both language sides?
- Avoid one side becoming much stricter than its pair.

## Prioritization

Review order:

1. All questions with non-empty `accepted` (mandatory).
2. Questions changed by recent cleanup automation.
3. Remaining questions in fixed-size batches (for example, 10 per file) until complete.

## Step 12 Deliverables

Create:

- `plans/reports/sentence_builder_manual_review_log.md`

Log format per reviewed item:

- file path
- question id
- language side
- accepted reason: `word_order`, `direct_alt`, `none`, `unknown`
- decision: `keep`, `restore_alt`, `adjust_distractor`, `rewrite_text`, `remove_accepted`
- rationale (1-2 lines)
- status: `done`

If a fix is needed, apply it in small checkpoints and rerun audit.

## Step 12 Exit Criteria

- Full dataset reviewed.
- All non-empty accepted entries have reason labels.
- Any wrongly removed intentional alternatives are restored.
- No reintroduced audit errors/warnings.
- Review log is complete and traceable.

## Step 14: Lexical-Substitution Heuristic Redesign

## Goal

Re-enable lexical-substitution detection with high precision and low false-positive noise.

## Current Problem

Token-difference-only logic over-flags because it cannot reliably separate:

- harmless variation
- intentional direct alternates
- unintended lexical drift

## Redesign Principles

1. Precision over recall.
2. Language-aware gating.
3. Multi-signal detection (no single-rule warning).
4. Alignment with accepted reasons (`word_order`, `direct_alt`).

## Proposed Detection Pipeline

Emit lexical warning only when all gates pass:

1. Constructibility gate
- accepted candidate is token-pool-valid.

2. Not word-order gate
- normalized bag-of-words differs from `text`.

3. Not tense/contraction gate
- candidate not already explained by other detectors.

4. Content-word substitution gate
- lexical change affects content words (not only function words).

5. Accepted-reason gate
- suppress warning if candidate is labeled as intentional `direct_alt`.

6. Confidence gate
- score exceeds calibrated threshold.

## Implementation Plan (Step 14)

1. Build gold set
- Create `plans/reports/lexical_heuristic_goldset.json`.
- Include true positives, true negatives, and intentional `direct_alt` examples.

2. Add explainable scoring
- For each lexical warning, log gate decisions and confidence contributors.

3. Add feature flag
- `--enable-lexical-heuristic` (default OFF during calibration).

4. Tune threshold
- Target high precision (for example >= 0.85).

5. Re-enable in warning mode
- Keep lexical findings as warnings.

6. Integrate accepted inventory metrics
- Include accepted-complexity outputs in the same audit run.

## Step 14 Deliverables

- Update `scripts/audit_sentence_builder.py` with gated lexical heuristic.
- Add optional lexical flag and explainability in JSON report.
- Add calibration report:
  - `plans/reports/lexical_heuristic_calibration.md`
- Add accepted inventory outputs listed above.

## Step 14 Exit Criteria

- Lexical heuristic re-enabled in controlled mode.
- Warning volume is actionable.
- False-positive rate is substantially lower than v1.
- Accepted inventory metrics are generated automatically each run.

## Challenges To Expect

1. Cross-language ambiguity
- Some alternates are valid in one pair but not in another.

2. Over-pruning risk
- Useful accepted variants may be removed without explicit reason tracking.

3. Reason-label drift
- If reason labels are skipped, future cleanups repeat the same debates.

4. Authoring drift over time
- New data can reintroduce broad accepted usage unless checks stay automated.

5. Detector overlap
- Tense/contraction/lexical signals can overlap and need deduping.

## Suggested Execution Order

1. Generate accepted inventory metrics.
2. Run Step 12 manual review with reason labeling.
3. Lock dataset state after review.
4. Run Step 14 redesign/calibration.
5. Re-run full audit and record final metrics.

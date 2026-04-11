# Sentence Builder Cleanup Execution Checklist

Use this as the live tracker while we execute `plans/sentence_builder_dataset_audit_plan.md`.

## Rules Of Engagement

- We move in small steps.
- We validate output at each step.
- We check in before moving to the next major step.
- We store progress continuously with `jj`.

## Step-by-step Checklist

- [x] 1. Baseline inventory captured
  - Confirm all target files are detected.
  - Confirm question counts per file.

- [x] 2. Create `scripts/audit_sentence_builder.py` (v1)
  - Implement hard checks: schema, required keys, response mode, translation count.
  - Implement content sanity checks: types, duplicates, empty text.

- [x] 3. Run audit script and generate baseline reports
  - `plans/reports/sentence_builder_audit_report.json`
  - `plans/reports/sentence_builder_audit_summary.md`

- [x] 4. Validate report quality with you
  - Ensure findings are understandable and actionable.
  - Adjust reporting format if needed.

- [x] 5. Add token-pool validity checks
  - Verify each `accepted` sentence can be formed from `text + distractors`.
  - Flag missing/overused tokens.

- [x] 6. Re-run reports and review with you
  - Confirm hard errors vs warnings split is correct.

- [x] 7. Add policy-warning heuristics
  - Contraction/non-contraction variants.
  - Likely tense/aspect shifts.
  - Likely lexical/synonym alternates.

- [x] 8. Re-run reports and finalize audit tool (v2)
  - Confirm stable output and practical severity levels.

- [x] 8.1 Add accepted-inventory reporting
  - `plans/reports/sentence_builder_accepted_inventory.json`
  - `plans/reports/sentence_builder_accepted_inventory.md`
  - Include `question_ids_by_accepted_count` and `accepted_by_reason`.

- [x] 9. Create cleanup backlog from report
  - `plans/sentence_builder_cleanup_backlog.md`
  - Group by file and priority.

- [x] 10. Start cleanup pass 1 (hard errors first)
  - Make minimal edits.
  - Re-run audit after each file or small batch.
  - NEW: Bulk removed 360 `accepted` items that used distractors to align with new strict policy.

- [x] 11. Cleanup pass 2 (high-confidence policy fixes)
  - Remove/replace distractors that create unwanted alternates.
  - Keep `accepted` minimal and intentional.
  - Bulk cleanup completed for all 6 files.

- [ ] 12. Manual language-quality pass
  - Accepted-first review: all non-empty `accepted` entries are reason-labeled (`word_order` / `text_subset` / `unknown`).
  - Review naturalness and direct translation quality.
  - Confirm distractors test language knowledge (not only word shuffling).
  - STRICT CHECK: Confirm no `accepted` items use words from the `distractors` pool.
  - NEW: Replace near-synonym distractors identified during bulk cleanup to prevent "valid but unaccepted" answers.

- [x] 13. Final verification
  - Re-run audit and confirm Definition of Done criteria.

- [ ] 14. Follow-up: redesign lexical-substitution heuristic
  - Reduce false positives while still catching true synonym/lexical swaps.
  - Re-enable only after validation on a representative sample.

- [ ] 15. Docs alignment pass
  - Update `docs/sentence_builder_rules.md` to match accepted-reason policy (word_order/text_subset) and accepted complexity tracking.
  - Update `docs/question_generation_common_rules.md` only if shared wording needs alignment.
  - Confirm no policy conflict between `docs/` and `plans/`.

## Live Progress Log

- Status: `In progress`
- Current step: `12`
- Notes:
  - Step 1 complete: detected 6 sentence-builder files.
  - Step 1 complete: each file currently has 50 questions (300 total).
  - Step 2 complete: added `scripts/audit_sentence_builder.py` with hard schema checks + basic sanity checks.
  - Step 2 complete: script compiles successfully (`uv run python -m py_compile scripts/audit_sentence_builder.py`).
  - Step 3 complete: smoke test run on `apps/public/en_no/sentence_builder.json` (50 questions, 0 findings).
  - Step 3 complete: full baseline run on all 6 files (300 questions, 0 findings).
  - Baseline reports written to `plans/reports/sentence_builder_audit_report.json` and `plans/reports/sentence_builder_audit_summary.md`.
  - Step 4 complete: report outputs look usable (`.json` + concise `.md` summary).
  - Step 5 complete: token-pool constructibility checks added.
  - Current findings after Step 5: 3 token-pool errors (all question `id=47`, language `nl` in `de_nl`, `en_nl`, `nl_no`).
  - Step 6 complete: confirmed token-pool findings are true positives (apostrophe token issue).
  - Step 7 complete: added heuristic warnings (contraction variants, likely tense/aspect shifts, likely lexical substitutions).
  - Current heuristic output is very noisy: 588 warnings (463 lexical-substitution, 119 tense/aspect, 6 contraction).
  - Step 8 calibration in progress: lexical-substitution warnings disabled temporarily due to high false-positive rate.
  - Follow-up captured as Step 14 to redesign and re-enable lexical-substitution heuristic later.
  - Step 8 complete: warnings reduced from 588 to 125 after disabling lexical heuristic.
  - Current warning mix is focused: 119 tense/aspect + 6 contraction/non-contraction.
  - Step 9 complete: generated `plans/sentence_builder_cleanup_backlog.md` from current audit report.
  - Backlog totals: 128 items (P0: 3, P1: 125, P2: 0).
  - Step 10 complete: fixed all 3 P0 token-pool errors for `id=47` on Dutch side in `de_nl`, `en_nl`, `nl_no`.
  - Current audit status: errors=0, warnings=125.
  - Step 11 batch 1 complete: resolved all 6 contraction/non-contraction warnings (files `de_en`, `en_nl`, `en_no`, ids `20` and `37` on `en` side).
  - Current audit status after batch 1: errors=0, warnings=113 (all are tense/aspect warnings).
  - Step 11 batch 2 complete: resolved tense/aspect warnings for `id=2,3,4` on `en` side in `de_en`, `en_nl`, and `en_no`.
  - Current audit status after batch 2: errors=0, warnings=104.
  - Step 11 final cleanup complete: removed remaining tense/aspect-shift `accepted` entries across all six files.
  - Bulk cleanup impact: 104 `accepted` items removed across 6 files.
  - Step 13 final verification complete: current audit result is errors=0, warnings=0.
  - Checklist aligned with `plans/sentence_builder_step12_step14_plan.md` (accepted-inventory, accepted-first manual review, docs alignment step).
  - Step 15 complete: updated `docs/sentence_builder_rules.md` to reflect accepted reason policy, distractor intent, and accepted tracking guidance.
  - Step 15 complete: applied minor shared-rule alignment in `docs/question_generation_common_rules.md` (no orthographic trap distractors).
  - Step 8.1 complete: audit script now outputs accepted inventory JSON/MD reports with `question_ids_by_accepted_count` and `accepted_by_reason`.
  - Current accepted inventory totals: 300 questions, 228 with accepted, 372 accepted items, explicit reason counts currently all `unknown` (expected before manual labeling).
  - Step 12 started with file-by-file workflow.
  - Completed first file pass: `apps/public/en_nl/sentence_builder.json` logged in `plans/reports/sentence_builder_manual_review_log.md` (52 accepted items reviewed).

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

- [ ] 8. Re-run reports and finalize audit tool (v2)
  - Confirm stable output and practical severity levels.

- [ ] 9. Create cleanup backlog from report
  - `plans/sentence_builder_cleanup_backlog.md`
  - Group by file and priority.

- [ ] 10. Start cleanup pass 1 (hard errors first)
  - Make minimal edits.
  - Re-run audit after each file or small batch.

- [ ] 11. Cleanup pass 2 (high-confidence policy fixes)
  - Remove/replace distractors that create unwanted alternates.
  - Keep `accepted` minimal and intentional.

- [ ] 12. Manual language-quality pass
  - Review naturalness and direct translation quality.

- [ ] 13. Final verification
  - Re-run audit and confirm Definition of Done criteria.

## Live Progress Log

- Status: `In progress`
- Current step: `8`
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

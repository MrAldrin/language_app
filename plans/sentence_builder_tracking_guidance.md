# Sentence Builder Tracking Guidance

This file contains tracking and reporting guidance for sentence-builder cleanup cycles.
It is intentionally separate from `docs/sentence_builder_rules.md`, which is focused on content creation rules.

## Purpose

Track `accepted` complexity and cleanup risk so future dataset updates are measurable and repeatable.

## Required Metrics Per Run

For each file and the total dataset:

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
  - `unknown`

## Report Artifacts

Generate and maintain:

- `plans/reports/sentence_builder_accepted_inventory.json`
- `plans/reports/sentence_builder_accepted_inventory.md`

## Usage In Cleanup Workflow

1. Generate inventory metrics before manual review.
2. Use inventory to prioritize high-risk questions (`accepted` non-empty, especially 2+ variants).
3. After edits, regenerate metrics and compare deltas.
4. Keep metrics snapshots with each major cleanup cycle.

## Notes

- `accepted` reason labels (`word_order` / `direct_alt`) should be logged during manual review.
- `unknown` should be treated as mandatory follow-up.

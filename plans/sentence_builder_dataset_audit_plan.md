# Sentence Builder Dataset Audit Plan

## Why This Plan

We now have updated rules in:

- `docs/question_generation_common_rules.md`
- `docs/sentence_builder_rules.md`

The existing sentence-builder datasets were authored before those rules were finalized.
This plan defines a repeatable process to audit and clean all `sentence_builder.json` files.

## Scope

Files in scope:

- `apps/public/en_no/sentence_builder.json`
- `apps/public/en_nl/sentence_builder.json`
- `apps/public/de_en/sentence_builder.json`
- `apps/public/de_nl/sentence_builder.json`
- `apps/public/de_no/sentence_builder.json`
- `apps/public/nl_no/sentence_builder.json`

Current size:

- 6 files
- 50 questions per file
- 300 total question objects

## Recommendation: Hybrid (Script + Manual Review)

Use a hybrid approach:

1. Scripted audit for deterministic checks and issue reporting.
2. Manual language review for naturalness and translation quality.

Why not script-only:

- Naturalness and “most direct translation” require language judgment.
- Some `accepted` items are intentional and cannot be auto-decided safely.

Why not manual-only:

- 300 questions is enough to miss consistency issues.
- We want reusable guardrails for future content updates.

## Audit Rules To Enforce

Derived from `docs/sentence_builder_rules.md`:

1. Schema and structural validity
- required keys exist (`id`, `question_type`, `difficulty`, `tags`, `content`, `translations`)
- `question_type == "sentence_builder_multiple_choice"`
- `content.response_mode == "token_sequence_choice"`
- exactly 2 translation languages per question

2. Basic content sanity
- `text` is non-empty
- `accepted` and `distractors` are arrays
- no duplicate entries in `accepted`/`distractors`
- `text` should not be duplicated inside `accepted`

3. Token-pool consistency
- each `accepted` sentence must be constructible from `text + distractors` token multiset
- flag tokens in `accepted` that are not present in the available token pool

4. Heuristic policy warnings (not hard errors)
- `accepted` looks like synonym/lexical swap rather than word-order variant
- contraction/non-contraction alternation in `accepted`
- tense/aspect shifts in `accepted`
- distractors likely enabling alternate full translations

5. Tag policy checks
- every tag uses `namespace:value`
- warn on legacy/unnamespaced tags

## Deliverables

### 1. Audit script

Create:

- `scripts/audit_sentence_builder.py`

Script behavior:

- scan all `apps/public/*/sentence_builder.json`
- emit machine-readable report:
  - `plans/reports/sentence_builder_audit_report.json`
- emit human-readable summary:
  - `plans/reports/sentence_builder_audit_summary.md`
- exit code:
  - non-zero on hard schema/content errors
  - zero when only warnings are present

### 2. Triage board

Create:

- `plans/sentence_builder_cleanup_backlog.md`

Backlog format per finding:

- file path
- question id
- language side (`en`/`no`/`de`/`nl`)
- finding type (`schema_error`, `token_pool_error`, `accepted_policy_warning`, etc.)
- proposed action (`remove distractor`, `replace distractor`, `move variant to text`, `drop accepted item`)
- status (`todo`, `in_progress`, `done`)

### 3. Cleanup pass strategy

Order of operations:

1. Fix hard errors first (schema/token-pool invalid).
2. Resolve high-confidence policy issues (contraction and clear tense shift variants).
3. Manually review remaining warnings for naturalness and directness.

## Execution Phases

### Phase 0: Baseline safety

- work in small step-by-step changes and store progress continuously with `jj`
- run audit script and save baseline report

### Phase 1: Build and validate script

- implement deterministic checks
- run on all 6 files
- confirm the report is stable and readable

### Phase 2: First cleanup iteration

- apply edits for hard errors and clear policy violations
- re-run audit
- ensure hard errors are zero

### Phase 3: Language-quality review

- manually inspect warnings that require linguistic judgment
- keep `accepted` only where alternates are intentionally valid
- prefer adjusting distractors over growing `accepted`

### Phase 4: Lock in future guardrails

- add a lightweight CI/local check command (optional but recommended)
- document usage in `README.md` or a short section in `docs/sentence_builder_rules.md`

## Definition of Done

For all 6 sentence-builder files:

- no schema/content hard errors
- every `accepted` is token-pool-valid
- no accidental synonym/contraction/tense alternatives left in `accepted` unless explicitly intentional
- distractors do not routinely create alternate full translations we do not want
- audit report is clean enough to be used as a release gate

## Future Workflow

For any new or modified `sentence_builder.json`:

1. run `scripts/audit_sentence_builder.py`
2. fix hard errors immediately
3. review warnings with the sentence-builder checklist
4. commit only when the report is clean/acceptable

This gives us consistent quality now and a reusable process for future dataset expansion.

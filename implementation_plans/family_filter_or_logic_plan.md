# Family Filter OR Logic Plan (Conceptual, No Code)

## Summary

This plan updates targeted practice filtering and settings layout to match study intent:
- Use a two-level settings UI.
- Keep first-level settings minimal and always visible.
- Show lower-level settings conditionally based on selected question set capabilities.
- For family-capable sets, use family-first filtering with default-all subtype selection.
- Use OR matching across selected subtype/attribute tags (not strict AND).

This document is planning-only. No implementation changes are made in this step.

## Problem We Are Fixing

Current strict AND behavior is too restrictive for pronoun practice. Example:
- If user selects `family:pronoun` and multiple `pronoun_type:*` values,
- Current filter effectively requires a row to contain all selected subtype tags,
- Most rows only have one pronoun subtype,
- Result: "no questions found" even when many relevant rows exist.

Current settings layout is also too flat:
- Family/subtype controls should not appear for question sets that do not support them.
- `Direction` should be contextual (shown in lower-level settings), not always in top-level controls.

## Target UI Structure

### 1) First-Level Settings (Always Visible)
Only show:
- `Source language`
- `Target language`
- `Question set`
- `Difficulty`

These determine which dataset is loaded and what lower-level options are available.

### 2) Second-Level Settings (Conditional Subsection)
Render a subsection below first-level settings based on selected dataset:
- Include `Direction` only for question types where it applies (for example word translation and sentence builder).
- Do not show `Direction` for cloze question sets.
- If dataset supports family filtering (`family:*` present):
  - Show `Family` dropdown.
  - Show `Subtype / Attributes` multiselect.
- If dataset does not support family filtering:
  - Do not render family/subtype controls.
  - Show only relevant lower-level controls for that question type.

## Target Filter Behavior (Family-Capable Sets)

### 1) Family-First Flow
- If dataset has `family:*`, family selection is the starting filter.
- Family selection defines available subtype/attribute options.

### 2) Default Selection Behavior
- After choosing family, preselect all co-occurring subtype/attribute tags for that family.
- This gives immediate broad practice with zero extra clicks.

### 3) Matching Semantics
- Family condition: required (`row has selected family`).
- Attribute condition: OR (`row has ANY selected attribute`).
- Combined predicate:
  - `row_has_family(selected_family)`
  - AND
  - `row_has_any(selected_attributes)`

### 4) Empty Attribute Selection
- If user deselects all attributes manually, do not return empty.
- Treat empty attribute selection as family-only mode.
- Practical equivalent: apply family predicate alone until at least one attribute is selected.

## Scope by Question Type

- Family-first filtering applies only to datasets containing `family:*` tags (currently canonicalized cloze + word translation).
- Sentence-builder or other non-family datasets:
  - No family/subtype UI controls.
  - Continue with non-family flow using available settings.

## UX Notes

- Keep labels explicit:
  - `Family`
  - `Subtype / Attributes` (multi-select, defaults to all)
- Helper text for family-capable sets:
  - "Subtype/Attributes uses ANY-match. Leave all selected for broad family practice."
- For non-family sets, do not show disabled family controls; hide them entirely to reduce noise.

## Validation Plan (When Implementing)

1. First-level row always shows only source, target, question set, difficulty.
2. Lower section appears with controls relevant to question type.
3. `Direction` is hidden for cloze question sets.
4. Family/subtype controls appear only when selected dataset has `family:*` tags.
5. Selecting `family:pronoun` auto-selects all pronoun-related attributes.
6. With default selections, pronoun datasets return non-empty results.
7. Selecting only `pronoun_type:relative` returns relative pronoun rows.
8. Selecting `pronoun_type:relative` + `case:genitive` returns rows matching either attribute (within selected family).
9. Clearing all attributes still returns family-matching rows.
10. Non-family datasets remain functional with no empty-state regression.

## Rollout Plan

1. Update settings layout to two-level structure.
2. Move `Direction` into second-level settings.
3. Add dataset capability detection (`family:*` support).
4. Conditionally render family/subtype controls only for family-capable datasets.
5. Implement family-required + subtype-OR filtering semantics.
6. Add default-all subtype initialization and empty-subtype fallback.
7. Run sanity checks on NL + DE cloze, then one word-translation, then one sentence-builder set.
8. Update docs for UI structure and filter semantics after behavior is verified.

## Decision Log

- Replaces earlier strict AND attribute logic with OR for subtype selection.
- Adopts progressive-disclosure settings UI (two levels).
- Keeps canonical tag taxonomy unchanged.
- Prioritizes practical targeting and low-friction workflow.

# Implementation Plan: Schema Simplification & Logic Decoupling

## Goal
Simplify the JSON data files by removing UI-specific presentation logic and redundant fields. The application will act as an adapter, taking pure linguistic content and dynamically deriving the UI requirements (prompts, answers, word pools) based on the `question_type` and `content.response_mode`.

**Strategy: Hard Cutover.** We will update the app logic and the JSON data files simultaneously. There will be no transitional backwards-compatibility logic in the app to parse the old schema, keeping the codebase clean.

## Target Schema Principles
- **Merge `prompt` and `answer` into `text`**: Since they are often identical (or the answer is a subset of the prompt), we only store the core `text`.
- **Remove `answer` from Cloze**: The answer will be dynamically extracted using the `hidden_word_index`.
- **Replace `word_pool` with `distractors`**: We only need to store the incorrect words. The app logic will combine the words from `text` with `distractors` to create the final pool.
- **Keep `content` block**: Specifically `response_mode`. This decouples the *data* (the translation pair) from the *presentation* (how the user interacts with it, e.g., chips vs. typing). This allows future merging of `word_translation` and `sentence_builder` under a single `translation` type.
- **Remove `schema_version` from rows**: Reduces boilerplate.

### Example: Target Translation Schema
```json
{
  "id": 1,
  "question_type": "translation",
  "difficulty": 1,
  "tags": ["pos:adjective"],
  "content": {
    "response_mode": "token_sequence_choice"
  },
  "translations": {
    "en": {
      "text": "I am very happy today",
      "distractors": ["sad", "tomorrow"]
    },
    "nl": {
      "text": "Ik ben erg blij vandaag",
      "distractors": ["morgen", "verdrietig"]
    }
  }
}
```

## Phase 1: Data Migration Script (Start Here)
To ensure we can verify the new JSON structure before changing the app code, we will first create and run the migration script.
1. Create a script `scripts/migrate_schema.py` to iterate through all `.json` files inside `apps/public/`.
2. For each question object in the JSON array:
   - **Delete** the `"schema_version"` key.
   - For each language under `"translations"`:
     - **Rename** `"prompt"` to `"text"`.
     - **Delete** `"answer"`.
     - **Convert** `"word_pool"` to `"distractors"`. To do this:
       - Tokenize `"text"` into words (strip punctuation, convert to lowercase if necessary for comparison, but maintain original casing in distractors if possible, or just do a simple string removal if exact matches are found). Actually, `word_pool` currently contains exact casing. Calculate: `distractors = [word for word in word_pool if word not in text.split()]` (handle basic punctuation).
       - Ensure `distractors` does not contain any of the exact words present in the `text` string (case-sensitive or insensitive depending on how `word_pool` was originally built).
     - Keep `"accepted"`, `"hidden_word_index"`, and `"hint"` as they are if they exist.
3. Keep the `"content"` block intact (with `"response_mode"`).
4. **Update `question_type`**: Consider changing `sentence_builder_multiple_choice` and `word_translation_multiple_choice` to `translation`, or just changing `cloze_word_choice` to `cloze` if that's preferred. For now, keep `question_type` as is unless a rename is desired. Let's keep them as is for now, but ensure the logic can handle them.
5. Run the script and spot-check the output files using `git diff`.

## Phase 2: Update Application Logic (The Adapter)
Modify `apps/language_app.py` to strictly expect and parse the new schema.
1. Update `extract_translation_fields` (approx line 1433):
   - Replace reading `prompt` and `answer` with reading `text`.
   - Update the returned dict to return `prompt: text` and `answer: text` temporarily for the internal Polars structure, or better, rename internal columns to `text_l1` and `text_l2`. Actually, the plan is to map it to a canonical in-memory format.
2. Update `transform_to_canonical` (approx line 1450):
   - Ensure the `text` field maps to `prompt_l1`/`prompt_l2` and `text_l1`/`text_l2` correctly, or adapt the schema to just use `text_l1` and `text_l2`.
   - For cloze questions, implement logic to extract the hidden word.
3. Update `make_word_pool` (approx line 1404):
   - Change logic to build the pool. `pool = text.split() + distractors`. Deduplicate and sort as needed.

## Phase 3: Update Widget Payload Logic
1. Update `prepare_curriculum` (approx line 1302):
   - Ensure the routing logic cleanly maps the in-memory canonical schema to the `source`, `target`, and `words` (pool) expected by the `QuestionWidget`.
   - For translation: `source` is L1 text, `target` is L2 text.
   - For cloze: `source` is L2 text, `target` is the dynamically extracted word based on `hidden_word_index`.

## Phase 4: Documentation Update
1. Ensure `ARCHITECTURE.md` perfectly matches the final implementation, specifically noting the `content.response_mode` preservation.

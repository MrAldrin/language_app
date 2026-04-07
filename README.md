# Language Learning App

Marimo-based language learning app for targeted vocabulary and grammar practice.  
The app is JSON-driven and deployed as a WebAssembly (WASM) static site on GitHub Pages.

## Quick Start

Run the app locally:

```bash
uv run apps/language_app.py
```

Build a local static WASM export (same flow used for Pages deployment):

```bash
scripts/build.sh
```

Alternative (explicit `uv` command):

```bash
uv run marimo export html-wasm apps/language_app.py --mode run --no-show-code --sandbox -o _site/index.html
cp -r apps/public _site/
```

Serve the exported site:

```bash
python -m http.server -d _site
```

Or with `uv`:

```bash
uv run -m http.server -d _site
```

## Deploy (GitHub Pages + WASM)

- Production deploy workflow: `.github/workflows/deploy-main.yml`
- Dev deploy workflow: `.github/workflows/deploy-dev.yml`
- Both workflows export `apps/language_app.py` with `marimo export html-wasm` and publish `_site/`

## How The App Works

- You choose a language pair (or language for cloze), question set, difficulty, and direction where applicable.
- Session questions are filtered from JSON curriculum, transformed into a canonical in-memory format, then shuffled into a practice set.
- During each question, you can `Check`, `Clear`, and `Reveal answer`, and the session tracks attempts/correctness with a summary at the end.

## What The App Currently Supports

- Source/target language selection from available dataset folders.
- Question set selection (`sentence_builder`, `word_translation`, `cloze`).
- Difficulty filters with mapped bands: `1-3` (easy), `4-7` (medium), `8-10` (hard).
- Direction control (`Both`, `L1 -> L2`, `L2 -> L1`) for non-cloze sets.
- Tag-based focus filtering when canonical tags (for example `family:*`) are present.
- In-question flow: `Check`, `Clear`, `Reveal answer`, plus `Previous`/`Next` navigation.
- Session summary with attempts, correct/incorrect totals, and accuracy.

## Question Types And Interaction Model

- `sentence_builder_multiple_choice`: build a full answer from a token pool; selected tokens can be reordered.
- `word_translation`: choose a single-token translation from options.
- `cloze_word_choice`: fill one blank from options; direction control is not applicable.

## Curriculum Data

Curriculum JSON lives under `apps/public/`:

- Pair-based datasets: `apps/public/<lang1>_<lang2>/`
- Language-based cloze datasets: `apps/public/<lang>/`

Common question shape:

- Top-level: `id`, `question_type`, `difficulty`, `tags`, `content`, `translations`
- Per-language translation payload: `text`, optional `accepted`, optional `distractors`
- Cloze rows: `content.practice_language` + `translations[practice_language].hidden_word_index`

Legacy fields from older schema versions are migrated by `scripts/migrate_schema.py`.

## Project Layout

Core project files:

- App runtime: `apps/language_app.py`
- Curriculum content: `apps/public/**`
- Local export helper: `scripts/build.sh`

Reference/background files:

- Architecture notes: `ARCHITECTURE.md`
- Content generation docs: `docs/**`
- Template-origin readmes: `origin_repo_readmes/**`

## Architecture (Short)

The app separates content storage from runtime logic: JSON files are adapted into a canonical in-memory shape, then rendered by a question UI layer.  
This keeps question authoring flexible while keeping interaction logic consistent across question types.

See `ARCHITECTURE.md` for details.

# Language App: Data & Exercise Architecture

This document outlines the architectural principles for handling linguistic data and dynamically generating UI exercises within the Language App.

## Core Philosophy: Separation of Storage and Application Logic

The primary architectural driver is the strict separation between how linguistic data is **stored** (for authoring and maintenance) and how it is **consumed** (by the application's UI and game logic).

1.  **Storage Layer:** Optimized for content creators. Prevents duplication, ensures high-quality idiomatic translations, and minimizes structural boilerplate.
2.  **Logic Layer (Adapter):** Acts as a funnel, transforming varied storage schemas into a single, predictable canonical format in memory.
3.  **Presentation/UI Layer:** Agnostic to data origins. Receives a standardized "Exercise Payload" and handles the interactive experience (rendering, input, checking).

---

## 1. The Storage Strategy: Monolingual vs. Bilingual Authoring

Different types of language exercises require different authoring approaches to avoid maintenance nightmares and poor translation quality.

### Bilingual Folders (e.g., `en_nl/`, `de_no/`)
**Used for:** Translation exercises (Sentence Translation, Word Translation).

*   **The Problem:** Relying on transitive translations (e.g., automatically generating Dutch-German translations simply because English-Dutch and English-German exist) frequently leads to unnatural, overly literal phrasing.
*   **The Solution:** Explicitly authoring translation pairs guarantees idiomatic accuracy in both directions.
*   **Structure:** Questions are designed in pairs (Language 1 <-> Language 2), as the user needs to practice translating back and forth. The specific "target" vs "source" language only matters at runtime.

### Monolingual Folders (e.g., `nl/`, `de/`)
**Used for:** Cloze tests (Fill-in-the-blank), Grammar exercises.

*   **The Problem:** A cloze test tests the internal logic, grammar, or vocabulary of the *target language itself*. Storing a Dutch cloze test in every bilingual folder (`en_nl/`, `de_nl/`, `no_nl/`) creates massive, unmaintainable data duplication.
*   **The Solution:** Core exercises exist independently of the user's mother tongue. They are authored once in a target-language folder.
*   **Progressive Enhancement:** The user's mother tongue (L1) is treated as an *optional hint*. If a hint exists for the user's L1, it is shown. If not, the core exercise remains completely valid and playable.

---

## 2. The Logic Layer: The Canonical Data Model

Despite the differences in how data is authored, the application logic must not be burdened with branching logic (`if cloze_file then... else if translation_file then...`). 

When JSON files are loaded, they are immediately passed through an adapter function (`transform_to_canonical` in `apps/language_app.py`) that coerces them into a **single, unified schema** in memory (a Polars DataFrame).

### The Unified Schema (In-Memory)

The in-memory schema strips away the concept of "prompt" and "answer" at the dataset level, focusing purely on bilingual content and metadata.

*   **Content:**
    *   `text_l1` (e.g., "The cat is big")
    *   `text_l2` (e.g., "De kat is groot")
*   **Metadata:**
    *   `question_type` (e.g., "translation", "cloze")
    *   `hidden_word_index` (e.g., `1` for cloze, `null` or `-1` for translation)
*   **Extras:**
    *   `hint_l1`, `hint_l2`
    *   `word_pool_l1`, `word_pool_l2`
    *   `accepted_l1`, `accepted_l2`

---

## 3. Deriving the Exercise Payload (Question Builder)

The final step before passing data to the UI widget (`QuestionWidget`) is dynamically deriving the actual exercise prompt and the expected answer. This logic is driven entirely by the `question_type` and the chosen `direction`.

By doing this, we achieve **Zero Redundancy**. We never manually define the "answer" for a cloze question in the JSON; it is extracted programmatically.

### The Routing Logic

When preparing a row for the UI, the system acts as a router:

#### A. Translation Exercise (`question_type == "translation"`)
The `hidden_word_index` is ignored (or expected to be `-1`).
*   **Direction L1 -> L2:**
    *   `display_prompt` = `text_l1`
    *   `target_answer` = `text_l2`
*   **Direction L2 -> L1:**
    *   `display_prompt` = `text_l2`
    *   `target_answer` = `text_l1`

#### B. Cloze Exercise (`question_type == "cloze"`)
The logic specifically looks for the `hidden_word_index`. 
*   *Note: Cloze is typically unidirectional, targeting L2.*
*   `display_prompt` = `text_l2` *(Passed to the UI, which uses the index to visually blank out the word)*
*   `target_answer` = `text_l2.split()[hidden_word_index]` **(Automatically extracted)**
*   `hint` = `text_l1` *(Optionally displayed below the prompt)*

---

## 4. The UI Layer (`QuestionWidget`)

The frontend widget receives a highly standardized, agnostic payload:
*   `prompt`
*   `target`
*   `hidden_index`

The UI doesn't care if the `target` was hardcoded in a JSON file or dynamically spliced out of a sentence. It simply renders the interface and checks if the user's input matches the `target`.

### Extensibility

This architecture is extremely flexible. If a new exercise type is added in the future (e.g., a "Dictation" exercise), the unified schema remains identical. The Logic Layer simply routes the `text_l2` to an audio generator, sets `target_answer` to `text_l2`, and passes it to the UI.

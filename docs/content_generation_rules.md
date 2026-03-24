# Language App Content Generation Rules


## 1. Data Schema, Types and Explanation

- **`id`**: Sequential integer.
- **`type`**: `sentence_builder_multiple_choice`.
- **`difficulty`**: Integer 1–10 (10 is hardest). 
- **`tags`**: List of several relevant tags (e.g., `plural`, `food`, `verb_conjugation`, `articles`, `irregular_verbs`).
- **`translations`**: A dictionary keyed by language code. Each entry contains:
    - **`primary`**: The primary translation. It should be the most common and natural translation in that language.
    - **`accepted`**: A list of all natural alternative correct translations. Can be empty if none. Omit punctuation/capitalization variations. All accepted answers must be valid translations of the other language's primary sentence (bidirectional symmetry).
    - **`word_pool`**: A list of all words that appear in either primary or accepted and then another 4-7 extra distractor words. There should be no duplicates.


## 2. Linguistic & Pedagogy Rules

- Grammar & Capitalization: Always use correct grammar and spelling in that language.
- Translation rules:  Translations should try to be as directly translated as possible to show a bridge between the languages. Either in the primary or accepted section.
- Naturalism: Use modern, conversational phrasing.
- Concepts: Each entry should target just a few specific grammar rule or vocabulary cluster, according to the difficulty given.
- The word_pool: Should not contain tells of the word order, like punctuation and capitalizing the first word in a sentence that is not capitalized by default in that language (Like german Zeitung)
- Distractor Logic: 
  - Should not contain spelling errors or non-standard contractions
  - Should be testing the user with alternatives from the same concepts as they are tagged with
 

## 3. Technical Constraints
- File type: json
- Encoding: Strictly **UTF-8** (support *æ, ø, å, ü, ß*).
- The questions should be generated in pairs of languages (one JSON file per language pair) and placed in their respective folders in data/. 
- The languages are `en`, `de`, `no`, `nl`


## Schema example:
```json
{
  "id": 1,
  "question_type": "sentence_builder_multiple_choice",
  "difficulty": 1,
  "tags": ["basics", "question"],
  "translations": {
    "no": {
      "primary": "Hvor er boka?",
      "accepted": ["Hvor er boken?"],
      "word_pool": ["hva", "hvem", "når", "var", "brevet", "avisa"]
    },
    "de": {
      "primary": "Wo ist das Buch?",
      "accepted": [],
      "word_pool": ["was", "wer", "wann", "Zeitung", "bist", "bin"]
    }
  }
}
```
import json
import os
from pathlib import Path
import re


def get_words(text):
    """Extract words ignoring basic punctuation."""
    # Simple split and strip punctuation for comparison
    return [
        re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?"\']', "", w).lower() for w in text.split()
    ]


def migrate_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    for item in data:
        if "schema_version" in item:
            del item["schema_version"]
            changed = True

        if "translations" in item:
            for lang, lang_data in item["translations"].items():
                if "prompt" in lang_data:
                    # Rename prompt to text
                    text = lang_data["prompt"]
                    lang_data["text"] = text
                    del lang_data["prompt"]
                    changed = True

                if "answer" in lang_data:
                    # For cloze, the answer might be different from text, but we extract it dynamically anyway
                    # For translation, prompt == answer mostly. We just delete answer.
                    del lang_data["answer"]
                    changed = True

                if "word_pool" in lang_data:
                    text = lang_data.get("text", "")
                    text_words = get_words(text)

                    distractors = []
                    for word in lang_data["word_pool"]:
                        # Compare ignoring punctuation
                        clean_word = re.sub(
                            r'[.,\/#!$%\^&\*;:{}=\-_`~()?"\']', "", word
                        ).lower()
                        if clean_word not in text_words:
                            distractors.append(word)

                    lang_data["distractors"] = distractors
                    del lang_data["word_pool"]
                    changed = True

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Migrated: {filepath}")


def main():
    public_dir = Path("apps/public")
    if not public_dir.exists():
        print(f"Error: {public_dir} does not exist.")
        return

    for json_file in public_dir.rglob("*.json"):
        migrate_file(json_file)


if __name__ == "__main__":
    main()

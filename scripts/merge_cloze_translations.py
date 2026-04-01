#!/usr/bin/env python3
import json
import argparse
import sys


def merge_translations(original_file, hints_file, output_file):
    """
    Merges hint translations back into the original cloze questions JSON.
    Follows schema v2 (hint_translation field).
    """
    try:
        with open(original_file, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading original file {original_file}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(hints_file, "r", encoding="utf-8") as f:
            translated_hints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading hints file {hints_file}: {e}", file=sys.stderr)
        sys.exit(1)

    updated_count = 0
    for q in questions:
        q_id = str(q.get("id"))
        if q_id in translated_hints:
            hints = translated_hints[q_id]
            # Schema v2: Other languages only require hint_translation
            for lang, text in hints.items():
                if "translations" not in q:
                    q["translations"] = {}
                q["translations"][lang] = {"hint_translation": text}
            updated_count += 1

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"Successfully merged {updated_count} questions into {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge translation hints back into cloze questions."
    )
    parser.add_argument(
        "original", help="Path to the original cloze questions JSON file."
    )
    parser.add_argument("hints", help="Path to the translated hints JSON file.")
    parser.add_argument(
        "--output", help="Output path (defaults to overwriting original)", default=None
    )

    args = parser.parse_args()
    output = args.output if args.output else args.original
    merge_translations(args.original, args.hints, output)

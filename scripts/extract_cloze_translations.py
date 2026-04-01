#!/usr/bin/env python3
import json
import argparse
import sys


def extract_sentences(input_file, output_file):
    """
    Extracts full sentences from cloze questions for translation.
    Replaces the blank token with the answer.
    """
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading {input_file}: {e}", file=sys.stderr)
        sys.exit(1)

    data_to_translate = []

    for q in questions:
        q_id = q.get("id")
        # Get the primary practice language data
        practice_lang = q.get("content", {}).get("practice_language", "nl")
        nl_data = q.get("translations", {}).get(practice_lang, {})

        prompt = nl_data.get("prompt", "")
        answer = nl_data.get("answer", "")
        blank_token = q.get("content", {}).get("blank_token", "___")

        # Simple replacement of the blank token with the answer
        full_sentence = prompt.replace(blank_token, answer)

        data_to_translate.append({"id": q_id, "nl": full_sentence})

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data_to_translate, f, indent=2, ensure_ascii=False)
        print(f"Extracted {len(data_to_translate)} sentences to {output_file}")
    except IOError as e:
        print(f"Error writing to {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract full sentences from cloze questions for translation."
    )
    parser.add_argument("input", help="Path to the cloze questions JSON file.")
    parser.add_argument("output", help="Path to save the extracted sentences.")

    args = parser.parse_args()
    extract_sentences(args.input, args.output)

#!/usr/bin/env python3
import json
import re
from pathlib import Path

DATA_ROOT = Path("apps/public")
TARGET_NAME = "sentence_builder.json"
TOKEN_RE = re.compile(r"[^\s]+")


def normalize_token(token: str) -> str:
    return token.strip('.,!?;:"()[]{}').lower()


def tokenize_text(text: str) -> list[str]:
    return [normalize_token(t) for t in TOKEN_RE.findall(text) if normalize_token(t)]


def build_available_token_multiset(text: str, distractors: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokenize_text(text):
        counts[token] = counts.get(token, 0) + 1
    for item in distractors:
        for token in tokenize_text(item):
            counts[token] = counts.get(token, 0) + 1
    return counts


def find_missing_tokens(
    candidate_sentence: str, available_counts: dict[str, int]
) -> list[str]:
    missing: list[str] = []
    used: dict[str, int] = {}
    for token in tokenize_text(candidate_sentence):
        used[token] = used.get(token, 0) + 1
        if used[token] > available_counts.get(token, 0):
            missing.append(token)
    return missing


def cleanup_file(file_path: Path):
    print(f"Cleaning {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    modified = False
    for question in data:
        translations = question.get("translations", {})
        for lang, payload in translations.items():
            text = payload.get("text", "")
            accepted = payload.get("accepted", [])
            distractors = payload.get("distractors", [])

            if not text or not isinstance(accepted, list):
                continue

            text_counts = build_available_token_multiset(text, [])

            new_accepted = []
            for item in accepted:
                if not isinstance(item, str):
                    new_accepted.append(item)
                    continue

                missing_from_text = find_missing_tokens(item, text_counts)
                if missing_from_text:
                    print(
                        f"  Q{question.get('id')} [{lang}]: Removing '{item}' (uses {missing_from_text})"
                    )
                    modified = True
                else:
                    new_accepted.append(item)

            payload["accepted"] = new_accepted

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"  Saved {file_path}")
    else:
        print(f"  No changes for {file_path}")


def main():
    files = sorted(DATA_ROOT.rglob(TARGET_NAME))
    for file_path in files:
        cleanup_file(file_path)


if __name__ == "__main__":
    main()

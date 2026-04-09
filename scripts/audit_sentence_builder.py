#!/usr/bin/env python3
"""Audit sentence_builder datasets for schema and basic content sanity.

Step 2 scope:
- Hard checks: required keys, question type, response mode, translation count
- Basic sanity: non-empty text, accepted/distractors array types, duplicate entries,
  and text duplicated in accepted
"""

from __future__ import annotations

import json
import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA_ROOT = Path("apps/public")
TARGET_NAME = "sentence_builder.json"

REQUIRED_QUESTION_KEYS = {
    "id",
    "question_type",
    "difficulty",
    "tags",
    "content",
    "translations",
}

EXPECTED_QUESTION_TYPE = "sentence_builder_multiple_choice"
EXPECTED_RESPONSE_MODE = "token_sequence_choice"
DEFAULT_REPORT_JSON = Path("plans/reports/sentence_builder_audit_report.json")
DEFAULT_SUMMARY_MD = Path("plans/reports/sentence_builder_audit_summary.md")
TOKEN_RE = re.compile(r"[^\s]+")


@dataclass
class Finding:
    severity: str  # error | warning
    finding_type: str
    file: str
    question_id: int | str
    language: str | None
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "finding_type": self.finding_type,
            "file": self.file,
            "question_id": self.question_id,
            "language": self.language,
            "message": self.message,
        }


def find_target_files(single_file: str | None = None) -> list[Path]:
    if single_file:
        path = Path(single_file)
        return [path] if path.exists() else []
    return sorted(DATA_ROOT.rglob(TARGET_NAME))


def build_summary_markdown(
    files_scanned: int,
    questions_scanned: int,
    total_findings: int,
    total_errors: int,
    total_warnings: int,
    reports: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append("# Sentence Builder Audit Summary")
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- Files scanned: {files_scanned}")
    lines.append(f"- Questions scanned: {questions_scanned}")
    lines.append(f"- Findings: {total_findings}")
    lines.append(f"- Errors: {total_errors}")
    lines.append(f"- Warnings: {total_warnings}")
    lines.append("")
    lines.append("## Findings By File")
    lines.append("")

    for report in reports:
        file_findings = report["findings"]
        err_count = sum(1 for f in file_findings if f["severity"] == "error")
        warn_count = sum(1 for f in file_findings if f["severity"] == "warning")
        lines.append(f"### `{report['file']}`")
        lines.append(f"- Questions: {report['question_count']}")
        lines.append(f"- Errors: {err_count}")
        lines.append(f"- Warnings: {warn_count}")
        if not file_findings:
            lines.append("- Findings: none")
        lines.append("")

    return "\n".join(lines) + "\n"


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def normalize_token(token: str) -> str:
    # Keep inner apostrophes/hyphens; remove surrounding punctuation and lowercase.
    return token.strip(".,!?;:\"()[]{}").lower()


def tokenize_text(text: str) -> list[str]:
    return [normalize_token(t) for t in TOKEN_RE.findall(text) if normalize_token(t)]


def build_available_token_multiset(text: str, distractors: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokenize_text(text):
        counts[token] = counts.get(token, 0) + 1
    # Distractors can be phrase chips; split to words for constructibility checks.
    for item in distractors:
        for token in tokenize_text(item):
            counts[token] = counts.get(token, 0) + 1
    return counts


def find_missing_tokens(candidate_sentence: str, available_counts: dict[str, int]) -> list[str]:
    missing: list[str] = []
    used: dict[str, int] = {}
    for token in tokenize_text(candidate_sentence):
        used[token] = used.get(token, 0) + 1
        if used[token] > available_counts.get(token, 0):
            missing.append(token)
    return missing


def token_set(text: str) -> set[str]:
    return set(tokenize_text(text))


CONTRACTION_MAP = {
    "don't": ["do", "not"],
    "can't": ["can", "not"],
    "won't": ["will", "not"],
    "i'm": ["i", "am"],
    "you're": ["you", "are"],
    "we're": ["we", "are"],
    "they're": ["they", "are"],
    "it's": ["it", "is"],
    "isn't": ["is", "not"],
    "aren't": ["are", "not"],
    "didn't": ["did", "not"],
    "doesn't": ["does", "not"],
    "wasn't": ["was", "not"],
    "weren't": ["were", "not"],
    "I've": ["i", "have"],
    "you've": ["you", "have"],
    "we've": ["we", "have"],
    "they've": ["they", "have"],
}

LIKELY_TENSE_MARKERS = {
    "en": {"is", "are", "am", "was", "were", "will", "did", "do", "does"},
    "de": {"ist", "sind", "war", "waren", "wird", "werden", "hat", "hatte"},
    "nl": {"is", "zijn", "was", "waren", "zal", "zullen", "heeft", "had"},
    "no": {"er", "var", "har", "hadde", "skal", "vil"},
}


def has_contraction_variant(text: str, accepted_item: str) -> bool:
    base = token_set(text)
    alt = token_set(accepted_item)

    for contracted, expanded in CONTRACTION_MAP.items():
        c = contracted.lower()
        exp = set(expanded)
        if c in base and exp.issubset(alt):
            return True
        if c in alt and exp.issubset(base):
            return True
    return False


def likely_tense_shift(text: str, accepted_item: str, lang: str) -> bool:
    markers = LIKELY_TENSE_MARKERS.get(lang, set())
    if not markers:
        return False
    base = token_set(text)
    alt = token_set(accepted_item)
    base_markers = base.intersection(markers)
    alt_markers = alt.intersection(markers)
    return base_markers != alt_markers and (base_markers or alt_markers)


def likely_lexical_swap(text: str, accepted_item: str) -> bool:
    base = token_set(text)
    alt = token_set(accepted_item)
    symmetric_diff = base.symmetric_difference(alt)
    # If only word order changes, diff is empty.
    # If there are lexical changes but still small overlap, this is likely a swap.
    if not symmetric_diff:
        return False
    overlap = len(base.intersection(alt))
    return overlap >= max(1, min(len(base), len(alt)) - 2)


def validate_question(
    question: Any,
    file_path: Path,
    index: int,
) -> tuple[list[Finding], int | str]:
    findings: list[Finding] = []

    if not isinstance(question, dict):
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=f"index:{index}",
                language=None,
                message="Question entry must be an object.",
            )
        )
        return findings, f"index:{index}"

    question_id = question.get("id", f"index:{index}")

    missing_keys = sorted(REQUIRED_QUESTION_KEYS - set(question.keys()))
    if missing_keys:
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=question_id,
                language=None,
                message=f"Missing required keys: {', '.join(missing_keys)}",
            )
        )

    if question.get("question_type") != EXPECTED_QUESTION_TYPE:
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=question_id,
                language=None,
                message=(
                    "Invalid question_type: "
                    f"expected '{EXPECTED_QUESTION_TYPE}', got {question.get('question_type')!r}"
                ),
            )
        )

    content = question.get("content")
    if not isinstance(content, dict):
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=question_id,
                language=None,
                message="content must be an object.",
            )
        )
    elif content.get("response_mode") != EXPECTED_RESPONSE_MODE:
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=question_id,
                language=None,
                message=(
                    "Invalid content.response_mode: "
                    f"expected '{EXPECTED_RESPONSE_MODE}', got {content.get('response_mode')!r}"
                ),
            )
        )

    translations = question.get("translations")
    if not isinstance(translations, dict):
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=question_id,
                language=None,
                message="translations must be an object.",
            )
        )
        return findings, question_id

    if len(translations) != 2:
        findings.append(
            Finding(
                severity="error",
                finding_type="schema_error",
                file=str(file_path),
                question_id=question_id,
                language=None,
                message=f"Expected exactly 2 translation languages, got {len(translations)}.",
            )
        )

    for lang, payload in translations.items():
        if not isinstance(payload, dict):
            findings.append(
                Finding(
                    severity="error",
                    finding_type="schema_error",
                    file=str(file_path),
                    question_id=question_id,
                    language=lang,
                    message="translations.<lang> must be an object.",
                )
            )
            continue

        text = payload.get("text")
        accepted = payload.get("accepted")
        distractors = payload.get("distractors")

        if not is_non_empty_string(text):
            findings.append(
                Finding(
                    severity="error",
                    finding_type="content_error",
                    file=str(file_path),
                    question_id=question_id,
                    language=lang,
                    message="text must be a non-empty string.",
                )
            )

        if not isinstance(accepted, list):
            findings.append(
                Finding(
                    severity="error",
                    finding_type="content_error",
                    file=str(file_path),
                    question_id=question_id,
                    language=lang,
                    message="accepted must be an array.",
                )
            )
            accepted = []

        if not isinstance(distractors, list):
            findings.append(
                Finding(
                    severity="error",
                    finding_type="content_error",
                    file=str(file_path),
                    question_id=question_id,
                    language=lang,
                    message="distractors must be an array.",
                )
            )
            distractors = []

        if isinstance(accepted, list):
            seen: set[str] = set()
            duplicates: list[str] = []
            for item in accepted:
                if not isinstance(item, str):
                    findings.append(
                        Finding(
                            severity="error",
                            finding_type="content_error",
                            file=str(file_path),
                            question_id=question_id,
                            language=lang,
                            message="accepted must contain only strings.",
                        )
                    )
                    continue
                if item in seen and item not in duplicates:
                    duplicates.append(item)
                seen.add(item)

            if duplicates:
                findings.append(
                    Finding(
                        severity="warning",
                        finding_type="duplicate_value_warning",
                        file=str(file_path),
                        question_id=question_id,
                        language=lang,
                        message=f"Duplicate accepted values: {duplicates}",
                    )
                )

            if isinstance(text, str) and text in accepted:
                findings.append(
                    Finding(
                        severity="warning",
                        finding_type="accepted_policy_warning",
                        file=str(file_path),
                        question_id=question_id,
                        language=lang,
                        message="text is duplicated in accepted.",
                    )
                )

            if isinstance(text, str) and isinstance(distractors, list):
                available_counts = build_available_token_multiset(text, distractors)
                for item in accepted:
                    if not isinstance(item, str):
                        continue
                    missing = find_missing_tokens(item, available_counts)
                    if missing:
                        findings.append(
                            Finding(
                                severity="error",
                                finding_type="token_pool_error",
                                file=str(file_path),
                                question_id=question_id,
                                language=lang,
                                message=(
                                    "accepted cannot be built from text+distractors tokens; "
                                    f"missing/overused tokens: {missing}"
                                ),
                            )
                        )
                    else:
                        if has_contraction_variant(text, item):
                            findings.append(
                                Finding(
                                    severity="warning",
                                    finding_type="accepted_policy_warning",
                                    file=str(file_path),
                                    question_id=question_id,
                                    language=lang,
                                    message=(
                                        "accepted appears to be a contraction/non-contraction "
                                        "variant of text."
                                    ),
                                )
                            )
                        if likely_tense_shift(text, item, lang):
                            findings.append(
                                Finding(
                                    severity="warning",
                                    finding_type="accepted_policy_warning",
                                    file=str(file_path),
                                    question_id=question_id,
                                    language=lang,
                                    message=(
                                        "accepted appears to introduce a likely tense/aspect "
                                        "shift vs text."
                                    ),
                                )
                            )
                        # NOTE: lexical-swap heuristic intentionally disabled for now.
                        # It currently over-flags and will be redesigned in a later phase.

        if isinstance(distractors, list):
            seen: set[str] = set()
            duplicates: list[str] = []
            for item in distractors:
                if not isinstance(item, str):
                    findings.append(
                        Finding(
                            severity="error",
                            finding_type="content_error",
                            file=str(file_path),
                            question_id=question_id,
                            language=lang,
                            message="distractors must contain only strings.",
                        )
                    )
                    continue
                if item in seen and item not in duplicates:
                    duplicates.append(item)
                seen.add(item)

            if duplicates:
                findings.append(
                    Finding(
                        severity="warning",
                        finding_type="duplicate_value_warning",
                        file=str(file_path),
                        question_id=question_id,
                        language=lang,
                        message=f"Duplicate distractor values: {duplicates}",
                    )
                )

    return findings, question_id


def audit_file(file_path: Path) -> dict[str, Any]:
    findings: list[Finding] = []
    question_count = 0

    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "file": str(file_path),
            "question_count": 0,
            "findings": [
                Finding(
                    severity="error",
                    finding_type="json_parse_error",
                    file=str(file_path),
                    question_id="file",
                    language=None,
                    message=f"Invalid JSON: {exc}",
                ).to_dict()
            ],
        }

    if not isinstance(raw, list):
        return {
            "file": str(file_path),
            "question_count": 0,
            "findings": [
                Finding(
                    severity="error",
                    finding_type="schema_error",
                    file=str(file_path),
                    question_id="file",
                    language=None,
                    message="Root must be a JSON array.",
                ).to_dict()
            ],
        }

    for idx, question in enumerate(raw, start=1):
        question_count += 1
        question_findings, _question_id = validate_question(question, file_path, idx)
        findings.extend(question_findings)

    return {
        "file": str(file_path),
        "question_count": question_count,
        "findings": [f.to_dict() for f in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        help="Audit one specific sentence_builder.json file instead of all files.",
    )
    parser.add_argument(
        "--report-json",
        default=str(DEFAULT_REPORT_JSON),
        help="Path for machine-readable JSON report.",
    )
    parser.add_argument(
        "--summary-md",
        default=str(DEFAULT_SUMMARY_MD),
        help="Path for human-readable markdown summary.",
    )
    args = parser.parse_args()

    files = find_target_files(args.file)

    if not files:
        print("No sentence_builder.json files found.")
        return 1

    all_reports: list[dict[str, Any]] = []
    total_questions = 0
    total_findings = 0
    total_errors = 0
    total_warnings = 0

    for file_path in files:
        report = audit_file(file_path)
        all_reports.append(report)
        total_questions += report["question_count"]
        total_findings += len(report["findings"])
        total_errors += sum(1 for f in report["findings"] if f["severity"] == "error")
        total_warnings += sum(1 for f in report["findings"] if f["severity"] == "warning")

    print(f"Files scanned: {len(files)}")
    print(f"Questions scanned: {total_questions}")
    print(f"Findings: {total_findings} (errors={total_errors}, warnings={total_warnings})")

    for report in all_reports:
        if report["findings"]:
            print(f"\\n{report['file']}")
            for finding in report["findings"]:
                lang = finding["language"] if finding["language"] is not None else "-"
                print(
                    "  "
                    f"[{finding['severity']}] "
                    f"qid={finding['question_id']} "
                    f"lang={lang} "
                    f"type={finding['finding_type']} "
                    f"- {finding['message']}"
                )

    report_json_path = Path(args.report_json)
    summary_md_path = Path(args.summary_md)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    summary_md_path.parent.mkdir(parents=True, exist_ok=True)

    full_report = {
        "totals": {
            "files_scanned": len(files),
            "questions_scanned": total_questions,
            "findings": total_findings,
            "errors": total_errors,
            "warnings": total_warnings,
        },
        "reports": all_reports,
    }
    report_json_path.write_text(
        json.dumps(full_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary_md_path.write_text(
        build_summary_markdown(
            files_scanned=len(files),
            questions_scanned=total_questions,
            total_findings=total_findings,
            total_errors=total_errors,
            total_warnings=total_warnings,
            reports=all_reports,
        ),
        encoding="utf-8",
    )
    print(f"\nWrote report JSON: {report_json_path}")
    print(f"Wrote summary MD: {summary_md_path}")

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

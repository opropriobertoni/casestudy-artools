#!/usr/bin/env python3
"""
extract_css_values.py -- Pre-extracts raw, repeated value candidates from
CSS files for downstream Design Token authoring by the token-pipeline-setup
Skill.

This script performs NO semantic decision. It does not assign DTCG $type,
does not name tokens, and does not deduplicate by meaning -- only by exact
string match. It is a heuristic, regex-based extractor (no CSS AST), meant
to surface candidates for the agent to interpret, not to serve as ground
truth.

Usage:
    python3 extract_css_values.py --input assets/css --output candidates.json

Run with --help for full argument details.
"""
import argparse
import json
import re
import sys
from pathlib import Path

CUSTOM_PROPERTY_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
COLOR_RE = re.compile(
    r"(#[0-9a-fA-F]{3,8}\b|"
    r"rgba?\([^)]+\)|"
    r"hsla?\([^)]+\))"
)
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;]+);")
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([\d.]+(?:px|rem|em))\s*;")
FONT_WEIGHT_RE = re.compile(r"font-weight\s*:\s*(\d{3}|normal|bold)\s*;")
LINE_HEIGHT_RE = re.compile(r"line-height\s*:\s*([\d.]+(?:px|rem|em|%)?)\s*;")
SPACING_RE = re.compile(
    r"(margin|padding|gap)(?:-[a-z]+)?\s*:\s*([\d.]+(?:px|rem|em)(?:\s+[\d.]+(?:px|rem|em)){0,3})\s*;"
)
RADIUS_RE = re.compile(r"border-radius\s*:\s*([\d.]+(?:px|rem|em|%))\s*;")
SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;]+);")


def find_selector(css_text: str, match_start: int) -> str:
    """Best-effort: walk backwards to the nearest preceding '{' and return
    the selector text immediately before it. Heuristic only."""
    chunk = css_text[:match_start]
    brace_idx = chunk.rfind("{")
    if brace_idx == -1:
        return ":unknown"
    prev_close = chunk.rfind("}", 0, brace_idx)
    selector = chunk[prev_close + 1:brace_idx].strip()
    return selector[-80:] if selector else ":unknown"


def extract_from_file(path: Path) -> list:
    text = path.read_text(encoding="utf-8", errors="ignore")
    candidates = []

    def add(property_name, value, match):
        candidates.append({
            "file": str(path),
            "selector_context": find_selector(text, match.start()),
            "property": property_name,
            "value": value.strip(),
        })

    for m in CUSTOM_PROPERTY_RE.finditer(text):
        add(m.group(1), m.group(2), m)
    for m in COLOR_RE.finditer(text):
        add("color-literal", m.group(1), m)
    for m in FONT_FAMILY_RE.finditer(text):
        add("font-family", m.group(1), m)
    for m in FONT_SIZE_RE.finditer(text):
        add("font-size", m.group(1), m)
    for m in FONT_WEIGHT_RE.finditer(text):
        add("font-weight", m.group(1), m)
    for m in LINE_HEIGHT_RE.finditer(text):
        add("line-height", m.group(1), m)
    for m in SPACING_RE.finditer(text):
        add(m.group(1), m.group(2), m)
    for m in RADIUS_RE.finditer(text):
        add("border-radius", m.group(1), m)
    for m in SHADOW_RE.finditer(text):
        add("box-shadow", m.group(1), m)

    return candidates


def main():
    parser = argparse.ArgumentParser(
        description="Pre-extracts raw CSS value candidates (custom properties, "
        "colors, typography, spacing, radius, shadow) from a directory of CSS "
        "files. Performs no DTCG typing or naming -- that is the agent's job."
    )
    parser.add_argument("--input", required=True, help="Directory containing CSS files (e.g. assets/css)")
    parser.add_argument("--output", required=True, help="Path to write candidates.json")
    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"ERROR: input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    css_files = sorted(input_dir.rglob("*.css"))
    if not css_files:
        print(f"ERROR: no .css files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    all_candidates = []
    for css_file in css_files:
        all_candidates.extend(extract_from_file(css_file))

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(all_candidates)} candidates from {len(css_files)} file(s) -> {args.output}")


if __name__ == "__main__":
    main()

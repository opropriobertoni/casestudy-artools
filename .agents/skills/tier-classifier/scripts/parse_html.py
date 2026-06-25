#!/usr/bin/env python3
"""
parse_html.py -- Pre-extracts structural candidates from a design-system.html
file for semantic classification by the tier-classifier Skill.

This script performs NO semantic classification. It only extracts a flat,
structured list of HTML elements that carry an id or class attribute, paired
with the nearest preceding section comment and a short text preview.

Usage:
    python3 parse_html.py --input design-system.html --output candidates.json

Run with --help for full argument details.
"""
import argparse
import json
import sys
from html.parser import HTMLParser


class CandidateExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.candidates = []
        self.current_section = None
        self._stack = []

    def handle_comment(self, data):
        comment = data.strip()
        if comment:
            self.current_section = comment

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        id_attr = attr_dict.get("id")
        class_attr = attr_dict.get("class")
        entry = None
        if id_attr or class_attr:
            entry = {
                "tag": tag,
                "id": id_attr,
                "classes": class_attr.split() if class_attr else [],
                "section_comment": self.current_section,
                "text_preview": "",
            }
            self.candidates.append(entry)
        self._stack.append(entry)

    def handle_endtag(self, tag):
        if self._stack:
            self._stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        for entry in reversed(self._stack):
            if entry is not None and not entry["text_preview"]:
                entry["text_preview"] = text[:60]
                break


def main():
    parser = argparse.ArgumentParser(
        description="Pre-extracts structural candidates (tag, id, classes, "
        "section comment, text preview) from an HTML file for downstream "
        "semantic tier classification. Performs no classification itself."
    )
    parser.add_argument("--input", required=True, help="Path to design-system.html")
    parser.add_argument("--output", required=True, help="Path to write candidates.json")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            html_content = f.read()
    except OSError as e:
        print(f"ERROR: could not read input file: {e}", file=sys.stderr)
        sys.exit(1)

    extractor = CandidateExtractor()
    extractor.feed(html_content)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(extractor.candidates, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(extractor.candidates)} candidates -> {args.output}")


if __name__ == "__main__":
    main()

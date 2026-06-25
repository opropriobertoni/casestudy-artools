#!/usr/bin/env python3
"""
detect_exceptions.py -- Clusters class names observed directly in
design-system.html by shared root, surfacing variant/state-modifier signals
in the ORIGIN naming convention (BEM, utility, ad-hoc -- whatever it is),
for the agent to translate into CUBE CSS Exceptions (data-variant /
data-state) inside the generated Component Spec.

Caminho 1 design note: the reference HTML was NOT authored in CUBE CSS.
This script does not search for data-* attributes (which likely don't
exist in the origin) -- it clusters compound classes by shared root
instead, and applies a keyword heuristic to flag the likely CUBE category
(style_variant vs state_modifier). It performs NO final naming decision --
the agent makes that call when writing the spec.

Usage:
    python3 detect_exceptions.py --html design-system.html --output exceptions_map.json

Run with --help for full argument details.
"""
import argparse
import json
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

STATE_KEYWORDS = {
    "loading", "open", "active", "disabled", "expanded", "selected",
    "collapsed", "closed", "checked", "invalid", "error", "success", "hidden",
}
STATE_PREFIXES = ("is-", "has-")


class ClassCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tag_class_groups = []  # [{"classes": [...], "section_comment": ...}]
        self.current_section = None

    def handle_comment(self, data):
        comment = data.strip()
        if comment:
            self.current_section = comment

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        class_attr = attr_dict.get("class")
        if class_attr:
            self.tag_class_groups.append({
                "classes": class_attr.split(),
                "section_comment": self.current_section,
            })


def classify_signal(class_name):
    lower = class_name.lower()
    if lower.startswith(STATE_PREFIXES):
        return "state_modifier"
    if any(kw in lower for kw in STATE_KEYWORDS):
        return "state_modifier"
    return "style_variant"


def root_of(class_name):
    """Heuristic: strip the last BEM-modifier ('--mod') or hyphen-suffix
    segment to find the shared root. 'btn-primary' -> 'btn';
    'card--open' -> 'card'. Classes with no separator return themselves
    (filtered out downstream -- not a variant signal)."""
    if "--" in class_name:
        return class_name.split("--")[0]
    parts = class_name.rsplit("-", 1)
    return parts[0] if len(parts) == 2 else class_name


def main():
    parser = argparse.ArgumentParser(
        description="Clusters HTML classes by shared root to surface variant/state "
        "signals in the origin naming convention, for CUBE CSS Exception translation "
        "by the agent. Performs no naming decision itself."
    )
    parser.add_argument("--html", required=True, help="Path to design-system.html")
    parser.add_argument("--output", required=True, help="Path to write exceptions_map.json")
    args = parser.parse_args()

    html_path = Path(args.html)
    if not html_path.is_file():
        print(f"ERROR: html file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    collector = ClassCollector()
    collector.feed(html_path.read_text(encoding="utf-8", errors="ignore"))

    style_clusters = defaultdict(list)
    standalone_state_classes = []

    for group in collector.tag_class_groups:
        classes = group["classes"]
        section = group["section_comment"]
        for cls in classes:
            if cls.lower().startswith(STATE_PREFIXES):
                siblings = [c for c in classes if c != cls]
                standalone_state_classes.append({
                    "class": cls,
                    "co_occurring_classes": siblings,
                    "section_comment": section,
                })
                continue
            root = root_of(cls)
            if root == cls:
                continue  # no separator -- not a variant signal, skip
            style_clusters[root].append({
                "class": cls,
                "signal_type": classify_signal(cls),
                "section_comment": section,
            })

    def dedupe(items):
        seen, out = set(), []
        for v in items:
            key = (v["class"], v["section_comment"])
            if key not in seen:
                seen.add(key)
                out.append(v)
        return out

    variant_clusters = [
        {"root": root, "variants": dedupe(variants)}
        for root, variants in style_clusters.items()
    ]
    standalone_state_classes = dedupe(standalone_state_classes)

    output = {
        "variant_clusters": variant_clusters,
        "standalone_state_classes": standalone_state_classes,
    }

    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Found {len(variant_clusters)} variant cluster(s) and "
        f"{len(standalone_state_classes)} standalone state class(es) -> {args.output}"
    )


if __name__ == "__main__":
    main()

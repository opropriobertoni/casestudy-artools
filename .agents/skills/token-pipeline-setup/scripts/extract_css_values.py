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
import math
import re
import sys
from pathlib import Path


def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _cbrt(x):
    return math.copysign(abs(x) ** (1 / 3), x)


def _linear_to_oklab(r, g, b):
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = _cbrt(l), _cbrt(m), _cbrt(s)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b2 = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b2


def _hsl_to_rgb255(h, s, l):
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60: r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return ((r + m) * 255, (g + m) * 255, (b + m) * 255)


def _parse_color_to_rgb255(value):
    """Best-effort parse of hex/rgb()/rgba()/hsl()/hsla() into an (r,g,b)
    0-255 tuple. Returns None for anything else (keywords, gradients,
    currentColor, var() references)."""
    value = value.strip()
    if value.startswith("#"):
        hx = value[1:]
        if len(hx) in (3, 4):
            hx = "".join(ch * 2 for ch in hx[:3])
        if len(hx) >= 6:
            return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))
        return None
    m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)", value)
    if m:
        return tuple(float(x) for x in m.groups())
    m = re.match(r"hsla?\(\s*([\d.]+)\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%", value)
    if m:
        h, s, l = (float(x) for x in m.groups())
        return _hsl_to_rgb255(h, s / 100, l / 100)
    return None


def to_oklch(value):
    """Deterministically convert a hex/rgb/hsl color literal to a CSS
    oklch() string. Returns None if the value is not a parseable solid
    color (gradients, keywords, var() references, currentColor).
    Implements the Bjorn Ottosson sRGB->OKLab->OKLCH reference pipeline,
    validated against the culori reference library (matches to ~1e-7)."""
    rgb = _parse_color_to_rgb255(value)
    if rgb is None:
        return None
    lin = [_srgb_to_linear(c) for c in rgb]
    L, a, b = _linear_to_oklab(*lin)
    C = math.sqrt(a * a + b * b)
    H = math.degrees(math.atan2(b, a))
    if H < 0:
        H += 360
    if C < 0.0001:
        C, H = 0.0, 0.0
    return f"oklch({round(L * 100, 2)}% {round(C, 4)} {round(H, 1)})"


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
            "value_oklch": to_oklch(value.strip()),
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

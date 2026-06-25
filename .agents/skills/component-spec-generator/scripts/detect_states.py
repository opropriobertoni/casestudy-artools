#!/usr/bin/env python3
"""
detect_states.py -- Deterministically detects which native interactive
pseudo-class states (:hover, :focus, :active, :disabled) actually exist in
the CSS source for each component listed in an approved tier-map.json, and
classifies any color change in that state as a derived shade (consistent
with Relative Color Syntax intent -- frontend-01-foundations Rule 35) or an
unrelated hardcoded color (a violation candidate to flag, not normalize).

This script performs NO naming or spec-writing decisions -- only binary
presence detection and a deterministic OKLCH color-relationship
classification. The OKLCH math is self-contained and was validated against
the culori reference library in the token-pipeline-setup Skill.

Usage:
    python3 detect_states.py --tier-map tier-map.json --css assets/css --output states_map.json

Run with --help for full argument details.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

# --- OKLCH math (self-contained for portability of this Skill folder) ---

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


def _oklch_from_oklch_string(value):
    m = re.match(r"oklch\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)", value.strip())
    if m:
        L_pct, C, H = (float(x) for x in m.groups())
        return (L_pct / 100, C, H)
    return None


def oklch_components(value):
    """Return (L, C, H) for any supported color literal (oklch/hex/rgb/hsl),
    or None if unparseable (gradients, keywords, var() references)."""
    direct = _oklch_from_oklch_string(value)
    if direct:
        return direct
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
    return (L, C, H)


def classify_color_relation(default_val, state_val):
    """Compare a state's color value against the element's default color.
    Returns one of: no_change_detected, new_in_state, derived_lightness,
    negligible_change, different_hue, unparseable."""
    if not state_val:
        return "no_change_detected"
    if not default_val:
        return "new_in_state"
    if default_val.strip() == state_val.strip():
        return "no_change_detected"
    d = oklch_components(default_val)
    s = oklch_components(state_val)
    if d is None or s is None:
        return "unparseable"
    dL, dC, dH = d
    sL, sC, sH = s
    hue_diff = min(abs(dH - sH), 360 - abs(dH - sH))
    chroma_diff = abs(dC - sC)
    lightness_diff = abs(dL - sL)
    if hue_diff < 8 and chroma_diff < 0.03:
        return "derived_lightness" if lightness_diff > 0.01 else "negligible_change"
    return "different_hue"


# --- CSS rule lookup ---

COLOR_PROP_RE = re.compile(r"(background-color|color|border-color)\s*:\s*([^;]+);")
STATES = ["hover", "focus", "active"]


def find_blocks(css_text, selector_pattern):
    pattern = re.compile(r"([^{}]+)\{([^{}]*)\}")
    blocks = []
    target = selector_pattern.strip()
    for m in pattern.finditer(css_text):
        selectors_raw, block_content = m.group(1), m.group(2)
        selectors = [s.strip() for s in selectors_raw.split(",")]
        for s in selectors:
            if s.endswith(target):
                start_idx = len(s) - len(target)
                if start_idx == 0 or (not s[start_idx - 1].isalnum() and s[start_idx - 1] not in ("-", "_")):
                    blocks.append(block_content)
                    break
    return blocks


def extract_colors(blocks):
    merged = {}
    for block_text in blocks:
        if not block_text:
            continue
        for m in COLOR_PROP_RE.finditer(block_text):
            merged[m.group(1)] = m.group(2).strip()
    return merged


def analyze_selector(css_text, selector):
    default_blocks = find_blocks(css_text, selector)
    default_colors = extract_colors(default_blocks)
    result = {}
    for state in STATES:
        blocks = find_blocks(css_text, f"{selector}:{state}")
        exists = len(blocks) > 0
        entry = {"exists": exists, "color_relation": None}
        if exists:
            state_colors = extract_colors(blocks)
            relations = [
                {"property": prop, "value": val, "relation": classify_color_relation(default_colors.get(prop), val)}
                for prop, val in state_colors.items()
            ]
            entry["color_relation"] = relations if relations else "no_color_change"
        result[state] = entry
    disabled_native = False
    for state in (":disabled", "[disabled]"):
        blocks = find_blocks(css_text, f"{selector}{state}")
        if blocks:
            disabled_native = True
            break
    result["disabled"] = {"exists": disabled_native, "note": "native attribute, not a class"}
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Detects which native pseudo-class states (:hover, :focus, "
        ":active, :disabled) exist in CSS for each tier-map.json component, and "
        "classifies color changes as derived-shade or different-hue (Rule 35 signal)."
    )
    parser.add_argument("--tier-map", required=True, help="Path to approved tier-map.json")
    parser.add_argument("--css", required=True, help="Directory containing CSS files")
    parser.add_argument("--output", required=True, help="Path to write states_map.json")
    args = parser.parse_args()

    tier_map_path = Path(args.tier_map)
    css_dir = Path(args.css)
    if not tier_map_path.is_file():
        print(f"ERROR: tier-map not found: {tier_map_path}", file=sys.stderr)
        sys.exit(1)
    if not css_dir.is_dir():
        print(f"ERROR: css directory not found: {css_dir}", file=sys.stderr)
        sys.exit(1)

    tier_map = json.loads(tier_map_path.read_text(encoding="utf-8"))
    css_text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in sorted(css_dir.rglob("*.css"))
    )

    output = []
    for entry in tier_map:
        if entry.get("tier") not in ("atoms", "molecules", "organisms"):
            continue
        selector = entry.get("selector")
        if not selector:
            continue
        output.append({
            "element": entry.get("element"),
            "selector": selector,
            "states": analyze_selector(css_text, selector),
        })

    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Analyzed {len(output)} component(s) -> {args.output}")


if __name__ == "__main__":
    main()

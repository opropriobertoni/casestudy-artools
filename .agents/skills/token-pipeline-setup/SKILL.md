---
name: token-pipeline-setup
description: >
  Use this Skill whenever you need to extract colors, typography, and spacing
  from CSS files and transform them into Design Tokens conforming to the W3C
  DTCG specification, generating tokens.json and tokens.css via Style Dictionary
  v4. Activate for terms like "extract tokens", "generate tokens.json", "create
  design tokens", "configure Style Dictionary", "tokens.css", "DTCG", or when the
  design-system-pipeline Workflow reaches Phase 2. Prerequisite: tier-map.json
  must already exist and be approved, with elements classified as tier "tokens".
---

# Token Pipeline Setup

## When to Use This Skill

- The `tier-map.json` already exists and has been approved, with elements of `tier: tokens` pending extraction.
- The `design-system-pipeline` workflow reaches Phase 2.
- The user asks to extract colors/typography/spacing from a CSS file, or to configure/run Style Dictionary.

## When NOT to Use This Skill

- The `tier-map.json` does not exist or has not been approved — direct the user to the `tier-classifier` skill (Phase 1) first.
- The request is to generate individual Component Specs — this is the responsibility of the `component-spec-generator` skill (Phase 3).
- The request is to audit drift between an already structured DS and an external source of truth (Figma/legacy) — this is the responsibility of the `design-system-audit` skill.
- There are no CSS files in `assets/css/` (Phase 0 manual has not been executed).

## Architectural Rules

- **Style Dictionary v4 is the canonical transformation tool — never reimplement the engine in Python.** A custom generator does not achieve real conformity with the DTCG specification (aliasing, `$type` inheritance, multiple output platforms). Re-writing this manually contradicts the rationale for adopting DTCG: real interoperability.
- **Mandatory prerequisite:** verify whether Node.js/npm is available in the workspace before installing any dependency. If absent, stop and inform the user — never assume.
- `scripts/extract_css_values.py` **never** decides `$type` or naming. It only extracts raw candidates (value + property + context). The semantic decision is always the agent's responsibility — the same separation of responsibilities as in `tier-classifier`.
- Mapping of extracted CSS property $\rightarrow$ DTCG `$type`:

| Extracted Property | DTCG `$type` |
|---|---|
| `color-literal`, `--color-*` | `color` |
| `font-size`, `padding`, `margin`, `gap`, `border-radius` | `dimension` |
| `font-family` | `fontFamily` |
| `font-weight` | `fontWeight` |
| `line-height` | `number` |
| `box-shadow` | `shadow` |

- Token naming follows the `<category>.<group>.<variant>` pattern (e.g., `color.brand.primary`, `spacing.md`). Never use the raw value as the name.
- Already existing custom properties (e.g., `--color-brand-primary`) are **high-confidence** candidates — preserve the semantic intent of the original name when generating the corresponding DTCG token.

## Execution Flow

1. Confirm that `tier-map.json` exists and was approved. Filter only elements with `tier: "tokens"`.
2. Confirm that Node.js/npm is available in the workspace. If not, stop and inform the user.
3. Run `scripts/extract_css_values.py --input assets/css --output candidates.json`.
4. Read `candidates.json`.
5. Deduplicate by exact value, group by semantic meaning, and assign DTCG `$type` according to the Architectural Rules table.
6. Name each token semantically (`<category>.<group>.<variant>`).
7. Write `app/design-system/tokens.json` in DTCG compliance (`$value`, `$type`, `$description`, and aliasing via `$ref` where two tokens share the same canonical value).
8. Verify if `style-dictionary` is installed in the project. If not, install it with `npm install style-dictionary@4 --save-dev`.
9. Copy `assets/sd.config.template.json` to the root of the project as `sd.config.json`, adjusting the `source` and `buildPath` paths to the actual project structure. Do not regenerate the config from scratch.
10. Run `npx style-dictionary build --config sd.config.json`.
11. Confirm that `app/design-system/tokens.css` was correctly generated.
12. STOP. Present `tokens.json` and `tokens.css` to the user.
13. DO NOT proceed to Phase 3 of the Workflow without explicit approval.

## External References

- `scripts/extract_css_values.py` — heuristic extractor via regex (pure Python stdlib, no external dependencies). **Documented limitation:** it is not a full CSS parser (no AST) — it may miss values in complex nested selectors. Treat candidates as a starting point, not absolute truth. Run first with `--help`. Treat as a black box.
- `assets/sd.config.template.json` — Style Dictionary v4 configuration template, validated against actual builds. Copy and adapt paths, never rewrite from scratch.

## Examples

**Input** (entry in `candidates.json`):
```json
{"file": "assets/css/components.css", "selector_context": ":root",
 "property": "--color-brand-primary", "value": "#ff5a1f"}
```

**Output** (corresponding entry in `tokens.json`):
```json
{
  "color": {
    "brand": {
      "primary": {
        "$value": "#ff5a1f",
        "$type": "color",
        "$description": "Primary brand color, used in CTAs"
      }
    }
  }
}
```

**Input:**
```json
{"file": "assets/css/components.css", "selector_context": ".btn-primary",
 "property": "border-radius", "value": "8px"}
```

**Output:**
```json
{
  "radius": {
    "md": {
      "$value": "8px",
      "$type": "dimension",
      "$description": "Standard border radius for buttons and cards"
    }
  }
}
```

## Validation Checklist

- [ ] Single responsibility confirmed? (extracts and transforms tokens — does not classify tiers, does not generate specs)
- [ ] External scripts referenced with `--help`?
- [ ] Node.js/npm prerequisite checked before installing dependencies?
- [ ] Absence of ambiguous behaviors?
- [ ] Principle of Lack of Surprise respected?

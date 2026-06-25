---
name: token-pipeline-setup
description: >
  Use this Skill whenever you need to extract colors, typography, and spacing
  from CSS files and transform them into Design Tokens conforming to the W3C
  DTCG specification, in 3 layers (Global → Semantic → Component) with colors in
  OKLCH, generating tokens.json and tokens.css via Style Dictionary v4. Activate for
  terms like "extract tokens", "generate tokens.json", "create design tokens",
  "configure Style Dictionary", "tokens.css", "DTCG", "OKLCH", or when the
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

- **Colors always in OKLCH in the Global layer (Rule 34 — `frontend-01-foundations`).** `scripts/extract_css_values.py` already delivers `value_oklch` calculated deterministically for all color candidates — always use this field as the `$value` of the Global token, never the original hex/rgb/hsl. When `value_oklch` is `null` (gradients, `currentColor`, keywords), report the candidate to the user instead of inventing a conversion.
- **Mandatory 3-layer structure (Rule 33 — `frontend-01-foundations`):** `global` $\rightarrow$ `semantic` $\rightarrow$ `component`. A `component` token never points directly to a raw value — it always references a `semantic` token via `$ref` (`{semantic.color.action.primary}`), which in turn references a `global` token (`{global.color.orange.500}`). Skipping the Semantic layer is a direct violation of Rule 33.
  - **Global:** raw palette values (a 1:1 parity with what the original CSS contained, already converted to OKLCH).
  - **Semantic:** role of use (`action.primary`, `feedback.danger`, `surface.elevated`) — named by function, not by color.
  - **Component:** specific component reference to a Semantic token (`button.background`, `card.border`).
- Token naming follows the `<layer>.<category>.<group>.<variant>` pattern (e.g., `global.color.orange.500`, `semantic.color.action.primary`). Never use the raw value as the name.
- Already existing custom properties (e.g., `--color-brand-primary`) are **high-confidence** candidates — preserve the semantic intent of the original name when deciding in which layer (Global or Semantic) the token should reside.

## Execution Flow

1. Confirm that `tier-map.json` exists and was approved. Filter only elements with `tier: "tokens"`.
2. Confirm that Node.js/npm is available in the workspace. If not, stop and inform the user.
3. Run `scripts/extract_css_values.py --input assets/css --output candidates.json`.
4. Read `candidates.json`.
5. Deduplicate by exact value. For color candidates, always use `value_oklch` (already calculated by the script) as `$value` — never the original hex/rgb/hsl. Group by semantic meaning and assign DTCG `$type` according to the Architectural Rules table.
6. Decide the layer of each token: raw palette value $\rightarrow$ `global`; use role $\rightarrow$ `semantic` (referencing `global` via `$ref`); specific component use $\rightarrow$ `component` (referencing `semantic` via `$ref`). Name them following `<layer>.<category>.<group>.<variant>`.
7. Write `app/design-system/tokens.json` with the three root-level namespaces (`global`, `semantic`, `component`), in compliance with DTCG (`$value`, `$type`, `$description`, real aliasing via reference `{path.to.token}` between layers — never a `component` pointing directly to `global`).
8. Verify if `style-dictionary` is installed in the project. If not, install it with `npm install style-dictionary@4 --save-dev`.
9. Copy `assets/sd.config.template.json` to the root of the project as `sd.config.json`, adjusting the `source` and `buildPath` paths to the actual project structure. Do not regenerate the config from scratch.
10. Run `npx style-dictionary build --config sd.config.json`.
11. Confirm that `app/design-system/tokens.css` was correctly generated.
12. STOP. Present `tokens.json` and `tokens.css` to the user.
13. DO NOT proceed to Phase 3 of the Workflow without explicit approval.

## External References

- `scripts/extract_css_values.py` — heuristic extractor via regex (pure Python stdlib, no external dependencies). **Calculates `value_oklch` automatically** for every color candidate (validated against the `culori` reference library, convergence to ~1e-7). **Documented limitation:** it is not a full CSS parser (no AST) — it may miss values in complex nested selectors. Treat candidates as a starting point, not absolute truth. Run first with `--help`. Treat as a black box.
- `assets/sd.config.template.json` — Style Dictionary v4 configuration template, validated against actual builds with the 3-layer structure (confirms correct resolution of chained `var()`: `component` $\rightarrow$ `semantic` $\rightarrow$ `global`). Copy and adapt paths, never rewrite from scratch.

## Examples

**Input** (entry in `candidates.json`, already enriched by the script):
```json
{"file": "assets/css/components.css", "selector_context": ":root",
 "property": "--color-brand-primary", "value": "#ff5a1f",
 "value_oklch": "oklch(68.24% 0.2108 37.7)"}
```

**Output** (corresponding entries in `tokens.json`, 3 layers):
```json
{
  "global": {
    "color": {
      "orange": { "500": { "$value": "oklch(68.24% 0.2108 37.7)", "$type": "color" } }
    }
  },
  "semantic": {
    "color": {
      "action": {
        "primary": {
          "$value": "{global.color.orange.500}",
          "$type": "color",
          "$description": "Primary action color, used in CTAs"
        }
      }
    }
  },
  "component": {
    "button": {
      "background": { "$value": "{semantic.color.action.primary}", "$type": "color" }
    }
  }
}
```

**Input:**
```json
{"file": "assets/css/components.css", "selector_context": ".btn-primary",
 "property": "border-radius", "value": "8px", "value_oklch": null}
```

**Output:**
```json
{
  "global": {
    "radius": { "100": { "$value": "8px", "$type": "dimension" } }
  },
  "semantic": {
    "radius": {
      "interactive": {
        "$value": "{global.radius.100}",
        "$type": "dimension",
        "$description": "Standard radius for interactive elements"
      }
    }
  }
}
```

## Validation Checklist

- [ ] Single responsibility confirmed? (extracts and transforms tokens — does not classify tiers, does not generate specs)
- [ ] External scripts referenced with `--help`?
- [ ] Node.js/npm prerequisite checked before installing dependencies?
- [ ] Every color token in the Global layer uses `value_oklch`, never hex/rgb/hsl?
- [ ] No `component` token references `global` directly, skipping `semantic`?
- [ ] Absence of ambiguous behaviors?
- [ ] Principle of Lack of Surprise respected?

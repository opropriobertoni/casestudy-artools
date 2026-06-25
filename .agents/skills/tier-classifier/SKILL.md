---
name: tier-classifier
description: >
  Use this Skill whenever you need to classify a design-system.html (or similar
  reference HTML) in the Five-Tier taxonomy — Foundations, Tokens, Atoms,
  Molecules, Organisms — generating a structured tier-map.json. Activate for
  terms like "classify design system", "map components in tiers", "Five-Tier
  audit", "what tier is this element", "organize atoms molecules organisms", or
  when it is necessary to decide in which folder under app/design-system/ an HTML
  component should reside. This Skill is the mandatory entry point (Phase 1)
  of the design-system-pipeline Workflow — invoke it before any token
  extraction or Component Specs generation.
---

# Tier Classifier

## When to Use This Skill

- The user asks to classify, map, or organize a `design-system.html` in the Five-Tier taxonomy.
- The `design-system-pipeline` workflow reaches Phase 1.
- The user asks which tier (Foundations/Tokens/Atoms/Molecules/Organisms) a specific element should reside in.

## When NOT to Use This Skill

- `design-system.html` does not yet exist in the reference directory (Phase 0 manual via Reference Cleaned HTML → Extract HTML Design System prompts has not been executed). Instruct the user to run the manual prompts first.
- The request is to extract color/typography/spacing values — this is the responsibility of the `token-pipeline-setup` skill (Phase 2).
- The request is to generate individual Component Specs — this is the responsibility of the `component-spec-generator` skill (Phase 3).
- The request is to audit divergence (drift) between an already structured DS and an external source of truth (Figma/legacy) — this is the responsibility of the `design-system-audit` skill, not this one.

## Architectural Rules

| Tier | Classification Criteria |
|---|---|
| `foundations` | Prose of global principles — voice & tone, accessibility, aesthetic prohibitions. Not an HTML element, but textual rules. |
| `tokens` | Raw deterministic value (color, spacing, typography) without its own interactive behavior. |
| `atoms` | Indivisible element with its own behavior (button, input, badge). Decomposing it destroys its function. |
| `molecules` | 2+ atoms combined with a single joint responsibility (form field: label + input + validation). |
| `organisms` | Broad functional zone composing multiple molecules/atoms — usually an entire section (header, footer, hero, table). |

- Each element receives **exactly one** tier. Never assign two tiers to the same element — this indicates that the element needs to be decomposed into smaller parts before classifying.
- The `parse_html.py` script **never** decides tiers. It only extracts structure (tag, id, classes, section comment, text preview). The semantic decision is always the agent's responsibility — preserving the single responsibility principle between script (deterministic) and Skill (interpretative).
- In case of ambiguity between two tiers, ask the user. Never assume — an incorrect classification in Phase 1 contaminates Phases 2 and 3 of the Workflow entirely.

## Execution Flow

1. Confirm that `design-system.html` exists in the reference directory. If it does not exist, stop and inform the user.
2. Run `scripts/parse_html.py --input design-system.html --output candidates.json`.
3. Read `candidates.json`.
4. For each candidate, classify it into exactly one tier using the Architectural Rules table above.
5. Discard candidates that are pure structural noise (wrappers without visual or interactive function of their own) — record this decision in the justification.
6. Write `tier-map.json`: a list of `{element, tier, justification}` objects, with `justification` in a single line.
7. Present `tier-map.json` to the user and stop. Do not proceed to Phase 2 of the Workflow without explicit approval.

## External References

- `scripts/parse_html.py` — Python script (pure stdlib, no external dependencies). Run first with `--help` to confirm the exact signature before invoking. Treat as a black box: do not read or modify the script's internal code.

## Examples

**Input** (entry in `candidates.json`):
```json
{"tag": "button", "id": null, "classes": ["btn", "btn-primary"],
 "section_comment": "hero", "text_preview": "Get started now"}
```

**Output** (corresponding entry in `tier-map.json`):
```json
{"element": "button.btn-primary (CTA in hero section)",
 "tier": "atoms",
 "justification": "Indivisible interactive unit, without composition of other elements."}
```

**Input:**
```json
{"tag": "header", "id": "main-nav", "classes": ["site-header"],
 "section_comment": "hero", "text_preview": ""}
```

**Output:**
```json
{"element": "header#main-nav",
 "tier": "organisms",
 "justification": "Global navigation functional zone, composes multiple atoms (logo, links)."}
```

## Validation Checklist

- [ ] Single responsibility confirmed? (classifies — does not extract tokens, does not generate specs)
- [ ] External scripts referenced with `--help`?
- [ ] Absence of ambiguous behaviors? (rule to ask in case of doubt is explicit)
- [ ] Principle of Lack of Surprise respected?

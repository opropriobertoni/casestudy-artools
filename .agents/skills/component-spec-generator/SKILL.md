---
name: component-spec-generator
description: >
  Use this Skill whenever you need to generate Component Specs in Markdown
  from elements already classified as atoms, molecules, or organisms in the
  tier-map.json, following the CUBE CSS convention (Block + Exceptions via
  data-attributes, never compound modifier classes). Activate for terms like
  "generate component spec", "document this component", "create spec for
  button/card/header", "Phase 3 of design-system-pipeline", or when you need to
  map native states (hover/focus/active/disabled) and exceptions (programmatic
  states/variants) of a component to the 2-5KB spec format. Prerequisite:
  tier-map.json and tokens.json must already exist and be approved.
---

# Component Spec Generator

## When to Use This Skill

- The `tier-map.json` and `tokens.json` already exist and have been approved.
- The `design-system-pipeline` workflow reaches Phase 3.
- The user asks to document, specify, or generate a spec for a specific component (atom, molecule, or organism).

## When NOT to Use This Skill

- `tier-map.json` or `tokens.json` do not exist/have not been approved — direct the user to `tier-classifier` (Phase 1) or `token-pipeline-setup` (Phase 2) first.
- The request is to physically rewrite the source CSS/HTML to actual CUBE CSS — this is **out of scope** for this Skill and pipeline (see Path 1 below). This Skill documents and prescribes a blueprint; it does not refactor existing code.
- The request is to audit drift between an already structured DS and an external source of truth — this is the responsibility of `design-system-audit`.

## Architectural Rules

- **Path 1 — Documentation Pipeline, not Active Transformation.** The original reference (Phase 0) does not start in CUBE CSS — it starts in whatever convention the source site uses (BEM, utility, ad-hoc). This Skill **documents what exists** in the source convention and **prescribes** the target CUBE name as a blueprint. It never rewrites `assets/css/` or `design-system.html`. Migrating to actual CUBE CSS is future engineering work (a new Web Component), outside of this pipeline.
- **`status` is always `proposed` in this Skill — never `documented`.** No actual Web Component has been implemented at this stage of the pipeline; the spec is a blueprint, not a confirmation of something already built.
- **Rule 14 (`frontend-01-foundations`):** `margin*` properties extracted from the source CSS are always excluded from the Block table — they belong to Composition, never to the Block. `padding*` remains (internal spacing is legitimate in the Block).
- **Rule 15 (`frontend-01-foundations`):** all programmatic states (loading, open, expanded, etc. — signaled by `standalone_state_classes` in the output of `detect_exceptions.py`) are documented as a CUBE Exception via `data-state="value"`, never as an additional class (`is-*`/`has-*` in the target).
- **Rule 16 (`frontend-01-foundations`):** the Target Markup of each spec uses brackets grouping notation (`[ block: name ]`) when commenting on class composition.
- **Rule 35 (`frontend-01-foundations`):** when `detect_states.py` classifies a state as `different_hue`, this is a **violação to report in the "Violações Detectadas" section**, never to be silenced or normalized as a valid derivation. `derived_lightness` and `negligible_change` are compliant and do not generate violations.
- Native states (`:hover`, `:focus`, `:active`) remain pseudo-classes under any methodology — CUBE CSS does not replace them with `data-attributes` (they are native to the browser, not programmatic). `:disabled` is already a native HTML attribute — naturally compliant, no migration needed.
- `scripts/detect_states.py` and `scripts/detect_exceptions.py` **never** decide the final CUBE naming or generate the spec. They only produce deterministic candidates (presence/absence of state, color relation, class clusters). The final semantic decision is always the agent's responsibility.
- Spec size: the 2-5KB range is a **ceiling**, not a floor — a simple atom can be below 2KB without issue. Never exceed 5KB; if this happens, trim non-essential details — never cut the "Violações Detectadas" section.

## Execution Flow

1. Confirm that `tier-map.json` and `tokens.json` exist and have been approved.
2. Run `scripts/detect_states.py --tier-map tier-map.json --css assets/css --output states_map.json`.
3. Run `scripts/detect_exceptions.py --html design-system.html --output exceptions_map.json`.
4. For each element with `tier` in `atoms`/`molecules`/`organisms` in the `tier-map.json`:
   a. Locate its record in `states_map.json` (by `selector`).
   b. Locate its cluster in `variant_clusters` and any `standalone_state_classes` whose `co_occurring_classes` includes its class(es) in `exceptions_map.json`.
   c. Extract Block properties from the source CSS, **excluding `margin*`** (Rule 14).
   d. Map each property to a token in `tokens.json` via `$ref` whenever there is a value match; if there is no matching token, report it as pending — never invent a `$ref`.
   e. Classify each class in the cluster: `style_variant` $\rightarrow$ `data-variant`; `state_modifier` $\rightarrow$ `data-state` (Rule 15).
   f. For any state with `color_relation: different_hue`, report it under "Violações Detectadas", citing Rule 35.
   g. Fill out `assets/component-spec.template.md` and write to `app/design-system/specs/<tier>/<name>.md`. Never alter the section structure of the template.
5. Confirm that each spec is within the 5KB limit.
6. STOP. Present the list of generated specs.
7. DO NOT proceed to Phase 4 of the Workflow without explicit approval.

## External References

- `scripts/detect_states.py` — detects the presence of `:hover`/`:focus`/`:active`/`:disabled` and classifies color relations via OKLCH (mathematics validated against the `culori` library in `token-pipeline-setup`). Treat as a black box. Run with `--help` first.
- `scripts/detect_exceptions.py` — clusters HTML classes from the source by shared root (style variants) and isolates `is-*`/`has-*` classes with their co-occurrence context (programmatic states). Does not decide final CUBE naming. Treat as a black box.
- `assets/component-spec.template.md` — fixed skeleton with placeholders. Copy and fill out, never rewrite the section structure.

## Examples

**Compliant case** (state derives correctly, no violation):

Input (`states_map.json`):
```json
{"selector": ".btn-primary", "states": {"hover": {"exists": true,
 "color_relation": [{"property": "background-color",
  "relation": "derived_lightness"}]}}}
```

Output (spec snippet): "Violações Detectadas" section = `"Nenhuma."`

**Violation case** (Rule 35):

Input (`states_map.json`):
```json
{"selector": ".btn-secondary", "states": {"hover": {"exists": true,
 "color_relation": [{"property": "background-color", "value": "#ff0000",
  "relation": "different_hue"}]}}}
```

Output (spec snippet):
```markdown
## Violações Detectadas
`:hover` uses `#ff0000`, a hardcoded hex with no hue/chroma relation to the default value (Rule 35) — recommended to derive via Relative Color Syntax or `color-mix()` instead of an independent literal.
```

## Validation Checklist

- [ ] Single responsibility confirmed? (documents and prescribes — does not classify tiers, does not extract tokens, does not rewrite source CSS)
- [ ] External scripts referenced with `--help`?
- [ ] `status` always `proposed`, never `documented`?
- [ ] `margin*` excluded from the Block table (Rule 14)?
- [ ] Programmatic states mapped to `data-state`, never class (Rule 15)?
- [ ] Violations of Rule 35 reported, never silenced?
- [ ] Each spec within the 5KB limit?

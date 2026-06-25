---
title: Design System Pipeline
description: Orchestrates Five-Tier classification, Design Tokens extraction, and Component Specs generation from an already extracted design-system.html (Phase 0 manual).
---

# Design System Pipeline

## Pre-condition (Phase 0 — manual, outside Antigravity)
Before invoking this workflow, confirm that the following exist in the reference directory:
- `design-system.html` (output of the Extract HTML Design System prompt)
- `STACK.md` (output of the Reference Cleaned HTML prompt)
- `assets/css/`, `assets/js/`, `assets/images/svg/` already extracted

If any of these do not exist: STOP and instruct the user to run the Reference Cleaned HTML → Extract HTML Design System prompts manually first. Do not attempt to bypass this step.

---

## Phase 1 — Five-Tier Classification
1. Load the `tier-classifier` skill.
2. Read `design-system.html` section by section.
3. Classify each element into exactly one tier: `foundations`, `tokens`, `atoms`, `molecules`, `organisms`.
4. Write `tier-map.json`: a list of `{element, tier, justification}` (justification in a single line, with no additional prose).
5. STOP. Present `tier-map.json` to the user.
6. DO NOT proceed to Phase 2 without explicit approval.
7. In case of ambiguity between two tiers: ask the user. NEVER make assumptions.

---

## Phase 2 — Design Tokens Extraction
1. Load the `token-pipeline-setup` skill.
2. Use only the elements approved as `tokens` in `tier-map.json`.
3. Extract color, typography, and spacing from the original CSS (`assets/css/`).
4. Write `app/design-system/tokens.json` in compliance with DTCG (`$value`, `$type`, `$description`, aliasing where applicable).
5. Run Style Dictionary v4 (`convertToDTCG` if there are mixed legacy tokens) to generate `app/design-system/tokens.css`.
6. STOP. Present the diff of `tokens.json` and `tokens.css`.
7. DO NOT proceed to Phase 3 without explicit approval.

---

## Phase 3 — Component Specs Generation
1. Load the `component-spec-generator` skill.
2. For each element classified as `atoms`, `molecules`, or `organisms`:
   - Generate spec in `app/design-system/specs/<tier>/<name>.md`.
   - Include states: `default`, `hover`, `active`, `focus`, `disabled` — only those that exist in the original reference.
   - Limit each spec to 2–5KB.
   - YAML Frontmatter: `name`, `tier`, `status: proposed`.
3. IT IS FORBIDDEN to include the full `<template>` code or transcribed tokens inside the spec — use only a reference (`$ref`) to `tokens.json`.
4. STOP. Present the list of generated specs.

---

## Phase 4 — DESIGN.md Consolidation
1. Without dedicated Skill. Execute following the `design-system-architecture.md` rule.
2. Compile YAML Frontmatter (semantic properties + raw hexadecimals) followed by Foundations prose (Voice & Tone, accessibility, aesthetic prohibitions).
3. Write `app/design-system/DESIGN.md`.
4. Present the final summary: count of generated tokens, atoms, molecules, and organisms.

---

## Transversal Rules
- Every STOP requires explicit user approval before proceeding to the next phase.
- Class naming, attributes, and values MUST be extracted literally from `design-system.html`. NEVER invent or approximate.
- If the user rejects a classification in Phase 1, correct `tier-map.json` and seek approval again before continuing.

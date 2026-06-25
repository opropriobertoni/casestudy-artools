---
trigger: model_decision
description: Apply when building or editing a UI component: Web Components/Shadow DOM, native dialog/popover/anchor-positioning/view-transitions/accordions, JS patterns, state (Zustand/Signals), or 3D/animation (WebGPU, Three.js, Rive).
---

# Frontend Rules — 02. Components & Interactivity
*Rules consulted per-component during day-to-day coding: visual isolation, native interactive APIs, JS design patterns, state management, and animation/3D engines. Part 2 of 3 — see also `frontend-foundations.md` and `frontend-performance-architecture.md`.*

**Table of Contents**
1. Visual Isolation & Web Components
2. Native APIs & Interactivity
3. JavaScript Design Patterns & State Management
4. Graphics, 3D & Animation Engines

### 1. Visual Isolation & Web Components
1. `@scope (.root) to (.limit)` — donut scope — to contain component styles without bleeding into injected children. _Exclusion: never use scope without a lower bound when there is a risk of an injected child that should escape the parent's style._
2. Use `:scope` to reference the local scope root (specificity 0-1-0). _Exclusion: never use `:root` or manually repeat the root selector inside the `@scope` block._
3. Rely on the browser's scope proximity to resolve conflicts between scopes of equal specificity. _Exclusion: never manually inflate selector specificity to "win" a more distant scope._
4. Use `&` for direct hierarchical correlation within nested blocks. _Exclusion: never manually duplicate the parent selector when `&` resolves it._
5. Declarative Shadow DOM (`<template shadowrootmode="open">`) for server-rendered Web Components. _Exclusion: never depend on `attachShadow()` via JS when the component needs to render correctly before JS executes._
6. `shadowrootclonable` when the component needs to support `cloneNode()` or serialization. _Exclusion: never omit this attribute if programmatic cloning is expected._
7. Style slotted content via `::slotted()`. _Exclusion: never assume global page styles reach slot content without the pseudo-element._
8. Protect any new/unstable CSS feature with `@supports (...)`. _Exclusion: never ship a CSS feature without a structured fallback when browser support is partial._

### 2. Native APIs & Interactivity
9. `<dialog>.showModal()` when the interaction requires native focus-trap (preventing screen readers from escaping the modal context) together with blocking `role="dialog"`/`alertdialog` semantics. _Exclusion: never implement a manual JS focus trap when `<dialog>` already guarantees this containment; never use a simple popover for a flow that requires blocking modality._
10. `popover` attribute for light, non-blocking overlays (tooltips, menus) with automatic light-dismiss. _Exclusion: never manage z-index manually for overlays eligible for a popover — the native Top Layer handles this._
11. `popovertarget` + `popovertargetaction` pair on the trigger; the browser also manages `aria-expanded` and keyboard focus order automatically for elements wired this way. _Exclusion: never write click handlers to open/close popovers, and never manually manage `aria-expanded` in JS, when the native attribute pair covers the case._
12. `popover="manual"` only when automatic light-dismiss/ESC is explicitly undesired. _Exclusion: never use manual as the default._
13. Animate opening/closing via `@starting-style` + `transition-behavior: allow-discrete`. _Exclusion: never import a JS animation library for `display: none` transitions when the native API covers the case._
14. Anchor floating elements via `anchor-name` on the anchor and `position-anchor` on the positioned element. _Exclusion: never calculate positions via `getBoundingClientRect()` + manual JS when CSS Anchor Positioning is available._
15. `position-area` for directional positioning and `@position-try` as a fallback. _Exclusion: never leave an anchored element without a fallback — it will clip/overflow near viewport edges._
16. `<details name="group">` for native mutually exclusive accordions. _Exclusion: never write JS to close sibling `<details>` elements; always accompany them with a `<summary>` as the toggle control._
17. `::backdrop` to style the `<dialog>` backdrop. _Exclusion: never simulate a backdrop with a manually positioned `div`/z-index when the native pseudo-element solves it._
18. View Transitions API (`document.startViewTransition()`) to animate DOM mutations in SPA flows. _Exclusion: never hand-orchestrate element position interpolation in JS when the native API covers the transition._
19. In MPA, declare `@view-transition { navigation: auto; }` purely in CSS. _Exclusion: never add JavaScript overhead for MPA navigation transitions when the CSS declaration alone covers it._
20. Use `::view-transition-old()`/`::view-transition-new()` to customize transition frames. _Exclusion: never hand-build a cross-fade/morph effect in JS when these native pseudo-elements resolve it._

### 3. JavaScript Design Patterns & State Management
21. Encapsulation via native ECMAScript Modules (ESM). _Exclusion: never implement the Module Pattern via manual closure/IIFE when native ESM is available in the build._
22. No side effects at module root level. _Exclusion: never execute logic with a side effect at a module's top level — it defeats effective Tree Shaking._
23. Separate components into Presentational (pure, stateless, props-only) and Container (coupled to data fetching/lifecycle). _Exclusion: never mix network-fetch or state logic inside a purely presentational component._
24. Compound Components + Context API for design-system component families. _Exclusion: never manually duplicate configuration props across sibling components when Compound Components solves it._
25. Middleware for chained interception logic (network, routing). _Exclusion: never scatter ad-hoc interception logic across the codebase when a centralized middleware pipeline solves it._
26. Mediator + Facade to abstract DOM manipulation libraries and centralize events. _Exclusion: never access a third-party DOM library directly from scattered call sites when this combined layer centralizes access._
27. Granular selectors (Zustand-style) when consuming global state. _Exclusion: never subscribe to the entire store when only a slice of state is needed in the component._
28. Push-based reactive primitives (Signals) for high-frequency update scenarios (1000+ subscribers). _Exclusion: never use a mutation that triggers a full component-tree re-render for an update that affects a single DOM node, when Signals are available._

### 4. Graphics, 3D & Animation Engines
29. WebGPU over WebGL for scenes with instance/particle volume beyond WebGL's practical pipeline capacity (~50k+) or requiring Compute Shaders. _Exclusion: never choose WebGL as the default engine for visualizations at this scale._
30. TSL (Three.js Shading Language) over raw GLSL strings inside Three.js/React Three Fiber components. _Exclusion: never write a shader as an untyped literal GLSL string when TSL is available in the stack — it loses TypeScript compiler error tracing._
31. Rive (`.riv` with State Machines) over Lottie for animation requiring conditional/interactive logic (hover, branching, states). _Exclusion: never implement animation branching via JS scheduling on top of a Lottie player when Rive solves it declaratively._
32. Lottie remains acceptable for purely decorative animation with no conditional logic. _Exclusion: never force a migration to Rive when there is no need for interactive state._
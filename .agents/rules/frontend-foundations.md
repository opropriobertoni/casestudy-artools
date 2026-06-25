---
trigger: always_on
---

# Frontend Rules — 01. Foundations
*Project-level setup configured once at project start: reset, naming architecture, design tokens, base semantics, and TypeScript config. Part 1 of 3 — see also `frontend-components-interactivity.md` and `frontend-performance-architecture.md`. Naming methodology: CUBE CSS (BEM superseded).*

**Table of Contents**
1. Reset & Base Behavior
2. CSS Architecture: CUBE CSS & Cascade Layers
3. HTML Semantics, SEO & Accessibility
4. Design Tokens, Fluid Layout & Geometry
5. TypeScript Standards

### 1. Reset & Base Behavior
1. `box-sizing: border-box` on `*, *::before, *::after`. _Exclusion: never calculate dimensions assuming `content-box`._
2. `text-size-adjust: none` on `html`. _Exclusion: never rely on mobile OS automatic font inflation._
3. Clear vertical spacing exclusively via logical properties (`margin-block-end: 0`) when the intent is solely to dictate vertical rhythm. _Exclusion: never use a generic `margin: 0` on all 4 sides when only block spacing is intended._
4. `img, picture, video, canvas, svg { display: block; max-width: 100% }`. _Exclusion: never leave media inline — it generates empty baseline space ("magic space")._
5. `font: inherit` on `input, button, textarea, select`. _Exclusion: never allow mobile form fields with `font-size` < 16px — it triggers automatic zoom on iOS._
6. `text-wrap: balance` on multi-line headings. _Exclusion: never leave multi-line titles unbalanced when supported._
7. `text-wrap: pretty` on paragraphs. _Exclusion: never allow an avoidable orphan line when supported._
8. `interpolate-size: allow-keywords` only within `@media (prefers-reduced-motion: no-preference)`, to animate between a fixed value and `auto` (accordions). _Exclusion: never apply outside the reduced-motion guard; never use JS `ResizeObserver` when natively supported._
9. `overflow-wrap: break-word` on headings/paragraphs that receive dynamically generated output (e.g., LLMs). _Exclusion: never leave external text without overflow protection (long strings, URLs without spaces)._
10. `isolation: isolate` on AI-injected or dynamically mounted component root containers, establishing a new stacking context. _Exclusion: never leave an AI-injected widget root without its own stacking context — risk of z-index collisions with host page elements._
11. Reset always inside `@layer reset`. _Exclusion: never declare a reset outside a named layer._
12. Adopt Modern Reset (Bell/Comeau style). _Exclusion: never use total destructive reset (Eric Meyer) or Normalize.css — both are obsolete for modern Baseline browsers._

### 2. CSS Architecture: CUBE CSS & Cascade Layers
13. Strictly separate CSS into 4 layers (CUBE): Composition, Utility, Block, Exception. _Exclusion: never mix external spatial layout responsibilities inside the Block layer._
14. Minimalist Block layer — only the visual skeleton of the component. _Exclusion: never place external padding/margin or generic visual decoration on the Block class; delegate to Composition and Utility._
15. State/variation via `data-attributes` (`data-state="loading"`), never an additional class. _Exclusion: never create an `is-*` class for state; the attribute covers the same semantics with native compatibility for JS and assistive technology._
16. Group classes by category using square brackets in the markup (`[ block ] [ composition ] [ utilities ]`). _Exclusion: never scramble classes from different layers without this visual grouping._
17. Utility-layer classes must be drawn from a finite, documented set anchored to Design Tokens. _Exclusion: never improvise an ad-hoc utility class outside that documented set._
18. Prefix JS behavior hooks with `.js-`, decoupled from the style class. _Exclusion: never use a structural style class (e.g., `.card-header`) as a JS mutation selector._
19. Declare the full Cascade Layers hierarchy at the top of the file. _Exclusion: never leave layer ordering implicit or partial._
20. Third-party CSS always inside a low-priority `layer(vendor)`. _Exclusion: never import an external library outside a layer._
21. Resolve specificity conflicts with third parties via layer ordering. _Exclusion: never use `!important` to override external library CSS when `@layer` resolves it._
22. All product CSS must reside inside a named layer. _Exclusion: never leave critical CSS outside any layer (unallocated CSS has absolute priority over all normal layers)._
23. When using `!important` within the layer system, remember the order inverts (the layer declared first wins). _Exclusion: never assume `!important` follows the same priority order across layers as normal declarations._

### 3. HTML Semantics, SEO & Accessibility
24. Replace generic `<div>`/`<span>` tags with semantic equivalents whenever one exists. _Exclusion: never wrap primary content in a `<div>` when `<main>` applies._
25. Exactly one `<main>` per page, marking the primary utility of the URL. _Exclusion: never use `<main>` for secondary content (sidebar/footer)._
26. `<nav>` only for real primary/secondary navigation blocks. _Exclusion: never use `<nav>` for a list of links without a navigational function._
27. `<article>` only for content that retains meaning outside the context of the page. _Exclusion: never use `<article>` for a widget that only makes sense within the current page._
28. `<section>` always with its own heading, grouping thematically related content. _Exclusion: never use `<section>` as a generic style container without a heading._
29. Every `<figure>` must have a `<figcaption>` when the image carries explanatory context. _Exclusion: never leave `<figure>` without a structural caption when relevant textual context exists._
30. Strict heading hierarchy: a single `<h1>`, never skip levels (h2→h4 is forbidden). _Exclusion: never use headings for visual font-size effects — that is the job of CSS._
31. `<i>`/`<b>` for purely visual italics/bold; `<em>`/`<strong>` only for real semantic emphasis. _Exclusion: never use semantic tags solely for visual formatting._
32. Every navigable state change must reflect in the History API (a real URL). _Exclusion: never gate deep content behind a conditional state toggle alone — it isolates pages from crawler discovery and breaks shareable links._

### 4. Design Tokens, Fluid Layout & Geometry
33. Tokens in 3 layers (Global → Semantic → Component); Component always references a Semantic token. _Exclusion: never point a Component token directly to a Global value, skipping the Semantic layer._
34. Color always in OKLCH for any programmatic palette generation. _Exclusion: never use HSL to derive luminosity variations when perceptual contrast consistency is required._
35. Derive color variations (hover, subtle, ghost, alpha) via Relative Color Syntax. _Exclusion: never hardcode a second color variable for states when it can be derived mathematically from the base._
36. Register animatable custom properties via `@property` with a defined `syntax`. _Exclusion: never transition a custom property that has not been registered via `@property`._
37. Reusable components declare `container-type: inline-size` on the parent and react via `@container`. _Exclusion: never use `@media` (viewport) to decide the internal layout of a component whose insertion context is uncertain._
38. Use `cqi`/`cqb` to size fonts/elements relative to the container. _Exclusion: never use `vw`/`vh` for an element inside a container whose width is not that of the viewport._
39. Style Queries (`@container style(--var: value)`) to react logically to parent custom properties. _Exclusion: never create a JS listener/observer just to replicate declarative conditional style changes._
40. Use `subgrid` when a child needs to align to a common grid track of the parent. _Exclusion: never manually recreate track dimensions on the child._
41. Prefer `svh`/`lvh` over `dvh` in continuous touch-interaction contexts; use `lvh` when the layout can assume the native UI is collapsed, and `svh` when the guarantee required is that nothing may ever be cut off. _Exclusion: never use `dvh` by default without evaluating the kinetic recalculation cost (layout thrashing) in production._
42. `clamp(min, preferred, max)` for fluid typography/dimensions. _Exclusion: never repeat the same property across multiple fixed media query blocks, and never lock the upper limit of `clamp()` ignoring the user's zoom/accessibility settings._

### 5. TypeScript Standards
43. `tsconfig` with `strict: true`, `noUncheckedIndexedAccess: true`, and `noImplicitOverride` enabled mandatorily. _Exclusion: never ship a TypeScript project without these three flags active._
44. `satisfies` instead of `as Type` when the goal is to validate against a type while preserving literal/narrow inference. _Exclusion: never use a type assertion (`as Type`) as a substitute for `satisfies` for this purpose — it widens inference and loses specificity._
45. `unknown` (never `any`) at network data boundaries (REST/GraphQL). _Exclusion: never type a network response as `any` — it requires a Type Guard/narrowing before any property access._
---
trigger: model_decision
description: Apply for performance optimization, system architecture, or security: fetchpriority, scheduler.yield, Web Workers, Core Web Vitals, RSC/Islands/microfrontends rendering strategy, bundle splitting, Trusted Types/XSS.
---

# Frontend Rules — 03. Performance & Architecture
*System-level decisions revisited during optimization or stack-architecture moments, not during line-by-line coding: rendering pipeline, network loading, main-thread runtime, rendering paradigm, microfrontends, and security. Part 3 of 3 — see also `01-foundations.md` and `02-components-interactivity.md`.*

**Table of Contents**
1. Rendering, Network & Runtime Performance
2. System Design: Architecture, Streaming, RSC & Islands
3. Security: DOM XSS Prevention

### 1. Rendering, Network & Runtime Performance
1. `fetchpriority="high"` on the `<img>` element representing the LCP. _Exclusion: never apply to more than one element on the same page — it dilutes the signal._
2. In `<picture>`, the priority attribute goes on the internal `<img>` tag, never on `<source>`. _Exclusion: never depend on `<source>` to signal priority._
3. Prioritize vital scripts over heavy analytics tools via `fetchpriority`. Emit `Link: <url>; rel=preload; as=image; fetchpriority=high` in the server HTTP header for the LCP resource whenever possible. _Exclusion: never let analytics scripts compete for priority with critical interactivity scripts._
4. `fetchpriority` requires no feature-detection — it degrades gracefully as native progressive enhancement. _Exclusion: never wrap `fetchpriority` in a conditional support check._
5. Replace legacy `<link rel="prefetch">` with Speculation Rules API for predictive navigation. _Exclusion: never use legacy prefetch as the primary mechanism in new projects, and explicitly exclude routes that mutate state (`/logout`) via `"not": {"href_matches": ...}`._
6. Calibrate speculation rules `eagerness` surgically: `conservative` for low-confidence links, `moderate` (~340ms hover) for general navigation, `eager` only for linear flows (checkout). _Exclusion: never use `eager` on high-fanout lists._
7. Never use `transition: all`. _Exclusion: strict restriction. Declare explicit properties, restricting animations/transitions to `transform` and `opacity`._
8. `will-change` applied only temporarily and removed via JS after use. _Exclusion: never leave `will-change` declared permanently in static CSS._
9. `contain: layout` on widgets whose internal mutations must be isolated from the external flow; `contain: paint` when there is internal overflow/scroll; `contain: strict` as a shorthand for layout+paint on fully independent blocks. _Exclusion: never leave dynamic panels (LLM-driven) without layout isolation when they mutate frequently._
10. `content-visibility: auto` always accompanied by a corresponding `contain-intrinsic-size`. Prefer it over `display: none` to defer long content outside the viewport. _Exclusion: never apply without intrinsic-size (risk of scrollbar jumping) and never use `display: none` as a lazy-render technique when `content-visibility: auto` preserves native search indexing and keyboard focus._
11. `scheduler.yield()` to break up any function exceeding ~50ms on the main thread (a Long Task). _Exclusion: never block the main thread beyond 50ms without yielding control back to the scheduler._
12. Prefer `scheduler.yield()` over `setTimeout(..., 0)` to break up Long Tasks, with feature-detection fallback (`globalThis.scheduler?.yield`). _Exclusion: never rely on `setTimeout(..., 0)` as the primary yielding mechanism — it loses priority inheritance and risks being pre-empted by third-party tasks._
13. Schedule analytics/tracking calls (e.g., `dataLayer.push()`) via `requestAnimationFrame` + `setTimeout` after paint. _Exclusion: never execute third-party tracking calls synchronously inside a click/input handler that blocks the visual response._
14. Delegate non-essential third-party scripts (analytics, support widgets, ad pixels) to a Web Worker via Partytown. _Exclusion: never run non-essential third-party scripts on the main thread when worker delegation is available._
15. Systematic Bundle Splitting and Tree Shaking across the build. _Exclusion: never ship a monolithic, unsplit JS bundle when the build tool supports splitting._
16. Import on Visibility for non-critical, below-the-fold components. _Exclusion: never eagerly import a heavy component that is only needed once visible or interacted with._

### 2. System Design: Architecture, Streaming, RSC & Islands
17. Default to Vertical Microfrontends (route-level split, e.g. `/docs`, `/dashboard`) over Horizontal (runtime Module Federation). _Exclusion: never default to horizontal/runtime composition — reserve it strictly for cases where a visual fragment must update without redeploying the host application._
18. Route microfrontends at the proxy/edge layer, not via client-side middleware. _Exclusion: never use traditional middleware routing for microfrontend composition when edge/proxy routing is available — it carries materially higher latency (~25% in production benchmarks)._
19. Isolate JS bundles strictly by execution domain/context. _Exclusion: never let one domain's bundle (e.g., documentation) intersect another unrelated domain's (e.g., billing)._
20. Prefer SSG/Jamstack with CDN distribution for predominantly static content. _Exclusion: never use SSR with full hydration when content can be pre-rendered statically._
21. Rendering-strategy preference order: **(1)** Resumability (Qwik) or Islands Architecture (Astro) when stack choice is open — they eliminate or minimize hydration cost entirely; **(2)** RSC/Streaming (Next.js App Router) when the React ecosystem is a project requirement; **(3)** classic SSR with full hydration only as a fallback when neither option above is available. _Exclusion: never default to full-tree hydration when a lower-cost paradigm is available in the chosen stack; never treat any single framework as the project default._

> **Scope note:** items 22–25 are tactical implementation detail for branch (2) above — React Server Components / Next.js App Router. Item 26 is tactical implementation detail for branch (1) — Astro-style Islands Architecture. Neither block is a universal default; apply only the branch that matches the project's actual stack.

22. Serve the Static Shell (nav, footer, layout) immediately, using `<Suspense fallback>` for data-dependent regions. _Exclusion: never block the entire response waiting for the slowest query — stream incrementally._
23. `'use client'` declared at the exact boundary of the interactive component. _Exclusion: never mark static components as client by default._
24. Server Actions (`useActionState`, `useFormStatus`) for submissions that update the UI progressively. _Exclusion: never use traditional full-page form POSTs when Server Actions are available in the stack._
25. In UI dynamically generated via streaming (e.g., `streamUI`), always `yield` a loading component before the resolved component's `return`. _Exclusion: never return a resolved UI component without a preceding loading state._
26. Islands Architecture: zero-JS by default, marking only genuinely interactive sections as islands. _Exclusion: never hydrate the entire page when only an isolated widget needs interactivity, and never let a script failure in one island propagate to another._
27. In an environment with React Server Components, adopt a Zero-Runtime styling engine (StyleX, Pigment CSS, Panda CSS, Tokenami). _Exclusion: never use legacy runtime CSS-in-JS (Emotion, Styled-Components) in component trees utilizing Server Components._
28. Control structural component variants through a typed "recipes" API (e.g., `cva`-style) provided by the Zero-Runtime engine. _Exclusion: never control variants via untyped conditional class-string concatenation when the engine offers a typed recipes/variants API._

### 3. Security: DOM XSS Prevention
29. Trusted Types via CSP (`require-trusted-types-for 'script'`) on any application that dynamically manipulates `innerHTML`/`outerHTML`. _Exclusion: never inject unsanitized strings directly into `innerHTML`/`outerHTML`/`eval()` in production without this policy enforced._
30. Centralized sanitization policy (e.g., DOMPurify + `RETURN_TRUSTED_TYPE`) as the single DOM-insertion gate. _Exclusion: never rely on ad-hoc sanitization scattered across the codebase when a Trusted Types policy can be the single gate._
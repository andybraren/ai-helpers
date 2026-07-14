---
name: uxd-create-design-spec
description: >-
  Create a structured design spec from a problem statement, research findings,
  or heuristic evaluation. Use when mapping UI to PatternFly components,
  documenting states and accessibility, or preparing a handoff before
  prototyping or engineering.
---

# Create Design Spec

Translate a problem statement and optional research into a design spec that engineering (or `uxd-prototype-create`) can build from. Every UI element maps to PatternFly components, states are explicit, and decisions trace back to evidence.

Works standalone. Pairs with `uxd-draft-acceptance-criteria` downstream and with `uxd-research-heuristic-eval` / research briefs upstream when available.

## Inputs

At least **one** of the first four is required. Zero inputs → **blocked**.

| Input | Required | Notes |
|-------|----------|-------|
| Problem statement / ticket description | Often | PM brief, Jira description, or feature ask |
| Research findings brief | Optional | Structured UXR findings for design consumption |
| Evaluation findings | Optional | Heuristic eval / expert review violation list |
| Visual reference | Optional | Screenshots, Figma context (`uxd-figma-read`), or live URL |
| Product / codebase context | Optional | Target product patterns, stack, repo path |
| Visual context profile | Optional | Computed surface colors / theme from a live app when available |
| Mode | No | `interactive` (default) or `pipeline` |

### Evaluation findings

When a heuristic evaluation or expert review is provided, treat it as first-class input (not "degraded" mode). Expect violations with ID, location, observation, severity, and optional heuristic reference.

1. Group by screen/location.
2. Decide: new surface, modify existing, or behavioral change.
3. Map to PatternFly components that resolve the issue.
4. Carry violation IDs into Research Traceability.
5. If `visual_inspection_needed` is set, note that the decision is text-only and visual verification is recommended.

## Process

### 1. Assess scope and build strategy

Determine product area, primary user tasks, and in/out of scope. Choose a build strategy:

| Signal | Strategy |
|--------|----------|
| Editable source with components | `modify-source` |
| Built/bundled app, live URL, or production UI to preserve | `dom-injection` |
| No existing UI | `greenfield` |

For `dom-injection`, document **injection targets** (DOM selectors) and **preserved elements**. Describe only new surfaces — the existing app is the layout.

### 2. Classify findings (when research or evaluation is present)

Classify each finding before designing:

- **Design problem** — blocks or degrades a user task → drives the spec
- **UI observation** — documents what exists, no user problem → context only
- **Improvement opportunity** — works but could be better → include if severity is Major+

If zero findings classify as design problems:

- Interactive: stop, show the classification table, ask what should improve
- Pipeline: blocked — cannot determine what to change

Add a Findings Classification table to the spec (see [references/spec-template.md](references/spec-template.md)).

### 3. Detect existing features

Before proposing new surfaces, check whether the target already has the feature.

- **modify-source:** Scan `package.json` and `src/` for related packages/components; read README.
- **dom-injection:** Scan bundles/CSS for related patterns; capture native visual design to match.
- **Interactive (when browser automation is available):** Click the trigger, screenshot before/after, classify as functional / partial / non-functional.

If the feature is already **functional**, prefer discoverability improvements over rebuilding a duplicate. For `dom-injection`, do not rely on programmatically triggering framework-internal state at runtime — design complementary surfaces instead.

Document findings in an Existing Features section. Details: [references/existing-features.md](references/existing-features.md).

### 4. Apply AI design language when relevant

If the feature involves AI (chatbot, assistant, generation UI), apply `pf-ai-guide`. Document which requirements apply in an "AI Design Language Compliance" section when needed. If `pf-ai-guide` is unavailable, note that and continue.

### 5. Map to PatternFly and validate tokens

Prefer computed visual context (live app profile) over visual impression when choosing theme/on-dark tokens and matching sibling styles.

For each UI element:

1. Look up the PatternFly component via PatternFly MCP / docs.
2. Confirm it exists in PF6 and is not deprecated.
3. Document variant/props and whether the product already uses it (reuse).
4. Validate every token name against PatternFly docs/MCP. Prefer semantic tokens. Flag gaps; never invent hex/spacing as if they were tokens.

If MCP/docs are unavailable, mark tokens `unverified` and continue in a degraded state.

### 6. Document interactions, a11y, and traceability

For each interaction: default, hover/active/focus/loading, error + recovery, empty, responsive breakpoints (576 / 768 / 992 / 1200 / 1450).

Per interaction: keyboard path, screen reader announcements, ARIA, focus management, contrast (4.5:1 normal / 3:1 large).

Trace each major decision to research finding, evaluation violation ID, problem constraint, PF guideline, or explicit **Designer judgment**.

### 7. Compile the spec

Assemble using [references/spec-template.md](references/spec-template.md). In `pipeline` mode, append the YAML summary from that file.

## Guardrails

- **Design Intent gate:** "What changes" must describe improvement/extension, not reproduction of the existing UI. Reproduction → blocked.
- Always assess build strategy before drafting layout.
- For `dom-injection`, describe only injected surfaces.
- Detect existing features before proposing replacements.
- Verify component mappings against current PatternFly docs.
- Every decision needs a traceability source (or explicit designer judgment).
- Use PatternFly tokens — no hardcoded hex, px, or ad-hoc spacing presented as final.
- Do not propose custom components without documenting why no PF component fits.
- Missing states → open questions, not invented behavior.
- Respect the 8px grid; minimum 14px body text.

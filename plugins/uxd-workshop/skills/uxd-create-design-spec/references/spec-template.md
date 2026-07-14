# Design Spec Output Template

```markdown
# Design Spec: [Feature/Area Name]

## Metadata
- **Ticket:** [ref or "none"]
- **Status:** [STANDARD | DEGRADED]
- **Date:** [generated date]
- **Spec mode:** [create | revise]

## Findings Classification
| Finding | Category | Drives Spec? | Rationale |
|---------|----------|--------------|-----------|
| V-01: … | Design problem | Yes | User task blocked |
| V-02: … | UI observation | No (context only) | Structural, no user impact |

## Problem
[1-2 sentence summary from problem statement]

## Design Intent
- **What changes:** [1-3 sentences: new surfaces, behaviors, or improvements]
- **What stays:** [existing UI elements preserved as-is]
- **Design problems addressed:** [finding IDs or "problem statement"]

## Scope
- **In scope:** [list]
- **Out of scope:** [list]

## Build Strategy
- **Approach:** [greenfield | modify-source | dom-injection]
- **Target:** [URL, repo path, or "none"]
- **Theme:** [light | dark | mixed — prefer computed visual context]
- **Visual context:** [available | not available]
- **Injection targets:** [DOM selectors, or "N/A"]
- **Preserved elements:** [what must not change, or "N/A"]

## Existing Features
- **Feature detected:** [name or "none"]
- **Detection method:** [package scan / CSS scan / interactive test / N/A]
- **Interactive test result:** [functional | partial | non-functional | not-tested]
- **Current state:** [brief]
- **Implementation strategy:** [extend / discoverability / custom match / N/A]

## Layout

### [Section Name]
- **PF Component:** [component] ([variant])
- **Purpose:** [what this does for the user]
- **States:** default, [list]
- **Responsive:** [breakpoint behavior]

## Component Mapping

| UI Element | PF Component | Variant/Props | Reuse? | Notes |
|------------|--------------|---------------|--------|-------|
| [element] | [component] | [variant] | existing / new | [notes] |

## Interaction Patterns

### [Pattern Name]
- **Trigger:** [user action]
- **Behavior:** [what happens]
- **States:** [transitions]
- **Error handling:** [failure + recovery]
- **A11y:** keyboard path, ARIA, screen reader announcement

## Accessibility Requirements

| Interaction | Keyboard | Screen Reader | ARIA | Contrast |
|-------------|----------|---------------|------|----------|
| [interaction] | [path] | [announcement] | [attrs] | [req] |

## Design Tokens

| Property | Token | Value | Validated | Notes |
|----------|-------|-------|-----------|-------|
| [property] | [PF token] | [resolved] | yes / unverified / gap | [context] |

## Research Traceability

| Decision | Source | Evidence | Rating |
|----------|--------|----------|--------|
| [decision] | [finding / V-XX / constraint / judgment] | [summary] | strong / moderate / weak / judgment |

## Non-claims
[What was NOT checked or verified]

## Open Questions
[Unresolved decisions needing designer input]
```

## Pipeline mode summary

When `mode` is `pipeline`, append:

```yaml
spec_summary:
  status: STANDARD | DEGRADED
  input_types: [evaluation_findings, problem_statement, …]
  component_count: [N]
  new_components: [N]
  reused_components: [N]
  interaction_count: [N]
  a11y_requirements_count: [N]
  token_count: [N]
  tokens_validated: [N]
  tokens_unverified: [N]
  open_questions_count: [N]
  degraded_decisions: [N]
```

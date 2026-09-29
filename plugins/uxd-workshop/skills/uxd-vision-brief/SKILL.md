---
name: uxd-vision-brief
version: 0.1.0
description: >-
  Create a structured UX vision brief covering the problem, target user, new
  capabilities, scope, and stakeholders. Use when starting vision work, scoping
  a near-term experience, or preparing a vision narrative.
audience: "UX designers"
inputs: "Product area or problem, optional research, optional target codebase"
outputs: "A structured vision brief in markdown"
---

# Vision Brief

Produces the framing document for a near-term UX vision: one user journey, 6–12 months out, shown later as a narrative and a prototype. This skill does not design the screens or build the prototype.

Work one section at a time. Confirm what you heard before moving on. Push vague answers toward a specific user, a specific pain, and one journey.

## Inputs

| Input | Required | Source |
|-------|----------|--------|
| Product area or problem | **Yes** | User. Ask if omitted. |
| Evidence (research, tickets, analytics, observation) | Recommended | User, or a research-lookup skill if one is available |
| Target codebase | No | User-provided path or repo. Skip integration notes when none is given. |

## Outputs

Write `vision-brief.md`. When a ticket or work item id is known, write `.artifacts/{ID}/vision-brief.md` in the working project. Do not write into this skill's directory.

## Arguments

$ARGUMENTS

Parse as: `<product-area-or-problem> [--workspace <path>] [--id <work-item-id>]`

| Flag | Default | Description |
|------|---------|-------------|
| `--workspace` | none | Codebase the vision may be prototyped in. Used only to discover that repo's own conventions. |
| `--id` | none | Work item id for the artifact path. |

---

## Step 1: Product area

Ask what area this vision is for and why now. Summarize in 2–3 sentences and confirm before continuing.

## Step 2: Existing research

Before defining the pain, look for what the team already knows.

If a research-lookup skill is available, use it for the product area and target user. Capture quotes, findings, study method, sample size, date, and links. If it is unavailable or returns nothing, say so and continue.

Label every claim as **evidence** or **assumption**. Do not block the brief when evidence is thin.

## Step 3: Current pain

Ask who the target user is, what they are trying to do, what is painful today, and what evidence supports that. Use retrieved research as the primary source when it exists.

Reject generic pain. "Users find it confusing" is not enough. A specific role, a concrete workflow, and a measurable friction is.

## Step 4: New capabilities

Ask which capabilities, technologies, or investments could change the experience, and whether each is committed, being explored, or aspirational.

Translate abstractions into user-facing behavior. "Add AI" is not a capability. "Show the three most likely causes, with the evidence each one is based on" is.

## Step 5: Scope

Draw the boundary:

- Time horizon, defaulting to 6–12 months unless the user sets another
- **One** primary journey
- What is explicitly out of scope

If the scope is a whole product, ask which single scenario would make a stakeholder say "build that."

## Step 6: Stakeholders

Ask who needs to see the vision, what each of them cares about, and whether a specific meeting or review is coming up. Note dynamics that should shape the story. Do not invent stakeholder names.

## Step 7: Target codebase

Run this step only when the user provides a workspace.

Discover from that repo — do not assume a layout, design system, ticket prefix, or flag file:

- Where this experience would live (existing area, new area, or unknown)
- How the repo names branches, feature flags, or scenario toggles, if it uses them
- Any design history or decision log for this area

Record only what you found. If a convention is absent, write "not used" rather than proposing one from another product.

## Step 8: Write the brief

```markdown
# Vision Brief: [Product area]

## Problem Statement
[2–3 sentences. Ground in evidence. Mark assumptions.]

## Target User
- **Role:**
- **Context:**
- **Goal:**
- **Current experience:**

## Evidence
- **Research lookup:** [Used / Not available / No results]
- [Finding, with source]
- [Assumption, labeled as an assumption]

## New Capabilities
- **[Name]:** [What the user can do]

## Capability Readiness
- [ ] Committed
- [ ] Being explored
- [ ] Aspirational

## Scope
- **Time horizon:**
- **Primary journey:**
- **Out of scope:**

## Prototype Target
- **Workspace:** [Path, or "not chosen"]
- **Placement:** [Discovered from the workspace, or "n/a"]
- **Branch / flag convention:** [The repo's own convention, or "n/a"]
- **Prior decisions reviewed:** [What was read, or "none found"]

## Stakeholders
| Who | What they care about |
|-----|----------------------|

## Presentation Context
[Where and when this will be shared]
```

Read the brief back. Revise until the user confirms the scope is one journey and the pain is specific.

## Quality checks

- Problem statement separates evidence from assumption
- Target user is a role in a context, not "users"
- Capabilities are user-facing behaviors
- Scope is one journey
- At least one stakeholder is named by role, with what they care about
- No product paths, ports, flag names, or branch prefixes were invented

When the user accepts the brief, the next skill is `uxd-vision-narrative`.

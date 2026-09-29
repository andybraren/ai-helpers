---
name: uxd-vision-review
version: 0.1.0
description: >-
  Score a UX vision prototype for narrative clarity, problem grounding,
  capability demonstration, and stakeholder readiness. Use when reviewing a
  vision prototype or preparing a stakeholder demo.
audience: "UX designers"
inputs: "Vision brief, vision narrative, and a prototype to review"
outputs: "A review scorecard, improvement list, and presentation plan"
---

# Vision Review

Judges whether a vision prototype tells a credible near-term story and helps the designer prepare to show it. This is not a heuristic audit, an acceptance-criteria check, or a usability study.

## Inputs

| Input | Required | Source |
|-------|----------|--------|
| Vision brief | **Yes** | `vision-brief.md` or `.artifacts/{ID}/vision-brief.md` |
| Vision narrative | **Yes** | `vision-narrative.md` beside the brief |
| Prototype | **Yes** | Path, URL, or running app the user points to |

If the brief or narrative is missing, stop and name the skill that should produce it (`uxd-vision-brief`, `uxd-vision-narrative`). If no prototype is available, stop and ask where it lives. Do not search a default repository.

## Outputs

Write `vision-review.md` beside the other vision artifacts.

## Arguments

$ARGUMENTS

Parse as: `<prototype-path-or-url> [--id <work-item-id>]`

---

## Step 1: See the prototype

Read the brief, the narrative, and the prototype source or running UI.

When a server is already running, or the project documents how to start one, use that. If the prototype gates the vision behind a flag, scenario, or query parameter, enable it the way that project does. Do not assume a package script, port, or flag file.

## Step 2: Scorecard

Rate each dimension **Strong**, **Adequate**, or **Needs work**, with a short assessment tied to something you actually saw.

1. **Narrative clarity** — Can someone outside the work follow the story in a few minutes? Is the problem immediate, and does the before/after contrast land?
2. **Problem grounding** — Is the pain evidenced in the brief, specific enough to be credible, and recognizable to a product or engineering partner?
3. **Capability demonstration** — Is there a moment where the person experiences the new capability, from their point of view, not as a feature label?
4. **Emotional impact** — Does the before feel costly, and does the after create a reason to build it?
5. **Feasibility signal** — Is this plausible in the brief's time horizon, without capabilities the narrative treats as magic? Could an engineer see a path?
6. **Visual credibility** — Does it look like the product it is supposed to extend? Realistic data, not placeholder copy. Judge against the design system that project uses. When that system is PatternFly, check that components, spacing, and theming match neighboring screens. When it is not, do not apply PatternFly rules.

## Step 3: Improvements

Sort changes into **Must fix**, **Should fix**, and **Nice to have**. Each item names the screen and the change. "Make it better" is not an item. "Replace the generic alert on screen 3 with the incident summary from beat 2" is.

## Step 4: Presentation plan

Draft with the designer:

- Opening line that frames the problem before the solution
- Click path
- Where to pause
- Closing line
- One- or two-sentence answers for: when could this be built, how it fits current work, what users have said (or that it has not been tested), what would be cut, and what is simulated versus real
- Who is in the room, how long, and whether they should drive or watch

## Step 5: Write the review

```markdown
# Vision Review: [Product area]

## Scorecard Summary

| Dimension | Rating |
|-----------|--------|
| Narrative clarity | |
| Problem grounding | |
| Capability demonstration | |
| Emotional impact | |
| Feasibility signal | |
| Visual credibility | |

## Detailed Assessments
[One short assessment per dimension]

## Improvements

### Must fix
### Should fix
### Nice to have

## Presentation Plan

### Demo script
### Prepared answers
### Context

## Decisions
[What this vision explored, the scorecard in brief, feedback, and next step. Duplicate this into the project's design log only when that project already keeps one.]
```

## Step 6: Close

Ask whether the designer has walked the prototype once without stopping, whether anyone else has seen it, and whether they can explain both the story and a path to building it.

If prototype code changed during the review, run the lint and build commands that repo documents. Skip this when the repo has none, or when nothing was changed. Do not impose a toolchain from another project.

## Quality checks

- All six dimensions are rated from the artifacts, not from the pitch
- Improvements name a screen and a change
- The demo script has an opening, a path, and a close
- At least three likely questions have answers
- The review does not assume a product, port, flag filename, or design-system rule the target project does not use

For acceptance criteria, usability, or a design-system critique, use `uxd-prototype-evaluate` or `uxd-evaluate-design-heuristics`. This skill stays on the vision story and the stakeholder conversation.

---
name: uxd-vision-narrative
version: 0.1.0
description: >-
  Turn a vision brief into a scene-by-scene user journey a prototype can show.
  Use when writing a vision story, defining before-and-after beats, or listing
  the screens a vision prototype needs.
audience: "UX designers"
inputs: "A vision brief, optional persona cards, optional target codebase"
outputs: "A vision narrative with a screen breakdown"
---

# Vision Narrative

Turns a vision brief into the story a prototype will act out. This skill does not build the prototype.

## Inputs

| Input | Required | Source |
|-------|----------|--------|
| Vision brief | **Yes** | `vision-brief.md`, `.artifacts/{ID}/vision-brief.md`, or user-provided text |
| Persona reference | No | Persona cards in the target project or an installed plugin, when they match the brief |
| Target codebase | No | Only to learn real navigation. Skip routes when no codebase is available. |

If no brief exists, stop and ask the user to run `uxd-vision-brief` or paste a brief.

## Outputs

Write `vision-narrative.md` beside the brief (`.artifacts/{ID}/vision-narrative.md` when an id is known).

## Arguments

$ARGUMENTS

Parse as: `[path-to-brief] [--workspace <path>]`

---

## Step 1: Set the scene

Establish who, when, and what is at stake.

Give the user a name and a concrete role. If persona cards are available and one fits the brief, use it and say which one. If none fits, invent a specific person and label them as synthetic. Do not require a particular persona file or directory.

Write a 2–3 sentence scene-setter. Example of the level of specificity, not a required domain:

> It's Tuesday morning. Priya, a platform engineer, opens her laptop to 47 unread alerts. Three tools each show part of what might be the same incident. She has 15 minutes before standup.

## Step 2: Today (before)

Write 3–5 beats of the current experience. Each beat has:

- What the user does
- What the product does, or fails to do
- How it feels
- Research source, when the beat comes from the brief's evidence

Ask the user whether each beat matches what people actually do today. Prefer quotes and findings from the brief over invented pain.

## Step 3: The pivot

Write the moment a new capability changes the outcome. It must be a specific action with a specific result, meaningfully better than today, and credible for the brief's time horizon. Not magic, and not "the AI helps."

## Step 4: Tomorrow (after)

Write 3–5 beats for the same person and scenario with the new capabilities. Mirror the before beats so the contrast is obvious.

Each beat: what the user does, what the product does, and what that enables. Name the objects on screen. "A single incident view with a confidence score and the evidence behind the suggested cause" is a beat. "A smarter dashboard" is not.

## Step 5: Payoff

Close on the value. What can this person do with the time or effort they got back, and what would they tell a colleague?

## Step 6: Screens

List the 3–5 views the prototype must show. For each:

- Screen name
- Placement in the product: existing page, new view in an existing area, or new area
- Which narrative beat it carries
- What must be visible
- What the user does

Include a route only when you have read the target app's navigation and the route is real or follows that app's routing pattern. Do not invent paths from another product.

## Step 7: Write the narrative

```markdown
# Vision Narrative: [Product area]

## The Setup
[Scene-setter]

## Today: [Name]'s Current Experience
### Beat 1: [Action]
[What they do, what happens, how it feels. Cite research when used.]

## The Pivot
[Turning point]

## Tomorrow: [Name]'s New Experience
### Beat 1: [Action]
[What they do, what happens, what it enables]

## The Payoff
[Value realized]

## Screen Breakdown

| # | Screen | Placement | Narrative moment | Key elements | User action |
|---|--------|-----------|------------------|--------------|-------------|
```

Read it back. Revise until the user agrees the before is true, the after is credible for the time horizon, and a stakeholder could follow the story without having been in the room.

## Quality checks

- The person has a name, a role, and a stake
- Before beats trace to evidence in the brief, or are labeled as assumptions
- After beats are concrete interactions
- Capabilities show up as things the person does, not as a technology list
- The screen list is enough to prototype, without product-specific paths that were not discovered from the target codebase
- Someone unfamiliar with the product can follow the story

When the user accepts the narrative, the next skill is `uxd-prototype-create`, with this narrative as the source. Pass the same workspace when one was chosen. Do not build the prototype in this skill.

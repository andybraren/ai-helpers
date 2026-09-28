---
name: vision-narrative
description: >-
  Help a designer craft a user journey narrative for a UX vision. Turns a vision
  brief into a concrete, scene-by-scene story showing how a user's experience
  transforms with new capabilities. Use when asked to write a vision story,
  create a narrative, or "vision-narrative".
disable-model-invocation: true
---

# Vision Narrative

Guide the designer through writing the story that the vision prototype will bring to life. This is Phase 2 of the UX Vision Playbook.

## Prerequisites

Read the vision brief first. Look for a file matching `*vision-brief*` or `*brief*` in the project. If none exists, tell the designer to run `/vision-brief` first.

## Process

### Step 1: Set the Scene

Work with the designer to establish:
- **Who:** Give the user a name and a concrete role. Check `.design/` in the rhoai-3.6 repo for existing personas the team already uses. Use one if it fits the vision's target user. If you need a new persona, document why the existing ones don't cover this scenario. Use a name from actual research if available.
- **When:** What time of day, what day of the week, what's happening in their work context?
- **What's at stake:** Why does this moment matter? What's the consequence of the current painful experience?

Write a 2-3 sentence scene-setter. Example:

> *It's Tuesday morning. Priya, a platform engineer at a mid-size fintech company, opens her laptop to 47 unread alerts from overnight. Three separate dashboards show fragments of what might be the same incident. She has 15 minutes before the morning standup where she'll need to explain what happened and whether it's resolved.*

### Step 2: Show the Current Pain (Before)

Write 3-5 narrative beats showing the user's current experience. Each beat should be a concrete action with a concrete frustration.

If the vision brief includes research findings from `uxd-research-insights`, use them as source material for these beats. Participant quotes from past studies make the "Before" section sharper and more credible. For example, if research found "I need to see eval results side-by-side with the prompt I used — switching tabs kills my flow," that quote can become a narrative beat almost directly.

Format each beat as:
- **What the user does** (specific action)
- **What happens** (the system response or lack thereof)
- **How it feels** (the friction, the wasted time, the frustration)
- **Research source** (optional — cite the study if this beat comes from documented research)

Ask the designer to validate each beat: "Is this accurate to what users actually experience today?"

### Step 3: The Pivot Moment

Write the transition — the moment where the new capability changes everything. This should feel like a turning point in the story.

The pivot should be:
- **Concrete:** The user does something specific and gets a specific, different result
- **Surprising:** The outcome is meaningfully better than what they expected based on current experience
- **Credible:** It's grounded in a real capability, not magic

### Step 4: Show the Transformed Experience (After)

Write 3-5 narrative beats showing the same user, same scenario, but with the new capabilities in place. Mirror the structure of the "before" beats so the contrast is visceral.

For each beat:
- **What the user does** (how the action changes or simplifies)
- **What happens** (the new system response)
- **What this enables** (what the user can now do that they couldn't before)

Push the designer to be specific about the interaction. "The AI helps" is not a narrative beat. "Priya sees a single unified incident view with a confidence score and a suggested root cause pulled from three similar incidents in the last 90 days" is.

### Step 5: The Payoff

End the narrative with a moment that captures the value. What can this user now do with the time/effort they saved? How does their role or capability change? What would they tell a colleague about this experience?

### Step 6: Identify the Key Screens

Based on the narrative, identify the 3-5 specific screens or views the prototype needs to show. For each screen:
- **Screen name:** What it is
- **Route:** Where it lives in the rhoai-3.6 navigation (e.g., `/ai-hub/agents/builder`). Is it a new page under an existing nav section? A new tab on an existing page? A new top-level nav item?
- **Narrative moment:** Which beat(s) it corresponds to
- **Key elements:** What must be visible on this screen to tell the story
- **Interaction:** What the user does here (click, scan, react)

This becomes the spec for Phase 3 (prototyping).

### Step 7: Compile the Narrative Document

Write the complete narrative to a file. Use this structure:

```markdown
# Vision Narrative: [Product Area]

## The Setup
[Scene-setter paragraph]

## Today: [User Name]'s Current Experience
### Beat 1: [Action]
[Narrative]

### Beat 2: [Action]
[Narrative]

### Beat 3: [Action]
[Narrative]

## The Pivot
[Transition moment]

## Tomorrow: [User Name]'s New Experience
### Beat 1: [Action]
[Narrative]

### Beat 2: [Action]
[Narrative]

### Beat 3: [Action]
[Narrative]

## The Payoff
[Closing moment — the value realized]

---

## Screen Breakdown

| # | Screen | Route | Narrative Moment | Key Elements | User Action |
|---|--------|-------|-----------------|--------------|-------------|
| 1 | [Name] | [e.g., /ai-hub/agents/builder] | [Beat reference] | [What's on screen] | [What user does] |
| 2 | [Name] | [e.g., /ai-hub/agents/builder/config] | [Beat reference] | [What's on screen] | [What user does] |
| 3 | [Name] | [e.g., /ai-hub/agents/detail] | [Beat reference] | [What's on screen] | [What user does] |
```

### Step 8: Review

Read the narrative back and ask:
- Does this feel true to what users actually experience today?
- Is the "after" experience credible for the 6-12 month time horizon?
- Would this story make a stakeholder lean forward and say "build that"?
- Is there a clear emotional arc — frustration to relief to excitement?

## Quality Checks

Before finishing, verify:
- [ ] The user has a name and a specific role/context
- [ ] The "before" beats are grounded in real, evidence-based pain points
- [ ] The "after" beats describe concrete interactions, not abstract improvements
- [ ] The new capabilities are shown through the user's experience, not described in technical terms
- [ ] The screen breakdown provides enough detail for prototyping
- [ ] Someone unfamiliar with the product could follow the story

---
name: vision-review
description: >-
  Evaluate a UX vision prototype against quality criteria: narrative clarity,
  prototype fidelity, strategic alignment, and stakeholder readiness. Produces a
  review scorecard and improvement plan. Use when asked to review a vision,
  evaluate a prototype, or "vision-review".
disable-model-invocation: true
---

# Vision Review

Evaluate the vision prototype and help the designer prepare for stakeholder presentation. This is Phase 4 of the UX Vision Playbook.

## Prerequisites

Read all project artifacts before starting:
- The vision brief (`*vision-brief*`)
- The vision narrative (`*vision-narrative*`)
- The prototype source code (look in the rhoai-3.6 feature area directory for the vision's React/PatternFly components)

If possible, run the prototype (`npm run start:dev` in the rhoai-3.6 directory — dev server at localhost:9000) and take screenshots or review the rendered pages using a browser tool. Make sure the vision's feature flag is enabled in the prototype bar.

## Process

### Step 1: Review Against Criteria

Evaluate the vision across six dimensions. For each, assign a rating and write a brief assessment.

**Use this scorecard:**

```markdown
# Vision Review Scorecard

## 1. Narrative Clarity
**Rating:** [Strong / Adequate / Needs Work]

Can someone who wasn't involved understand the story in under 3 minutes?

- Is the user's problem immediately clear?
- Does the before/after contrast land?
- Is there a clear emotional arc?
- Assessment: [Your assessment]

## 2. Problem Grounding
**Rating:** [Strong / Adequate / Needs Work]

Is the pain point real and evidence-based?

- Does the brief cite specific evidence (research, data, tickets)?
- Would a PM or eng lead recognize this problem?
- Is the scope specific enough to be credible?
- Assessment: [Your assessment]

## 3. Capability Demonstration
**Rating:** [Strong / Adequate / Needs Work]

Does the prototype show HOW the new capability works, not just THAT it exists?

- Is there an interactive moment where the user experiences the capability?
- Is the capability shown through the user's lens (not technical)?
- Would a stakeholder understand what's different from today?
- Assessment: [Your assessment]

## 4. Emotional Impact
**Rating:** [Strong / Adequate / Needs Work]

Does the vision create conviction?

- Does the "before" make you feel the pain?
- Does the "after" make you want to build this?
- Would a stakeholder show this to their peers?
- Assessment: [Your assessment]

## 5. Feasibility Signal
**Rating:** [Strong / Adequate / Needs Work]

Is this plausibly achievable in the stated time horizon?

- Are the capabilities realistic for 6-12 months?
- Does it avoid requiring capabilities that don't exist yet?
- Could an engineer watch this and see a path to building it?
- Assessment: [Your assessment]

## 6. Visual Credibility
**Rating:** [Strong / Adequate / Needs Work]

Does it look and feel like the actual product?

- Does it use PatternFly components consistently?
- Is the data realistic (not lorem ipsum or placeholder)?
- Does the layout match the product's conventions?
- Would a stakeholder who uses the product daily find it believable?
- Does it respect the dark mode toggle (ThemeContext)?
- Are PF components used without custom CSS overrides?
- Does the page structure match existing rhoai-3.6 patterns (PageSection, Toolbar, composable Table)?
- Are imports using standard patterns (`@patternfly/react-core`, not deep imports)?
- Does mock data follow the `src/mockData/` conventions (typed arrays, exported constants)?
- Assessment: [Your assessment]
```

### Step 2: Identify Improvements

Based on the scorecard, create a prioritized list of improvements.

Categorize as:
- **Must fix** — Issues that would undermine the vision's impact
- **Should fix** — Issues that weaken the vision but don't break it
- **Nice to have** — Polish items if time allows

For each improvement, be specific about what to change and why. "Make it better" is not an improvement item. "Replace the generic alert text on screen 3 with a specific incident summary that matches the narrative's root cause scenario" is.

### Step 3: Prepare for Stakeholder Presentation

Help the designer prepare for sharing the vision. Work through:

**Demo script:**
- What's the opening line? (Frame the problem before showing the solution)
- What's the click path through the prototype?
- Where should the designer pause and let the stakeholder react?
- What's the closing message?

**Anticipated questions and answers:**

Stakeholders will typically ask:
1. "When can we build this?" — Have a honest answer about feasibility and what it would take
2. "How does this fit with [current initiative]?" — Connect the vision to existing priorities
3. "What did users think?" — Note if user validation has been done; if not, suggest it as a next step
4. "What would we need to cut to do this?" — Have an opinion on scope and tradeoffs
5. "Is the AI part real?" — Be clear about what's simulated vs. what exists today

Help the designer draft 1-2 sentence answers for each.

**Presentation context:**
- Who's in the room?
- How much time do they have?
- Should the stakeholder click through themselves or watch a demo?
- Is this a "get feedback" presentation or a "build conviction" presentation?

### Step 4: Write the Review Document

Compile everything into a review document and save it to the project:

```markdown
# Vision Review: [Product Area]

## Scorecard Summary

| Dimension | Rating |
|-----------|--------|
| Narrative Clarity | [Rating] |
| Problem Grounding | [Rating] |
| Capability Demonstration | [Rating] |
| Emotional Impact | [Rating] |
| Feasibility Signal | [Rating] |
| Visual Credibility | [Rating] |

## Detailed Assessments
[Full scorecard from Step 1]

## Improvements

### Must Fix
- [Item]

### Should Fix
- [Item]

### Nice to Have
- [Item]

## Presentation Plan

### Demo Script
[Opening → click path → pauses → closing]

### Prepared Answers
[Q&A pairs]

### Context
[Who, when, how long, format]
```

### Step 5: Post-Change Verification

Before any review session, verify the prototype builds cleanly:
1. Run `npx eslint` on all changed files in the rhoai-3.6 repo
2. Run `npm run build` to confirm no build errors
3. Fix any lint or build errors before the critique session

These checks are required by the rhoai-3.6 repo's agent rules and will catch issues that would distract reviewers from the vision itself.

### Step 6: Final Check

Ask the designer:
- Have you walked through the prototype yourself at least once without stopping?
- Has at least one other person (designer, PM, or eng) seen it before the stakeholder presentation?
- Do you feel confident explaining both the vision and the path to building it?

If the answer to any of these is no, help address that gap before wrapping up.

### Step 7: Update Design History

After the review is complete and feedback has been incorporated, update the design history at `.design/features/<area>/design-history.md` in the rhoai-3.6 repo. Add an entry documenting:
- What vision was explored and what it showed
- The review scorecard summary
- Stakeholder feedback and any decisions made
- Next steps (further iteration, roadmap inclusion, parked, etc.)

This keeps the team's design evolution traceable and prevents future designers from re-exploring rejected directions without context.

## Quality Checks

Before finishing, verify:
- [ ] All six dimensions are rated with specific assessments
- [ ] Improvement items are specific and actionable
- [ ] Demo script has a clear opening, path, and closing
- [ ] At least 3 anticipated questions have prepared answers
- [ ] The designer has a plan for who sees this and when
- [ ] `npx eslint` and `npm run build` pass cleanly on the rhoai-3.6 branch
- [ ] Design history has been updated with the vision work and its outcome

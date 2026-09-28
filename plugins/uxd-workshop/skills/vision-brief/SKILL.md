---
name: vision-brief
description: >-
  Guide a designer through defining a UX vision brief: problem space, target
  user, new capabilities, scope, and stakeholders. Produces a structured brief
  document that feeds into vision-narrative. Use when asked to start vision work,
  define a vision brief, scope a vision, or "vision-brief".
disable-model-invocation: true
---

# Vision Brief

Guide the designer through creating a structured vision brief. This is Phase 1 of the UX Vision Playbook.

## Process

Work through these sections interactively. Ask the designer questions, help them sharpen vague answers, and push for specificity. Use the AskQuestion tool when presenting choices.

### Step 1: Identify the Product Area

Ask the designer:
- What product area or feature domain is this vision for?
- Why this area? What's driving the need for vision work here?

Summarize what you hear back to confirm alignment before moving on.

### Step 1b: Map to the rhoai-3.6 Codebase

The vision will be built as new pages in the rhoai-3.6 prototype repo. Help the designer identify:
- **Feature area:** Which rhoai-3.6 directory does this map to? (`AIHub/`, `GenAIStudio/`, `DevelopTrain/`, `ObserveMonitor/`, `Settings/`, or a new top-level area)
- **Feature mapping:** Check `.design/feature-mapping.md` to see how code paths map to design areas.
- **Design history:** Read `.design/features/<area>/design-history.md` for the relevant area. Note any prior vision work, rejected directions, or existing commitments that should inform the scope. If no design history exists for this area, note that as well.
- **Branch name:** What branch will this work live on? Follow the convention `prototype/RHOAIUX-<ticket>-<short-description>` or `feature/vision-<area>`.
- **Feature flag name:** Every new vision page needs a toggle in `FeatureFlagsContext.tsx`. Propose a flag name (e.g., `showVisionAgentOps`).

### Step 2: Surface Existing Research

Before defining the pain, help the designer find what the team already knows. If `uxd-research-insights` is available (requires `gws` CLI + VPN), run it to retrieve past research findings about the product area and target user.

Suggested queries:
- "What do we know about [target user role] from our UX research?"
- "Pull findings about [product area] from the last 18 months"
- "Do we have any research on [the workflow or pain point being explored]?"

Capture the results: participant quotes, specific findings, study metadata (method, n, date), and deep links to slides. These become the "Evidence" section of the brief and feed directly into the narrative's "Before" beats.

If the skill is not available or returns no results, note that in the brief as a gap. The vision can proceed without research, but the brief should be transparent about which claims are evidence-based and which are assumptions.

### Step 3: Define the Current Pain

This is the foundation. The vision is only powerful in contrast with today's reality.

Ask the designer to describe:
- Who is the target user? (Role, context, what they're trying to accomplish)
- What is their current experience like? What's painful, slow, frustrating, or broken?
- What evidence exists for these pain points? (User research, support tickets, analytics, direct observation)

If research findings were retrieved in Step 2, use them as the primary source for this section. Pull specific quotes, data points, and participant counts into the pain description.

Push for specificity. "Users find it confusing" is not enough. "Cluster admins spend 40 minutes manually correlating alerts across three different dashboards to diagnose a single incident" is.

If the designer doesn't have evidence and no research was found, flag this as a gap and note it in the brief — but don't block the process. The vision can surface where research is needed.

### Step 4: Identify the New Capabilities

Ask the designer:
- What new capabilities, technologies, or investments could change this experience? (AI/ML features, new integrations, platform changes, automation, etc.)
- Are these capabilities already on the roadmap, being explored, or aspirational?
- How concrete is the team's understanding of what these capabilities can do?

Help translate abstract capabilities ("add AI") into concrete user-facing behaviors ("automatically surface the three most likely root causes based on historical incident patterns and current alert context").

### Step 5: Define Scope and Time Horizon

Help the designer draw boundaries:
- Time horizon: What does 6-12 months from now look like for this area?
- Scope: Which user journey or workflow will the vision focus on? (Push for ONE primary journey)
- What is explicitly OUT of scope?

If the designer is scoping too broadly, ask: "If you could only show one scenario to leadership that would make them say 'yes, build that,' what would it be?"

### Step 6: Identify Stakeholders and Context

Ask:
- Who needs to see this vision? (Director, VP, PM lead, engineering lead, etc.)
- What do they care about? What would make them lean forward?
- Is there an upcoming event where this could be presented? (Roadmap review, strategy meeting, design review)
- Are there any political dynamics or existing opinions to be aware of?

### Step 7: Draft the Brief

Compile everything into a structured brief document. Write it to a file in the project.

Use this template:

```markdown
# Vision Brief: [Product Area]

## Problem Statement
[2-3 sentences describing the core user problem, grounded in evidence]

## Target User
- **Role:** [Who they are]
- **Context:** [When and where they encounter this problem]
- **Goal:** [What they're trying to accomplish]
- **Current experience:** [What's painful about today — be specific]

## Evidence
[Bullet list of evidence sources: research findings, support ticket themes, analytics data, direct observations]
- **Research retrieved via `uxd-research-insights`:** [Yes / No / Not available]
- [Finding 1 with citation and slide link]
- [Finding 2 with citation and slide link]
- [Participant quote with attribution]

## New Capabilities
[What new capabilities could transform this experience]
- **Capability 1:** [Concrete description of what it does for the user]
- **Capability 2:** [Concrete description]

## Capability Readiness
- [ ] On the roadmap (committed)
- [ ] Being explored (prototyping / proof of concept)
- [ ] Aspirational (not yet started but plausible in time horizon)

## Scope
- **Time horizon:** [e.g., 6-12 months]
- **Primary journey:** [The one user workflow this vision will show]
- **Out of scope:** [What this vision does NOT cover]

## rhoai-3.6 Integration
- **Feature area:** [e.g., AIHub/, DevelopTrain/]
- **Branch:** [e.g., prototype/RHOAIUX-456-vision-agent-ops]
- **Feature flag:** [e.g., showVisionAgentOps]
- **Design history reviewed:** [Yes/No — note any relevant prior decisions]

## Stakeholders
| Who | What They Care About |
|-----|---------------------|
| [Name/Role] | [Their priorities and concerns] |

## Presentation Context
[Where and when this will be shared; any relevant dynamics]
```

### Step 8: Review with the Designer

Read back the brief and ask:
- Does this accurately capture your intent?
- Is there anything missing or wrong?
- Does the scope feel right — focused enough to be powerful, broad enough to be meaningful?

Make revisions based on their feedback.

## Quality Checks

Before finishing, verify:
- [ ] Problem statement is grounded in evidence, not assumption
- [ ] Target user is a specific role, not "users" generically
- [ ] Capabilities are described as user-facing behaviors, not technical abstractions
- [ ] Scope is ONE user journey, not an entire product area
- [ ] At least one stakeholder is identified with what they care about
- [ ] rhoai-3.6 feature area is identified and design history has been reviewed
- [ ] Branch name follows the team convention
- [ ] Feature flag name is proposed

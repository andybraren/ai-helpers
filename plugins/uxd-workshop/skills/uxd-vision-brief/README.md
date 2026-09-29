# UX vision playbook

A near-term vision is one user journey, about 6–12 months out, shown as an interactive prototype inside the product’s own shell. It makes a future experience concrete enough that leadership, product, and engineering can react to the same picture.

This is the human guide for that work. The agent steps live in each skill’s `SKILL.md`. Start with [SKILL.md](SKILL.md) in this folder.

**Contract for this phase:** [SKILL.md](SKILL.md)

## Why teams do this

- **Alignment.** A clickable story replaces everyone imagining a different future from a doc.
- **Influence.** Showing where the product could go is how design joins the priority conversation.
- **Direction.** Later feature work has a reference: does this sprint move toward the future you showed?

The artifact should make someone say “that’s where we should go.” It is grounded in known pain and capabilities the organization is actually investing in.

## Before you start

- A product area with known pain, and one journey inside it
- Whatever evidence you already have: research, tickets, analytics, observation. New research is optional. Label assumptions when evidence is thin.
- One product or engineering partner for an hour or two during the brief
- About 5–8 working days across the four phases, not necessarily consecutive
- A place to build, when you are ready: an existing product prototype, or a standalone prototype if you are still exploring

## The four phases

| Phase | Skill | Workshop | You leave with | Time |
|-------|--------|----------|----------------|------|
| 1. Brief | `uxd-vision-brief` | Value proposition canvas | Problem, user, capabilities, one journey, stakeholders | 1–2 days |
| 2. Narrative | `uxd-vision-narrative` | Vision journey map | Before/after story and the screens that tell it | 1–2 days |
| 3. Prototype | `uxd-prototype-create` | Component mapping | Interactive prototype, 3–5 screens, realistic content | 2–3 days |
| 4. Review | `uxd-vision-review` | Structured critique | Scorecard, fixes, and a plan for the stakeholder session | ~1 day |

Each phase’s file is the input to the next. Agree on the brief before writing the story. Agree on the story before building screens.

## 1. Brief

Say who hurts, what they are trying to do, which new capabilities could change that, and the one journey you will show. Name who needs to see it and what they care about.

Run `uxd-vision-brief`. If you already have a discovery brief, hand it over instead of starting from a blank problem.

**Workshop — value proposition canvas (60–90 min, with your partner).** Fill the customer side first: jobs, pains, gains. Then the value side: capabilities, pain relievers, gain creators. Use research quotes on the pains. Circle the top three pain-reliever links. Those become the problem statement and the capabilities. Unaddressed pains become out of scope.

The canvas is Alexander Osterwalder’s [Value Proposition Canvas](https://www.strategyzer.com/resources/canvas-tools-guides/the-value-proposition-canvas).

Common miss: scoping a whole product area. One journey is enough.

## 2. Narrative

Tell the story of one named person. Today’s experience, the moment a new capability changes the outcome, tomorrow’s experience, and the payoff. Then list the 3–5 screens that carry that story.

Run `uxd-vision-narrative` with the brief. The story should follow a person. “The user easily finds what they need” is not a beat. A named action, a named result, and how it feels is a beat.

**Workshop — vision journey map (about 90 min).** Five columns on a wall, board, or shared canvas: Setup, Rising tension, The pivot, New experience, Payoff. In each column note what happens, what the person does, what the product does, and how it feels. Spend the most time on the pivot: one concrete action and one concrete response. Read the row aloud as a story, then mark which moments are separate screens.

Questions worth answering, from Julie Zhuo’s framing of a future experience: when does this person hit this moment, what was broken before, what can they do now, and why would they come back?

Common miss: a feature list with a character’s name on it.

## 3. Prototype

Build only the screens the narrative needs, in the product’s design system, with realistic data. A vision that looks like a different product is easy to dismiss. Placeholder copy has the same effect.

Run `uxd-prototype-create` and give it the narrative, especially the screen breakdown. Point `--workspace` at the product prototype when you have one. Use `--decisions human` when you want to choose the design direction, and `--depth normal` unless you want fewer or more decision points. `standalone` is for an early sketch before you commit to a codebase.

After the first build, `uxd-prototype-evaluate` can check usability and acceptance criteria. That score is optional. The stakeholder judgment happens in phase 4.

**Workshop — component mapping (45–75 min, solo or with a partner).** For each screen from the journey map: find the closest existing page in the product, name the primary content and the main action, and sketch where the new capability shows up. Note the sample data (names, counts, statuses). Bring those notes to the build.

Common miss: more screens than the story needs, or generic content where the research had specifics.

## 4. Review

Judge the prototype as a vision, then prepare to show it. Six dimensions, each Strong, Adequate, or Needs work:

- **Narrative clarity** — someone who was not in the work can follow it in a few minutes
- **Problem grounding** — the pain is evidenced and specific
- **Capability demonstration** — the prototype shows how the new capability works, from the person’s point of view
- **Emotional impact** — the before feels costly and the after is worth building
- **Feasibility signal** — plausible in the time horizon you stated
- **Visual credibility** — looks like the product, with realistic data

Run `uxd-vision-review` with the brief, the narrative, and the prototype. For a design-system or usability critique, use `uxd-evaluate-design-heuristics` or `uxd-prototype-evaluate` instead of stretching this review to cover them.

**Workshop — structured critique (45–60 min, 2–6 people from design, product, and engineering).** Adapted from [Jakob Nielsen’s design critique](https://jakobnielsenphd.substack.com/p/design-crit). Share the prototype and 3–5 questions a day ahead. In the room: a silent walkthrough (5–7 min, no comments), individual notes (screen, observation, suggestion), then a facilitated discussion. Sort notes into must fix, should fix, and later.

Have a short answer ready for “when can we build this?”, “what would we cut?”, and “what have users said?”

Common miss: showing it to leadership as the first people who have seen it.

## Tips

- Write the story before the screens. A weak story does not get rescued by a polished prototype.
- Make today’s pain specific so tomorrow reads as a change.
- Keep one user, one journey, one set of capabilities.
- Let stakeholders click through it themselves when you can.
- Keep the prototype as a reference in planning. Update it when the product or the bet changes.

## Questions people ask

**What is a vision prototype for?**
It shows a transformed experience over a 6–12 month horizon so a group can decide whether that future is worth pursuing. Usability testing of a committed feature is a different job.

**Who needs to be in the room?**
A product or engineering partner during the brief, at minimum. A vision written only inside design tends to miss what the organization will actually invest in.

**What if the roadmap has no clear capabilities yet?**
Ask product and engineering what they are exploring. If there is no signal, the brief’s job is to make that gap visible.

**How finished should it look?**
Finished enough that people react to the experience. Match the product’s design system and spend the effort on real content and data.

**What if leadership does not engage?**
Show your partner first, then the immediate team. The versions that travel are the ones someone else asks to share.

**Where does the work live afterward?**
On a branch or in the artifact folder for that effort, with the brief, narrative, and review beside the prototype. After the stakeholder session, record what was decided so the next person does not re-explore a direction you already closed.

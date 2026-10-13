---
name: uxd-slides-create
version: 0.1.0
description: >-
  Create or refine a markdown slide deck from a template. Use when turning a
  brief, research readout, design review, or user journey into a local slide
  deck.
audience: UXD practitioners
inputs: A brief, notes, ticket, research, or an existing slides directory
outputs: slides.md, metadata.json, and an assets directory
---

# Create Slides

Author or revise a slide deck. `slides.md` is the source of truth. A template supplies the slide sequence and the CSS layout. The local viewer is `uxd-slides-export`. A Google Slides or Figma Slides copy is `uxd-slides-publish`.

Family: **create** → `uxd-slides-export` → `uxd-slides-publish`.

## Requirements

- Node.js 18 or later to validate `slides.md`.

## Where it lives

Default location is `.artifacts/{ID}/slides/`. Use the ticket id when one is in context. Otherwise use a kebab-case slug from the title. Use a path the user supplies when they give one.

```text
slides/
├── slides.md
├── metadata.json
└── assets/
```

`metadata.json` contains `title`, `description`, `template`, `aspectRatio` (`16:9`), `status`, `createdAt`, and `updatedAt`. `status` is `draft` until publish. Do not put secrets in metadata.

After publish, `canonical` records the shared URL. Editing `slides.md` sets `status` back to `draft` and leaves `canonical` in place. The viewer then says the shared copy is stale. The markdown remains the authoring source.

## Templates

Read [templates/README.md](templates/README.md). If the user names a type, read that folder's `context.md` and start from its `slides.md`. Keep the template's order. Replace every placeholder. When revising a deck that already exists, keep its structure unless the user asks to restart from the template.

| Request | Template |
|---|---|
| Briefing, stakeholder update, or a general talk | `templates/briefing` |
| Research readout or findings share-out | `templates/research-readout` |
| Design review or critique readout | `templates/design-review` |
| User journey or story-beat walkthrough | `templates/user-journey` |

Any other deck starts from `briefing`. Read [slides format](references/slides-format.md) before adding a slide type.

## Authoring workflow

1. Resolve the artifact id, communication goal, audience, template, and source evidence. If the goal, audience, or source is materially unclear, ask only for the missing information.
2. Read the template `context.md` and copy `slides.md` as the base before writing anything else.
3. Write one idea per slide. Use a heading plus at most five bullets, or two short sentences. Put speaker notes in a notes comment, not on the slide.
4. Copy local images into `assets/` and reference them with relative paths. Do not embed credentials, authenticated URLs, or absolute local paths.
5. Label assumptions. Do not present invented observations as research. Remove every "Replace with" placeholder.
6. Write `metadata.json`. New decks use `"status": "draft"`. A revision of a published deck returns `status` to `draft` and keeps `canonical`.
7. Validate, then build the viewer:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/validate-slides.mjs" <slides-dir>
node "${CLAUDE_SKILL_DIR}/../uxd-slides-export/scripts/export-slides.mjs" <slides-dir>
```

Fix every error. Review warnings for dense slides and missing assets. Serve the export and check the sequence, type, and images. Suggest `uxd-slides-publish` only when the user wants a Google Slides or Figma Slides copy.

## Completion check

- The sequence still follows the requested template.
- Placeholder copy is gone. Claims trace to the supplied sources, and assumptions are labeled.
- Validation passes: known slide types, headings, relative asset paths, and required metadata.
- The viewer was built and checked locally.
- A published deck that was edited is `draft` again, with the previous shared URL still in `canonical`.

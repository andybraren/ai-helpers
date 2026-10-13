---
name: uxd-slides-create
version: 0.1.0
description: >-
  Create or refine a local slide deck from a deck template. Use when turning a
  brief, research readout, design review, or user journey into slides.
audience: UXD practitioners
inputs: A brief, notes, ticket, research, or an existing slide deck directory
outputs: A deck folder with metadata.json, assets, and numbered slide folders
---

# Create Slides

Author or revise a slide deck. Each slide is a numbered folder. A deck template supplies the starting sequence. Slide templates supply a single slide when you add one. The local viewer is `uxd-slides-export`. A Google Slides or Figma Slides copy is `uxd-slides-publish`.

Family: **create** → `uxd-slides-export` → `uxd-slides-publish`.

## Requirements

- Node.js 18 or later to create and validate a deck.

## Where it lives

Default location is `.artifacts/slides-{name}/`. `{name}` is a kebab-case slug from the title. Use a path the user supplies when they give one.

```text
.artifacts/slides-name/
├── metadata.json
├── assets/
│   └── default.css
└── slides/
    ├── 1/
    │   ├── content.md
    │   ├── speaker-notes.md
    │   └── metadata.json
    └── 2/
        └── …
```

Deck `metadata.json` contains `specVersion` (`0.1.0`), `title`, `description`, `template` (the deck template name), `aspectRatio` (`16:9`), `status`, `createdAt`, and `updatedAt`. `specVersion` is the slides artifact spec in `specifications/slides/`. `status` is `draft` until publish. Do not put secrets in metadata. Do not change `specVersion` by hand.

`assets/default.css` is the layout snapshot. Deck-wide theme changes, such as a new highlight color, go in `assets/custom.css`. A slide that must diverge from its slide template gets `slides/{n}/custom.css`. Omit both files until there is a real override.

After publish, `canonical` records the shared URL. Editing the deck sets `status` back to `draft` and leaves `canonical` in place. The viewer then says the shared copy is stale.

## Templates

Read [templates/README.md](templates/README.md). If the user names a type, read that deck's `context.md`. Keep its slide order. Replace every placeholder. When revising a deck that already exists, keep its folders unless the user asks to restart from the template.

| Request | Deck template |
|---|---|
| Briefing, stakeholder update, or a general talk | `briefing` |
| Research readout or findings share-out | `research-readout` |
| Design review or critique readout | `design-review` |
| User journey or story-beat walkthrough | `user-journey` |

Any other deck starts from `briefing`. To add a slide, copy `templates/slides/{template}/` into `slides/{next-number}/`. Read [slides format](references/slides-format.md) before adding a slide template.

## Authoring workflow

1. Resolve the deck name, communication goal, audience, deck template, and source evidence. If the goal, audience, or source is materially unclear, ask only for the missing information.
2. Read the deck `context.md`, then create the folder:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/instantiate-deck.mjs" <deck-template> .artifacts/slides-{name}
```

3. Write one idea per slide in that folder's `content.md`. Use a heading plus at most five bullets, or two short sentences. Put speaker notes in `speaker-notes.md`, not on the slide.
4. Copy local images into `assets/` and set a split or beat slide's `image` to `assets/file.png`. Do not embed credentials, authenticated URLs, or absolute local paths.
5. Reorder by renaming the numbered folders. Do not edit slide content just to change order.
6. Label assumptions. Do not present invented observations as research. Remove every "Replace with" placeholder.
7. Fill deck `metadata.json`. New decks use `"status": "draft"`. A revision of a published deck returns `status` to `draft` and keeps `canonical`.
8. Validate, then build the viewer into the same folder:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/validate-slides.mjs" .artifacts/slides-{name}
node "${CLAUDE_SKILL_DIR}/../uxd-slides-export/scripts/export-slides.mjs" .artifacts/slides-{name}
```

Fix every error. Review warnings for dense slides and missing assets. Serve the deck and check the sequence, template, and images. Suggest `uxd-slides-publish` only when the user wants a Google Slides or Figma Slides copy.

## Completion check

- The sequence still follows the requested deck template.
- Placeholder copy is gone. Claims trace to the supplied sources, and assumptions are labeled.
- Validation passes: known slide templates, headings, relative asset paths, and required metadata.
- The viewer was built in the deck folder and checked locally.
- A published deck that was edited is `draft` again, with the previous shared URL still in `canonical`.

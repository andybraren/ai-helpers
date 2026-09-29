---
name: uxd-canvas-create
version: 0.0.1
description: >-
  Create or refine JSON Canvas artifacts, including journey maps, service
  blueprints, architecture diagrams, user flows, affinity maps, mind maps, and
  freeform canvases. Use when turning a brief, research, or structured content
  into a spatial canvas that works across JSON Canvas tools.
---

# Create Canvas

Create a readable spatial artifact as `canvas.json`, with optional `metadata.json` and local assets. The default output is `.artifacts/{ID}/canvas/`; honor a user-supplied location.

Family: **create** → `uxd-canvas-export` → `uxd-canvas-publish`.

## Requirements

- Node.js 18 or later to run the bundled validator.

## Inputs and outputs

Accept a brief, document, ticket, research source, existing canvas, or direct description. If the purpose, audience, or source content is materially unclear, ask only for the missing information.

Write:

```text
canvas/
├── canvas.json
├── metadata.json
└── assets/          # only when the canvas uses local files
```

`canvas.json` is the portable source of truth. `metadata.json` contains `title`, `description`, `createdAt`, and `updatedAt`; do not put presentation state or source secrets there.

## Canvas modes

- **Journey map:** define the persona, journey scope, phases, and evidence-backed lanes. Common lanes are goals/actions, touchpoints or tools, thoughts or emotions, pain points, and opportunities. Distinguish current-state and future-state journeys. Label assumptions instead of presenting invented observations as research.
- **Service blueprint:** align customer actions, frontstage activity, backstage activity, support processes, and evidence by phase.
- **Flow or architecture:** establish a clear reading direction, use short relationship labels, and encode direction with edge endpoints.
- **Affinity or mind map:** cluster concepts spatially and use groups only when the grouping adds meaning.
- **Freeform:** choose the structure that best communicates the source material.

## Authoring workflow

1. Identify the communication goal, audience, canvas mode, source evidence, and intended reading order.
2. Sketch the information hierarchy before writing nodes. For journey maps and blueprints, make phases consistent columns and lanes consistent rows.
3. Read [JSON Canvas fields and extensions](references/canvas-schema.md) before authoring unfamiliar node types or presentation extensions.
4. Write standards-compatible nodes and edges. Prefer stable, descriptive IDs such as `phase-discover-actions` over random IDs.
5. Copy local files into `assets/` and use relative paths. Do not embed credentials, authenticated URLs, or inaccessible local absolute paths.
6. Validate the result:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/validate-canvas.mjs" <path-to-canvas.json>
```

Fix every error. Review warnings for overlaps, dense text, and edge routing rather than dismissing them automatically.

## Craft rules

- Keep nodes scannable. A title plus one short supporting line is usually enough; split paragraphs and long lists across nodes.
- Size nodes to fit their content. Starting points: title `200×80`; title plus a line `250×100–120`; 3–4 short lines `250×160–200`; dense content `320–400×240–400` or multiple nodes.
- Use a 20-unit grid and leave at least 30–40 units between neighboring nodes. Avoid overlaps and edges crossing unrelated nodes.
- Use color semantically and consistently. Do not rely on color alone to communicate status or meaning.
- Put groups behind their children. The bundled viewer reserves the top 24 units of a group for its label.
- Use `fromSide` and `toSide` to reinforce reading order; add arrow endpoints when direction matters.
- Keep primary content visible without scrolling at the initial fit-to-content view.

## Completion check

- The structure answers the stated communication goal.
- Research-derived claims are traceable to supplied sources; assumptions are labeled.
- Node IDs and edge IDs are unique, dimensions are positive, and every edge resolves.
- Labels are readable, nodes do not overlap unintentionally, and local assets resolve.
- The validator completes without errors.

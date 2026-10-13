---
name: uxd-slides-export
version: 0.1.0
description: >-
  Build a local HTML, CSS, and JavaScript slide viewer from a markdown deck.
  Use when presenting a deck locally or preparing it for publish. Does not
  publish to Google Slides or Figma Slides.
audience: UXD practitioners
inputs: A slides directory with slides.md, metadata.json, and optional assets
outputs: A local viewer with HTML, CSS, JavaScript, and copied assets
---

# Export Slides

Turn a markdown deck into a local presentation. The viewer is HTML, CSS, and JavaScript, plus an `assets/` folder. Do not inline the CSS or JavaScript into `index.html`. Do not publish. Google Slides and Figma Slides are `uxd-slides-publish`. Editing the deck is `uxd-slides-create`.

The viewer source lives next to the export script:

```text
viewer/
├── index.html
├── viewer.css
├── viewer.js
└── deck-base.css
```

`scripts/export-slides.mjs` copies the viewer, appends the template's `custom.css`, and embeds the compiled deck in `index.html`. The stage is 1920×1080 and scales to the window. Arrow keys, Space, and the two halves of the slide move between slides. `S` toggles speaker notes. `F` hides the toolbar. Escape leaves present mode.

Family: `uxd-slides-create` → **export** → `uxd-slides-publish`.

## Requirements

- Node.js 18 or later.
- Python 3, or another static server, to check the viewer in a browser.

## Inputs and output

Accept a slides directory that contains `slides.md` and `metadata.json`. Images live in that directory's `assets/`.

Default output is `.artifacts/{ID}/export/` when the source directory is named `slides`. Otherwise it is `<slides-dir>/export/`.

```text
export/
├── index.html
├── viewer.css
├── custom.css
├── viewer.js
├── deck.json
├── slides.md
├── metadata.json
├── assets/
└── export-manifest.json
```

`slides.md` in the export is a copy. Edit the source `slides/` directory, then export again. `deck.json` is the compiled slide list the page embeds. `export-manifest.json` records the title, template, slide count, status, and written files.

## Flags

$ARGUMENTS

Parse as: `<slides-dir> [--output <dir>] [--title <text>]`.

| Flag | Default | Meaning |
|---|---|---|
| `--output` | sibling `export/` when the source is `slides/`; otherwise `<slides-dir>/export/` | Export destination |
| `--title` | `metadata.json` title | Viewer title |

## Build

1. Confirm `slides.md`, `metadata.json`, and every local image path.
2. Review slide text and images for confidential or personal data before suggesting publish.
3. Export:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/export-slides.mjs" <slides-dir> --output <export-dir>
```

4. Serve the export and open `index.html`. Check the first slide, a content slide, a split slide when the deck has one, notes, and present mode.

```bash
python3 -m http.server --directory <export-dir> 8000
```

5. Report the export path, template, and slide count. When `canonical` is set, say whether the banner shows a current shared copy or a stale one. Suggest `uxd-slides-publish` only when the user wants Google Slides or Figma Slides.

## Completion check

- The export opens through a local static server and needs no application server.
- CSS and JavaScript stay in `custom.css`, `viewer.css`, and `viewer.js`.
- Local images were copied under `assets/`. Remote and absolute paths were not added.
- `export-manifest.json` lists the written files, including itself.
- Speaker notes are off the slide until Notes is opened.
- The source `slides/` directory was not described as the shared copy.

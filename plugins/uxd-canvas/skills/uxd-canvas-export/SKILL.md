---
name: uxd-canvas-export
version: 0.0.1
description: >-
  Export a JSON Canvas as a portable local artifact — a single HTML viewer by
  default, or canvas.json and assets. Use when sharing a journey map locally,
  producing a static HTML file, or preparing a canvas for publish.
---

# Export Canvas

Turn a completed `canvas.json` into a portable local export. The default is a
single HTML file with the viewer and local assets inlined. Do not push or
deploy from this skill — that is `uxd-canvas-publish`.

The viewer source lives next to the export script:

```text
viewer/
├── index.html
├── viewer.css
└── viewer.js
```

`scripts/export-canvas.mjs` inlines those files with the canvas JSON into a
single `index.html` when `--viewer html`. Do not copy the separate CSS or JS
into the export.

Family: `uxd-canvas-create` → **export** → `uxd-canvas-publish`.

## Requirements

- Node.js 18 or later to build the static viewer.
- Python 3 or another local static server for browser verification of HTML exports.

## Inputs and output

Accept either a canvas directory or a path to `canvas.json`. A canvas directory can also contain `metadata.json` and `assets/`.

Default output is `.artifacts/{ID}/export/` when the source lives in `canvas/`; otherwise `<canvas-dir>/export/`.

```text
export/
├── index.html             # viewer + canvas data + inlined assets
└── export-manifest.json
```

Optional files, depending on flags:

```text
export/
├── index.html
├── canvas.json
├── assets/
└── export-manifest.json
```

## Flags

$ARGUMENTS

Parse as: `<canvas-path> [--output <dir>] [--viewer html|none] [--json|--no-json] [--assets inline|folder] [--chrome viewer|none] [--title <text>]`.

| Flag | Default | Meaning |
|---|---|---|
| `--output` | sibling `export/` when source is `canvas/`; else `<canvas-dir>/export/` | Export destination |
| `--viewer html\|none` | `html` | Include or omit the interactive HTML viewer |
| `--json` / `--no-json` | `--no-json` with HTML; `--json` with `--viewer none` | Write a sidecar `canvas.json` |
| `--assets inline\|folder` | `inline` with HTML; `folder` with `--viewer none` | Embed local files as data URIs, or copy `assets/` |
| `--chrome viewer\|none` | `viewer` | Include or omit the top toolbar and status pill (HTML only) |
| `--title` | `metadata.json` title or folder name | Viewer title |

`--no-viewer` is an alias for `--viewer none`. `--viewer none --no-json` is an error.

`--chrome viewer` includes theme, grid, mouse/trackpad, zoom in, zoom out, reset-view controls, node/edge status, pan, wheel/pinch zoom, touch gestures, and keyboard zoom shortcuts. `--chrome none` hides the toolbar and status pill but retains pan, zoom, touch, link, and scroll interactions.

## Build

1. Confirm that `canvas.json` exists and every referenced local asset is available.
2. Review canvas text, URLs, issue records, reactions, and images for confidential or personal data before suggesting publish.
3. Export. Default is a shareable HTML file:

```bash
node "${CLAUDE_SKILL_DIR}/scripts/export-canvas.mjs" \
  <canvas-path> \
  --output <export-dir>
```

Examples:

```bash
# HTML viewer plus a portable canvas.json, assets copied beside them
node "${CLAUDE_SKILL_DIR}/scripts/export-canvas.mjs" <canvas-path> --json --assets folder

# JSON Canvas only, for other JSON Canvas tools
node "${CLAUDE_SKILL_DIR}/scripts/export-canvas.mjs" <canvas-path> --no-viewer
```

4. If the export includes HTML, serve it locally and inspect the initial fit, node content, edges, assets, links, theme choices, pan, and zoom. A simple server is enough: `python3 -m http.server --directory <export-dir> 8000`. For `--viewer none`, confirm `canvas.json` and any `assets/` instead.
5. Report the local output, including viewer/json/assets mode. Suggest `uxd-canvas-publish` only when the user wants an external host.

## Completion check

- HTML exports open through a local HTTP server with no application-server dependency.
- Viewer chrome matches `--chrome` when HTML is included; interactions remain available in both chrome modes.
- `--assets inline` produces no `assets/` folder; `--assets folder` copies local files next to the export.
- `--json` writes `canvas.json`; it is omitted by default when HTML is included.
- `export-manifest.json` records title, flags, and written files.
- All nodes, edges, labels, styles, and local assets render.
- No unintended internal data, credentials, inaccessible URLs, or local absolute paths are included.
- The final response identifies the local path and export mode. Do not deploy.

# Slide deck

A deck is a folder. Slide order is the numbered folder name under `slides/`. Reorder by renaming those folders (`2` becomes `3`). Do not store a second order field.

```text
.artifacts/slides-name/
├── metadata.json
├── assets/
│   ├── default.css
│   ├── custom.css
│   └── diagram.svg
└── slides/
    ├── 1/
    │   ├── content.md
    │   ├── speaker-notes.md
    │   └── metadata.json
    └── 2/
        ├── content.md
        ├── speaker-notes.md
        ├── metadata.json
        └── custom.css
```

`assets/custom.css` and a slide's `custom.css` are omitted until someone changes the theme or that slide.

## Deck metadata.json

```json
{
  "specVersion": "0.1.0",
  "title": "",
  "description": "",
  "template": "briefing",
  "aspectRatio": "16:9",
  "status": "draft",
  "createdAt": "",
  "updatedAt": "",
  "canonical": null
}
```

`specVersion` is the slides artifact spec this folder complies with. The current spec is 0.1.0, defined in `specifications/slides/`. `template` here is the deck template (`briefing`, `research-readout`, `design-review`, or `user-journey`). `status` is `draft` while the folder is the working copy. After Google Slides or Figma Slides publish succeeds, set `status` to `published` and set `canonical` to `{ "target", "url", "publishedAt" }`. Editing the deck again sets `status` back to `draft` and keeps `canonical`.

## Slide folder

`content.md` is the visible copy only.

- `#` heading, once
- `##` subheading, once
- `###` a short group label
- `-` bullets, five or fewer, except on a beat
- `>` a quote
- `![alt](assets/file.png)` an inline image
- one fenced code block when the audience needs the source text
- `**bold**`, `` `code` ``, and `[label](https://...)` inside a line

Do not use tables. Do not use a remote or absolute image path. Copy files into the deck `assets/` folder and use a path that starts with `assets/`.

`speaker-notes.md` is speaker notes. They are not drawn on the slide. Leave the file in place when the notes are empty.

`metadata.json` says which slide template the slide uses:

```json
{
  "template": "split",
  "kicker": "Observation",
  "image": "assets/screen.png"
}
```

| `template` | What it is |
|---|---|
| `title` | Opening cover. Heading, optional subheading. |
| `section` | Section divider. Heading only. |
| `content` | Heading plus short copy or bullets. |
| `split` | Copy on the left, the `image` on the right. |
| `quote` | A quotation. The heading is the attribution when you need one. |
| `beat` | Journey beat. Story and sketch on the left. Users, unmet needs, and solutions on the right. The heading is not drawn. |
| `closing` | Same visual role as a title slide. Use it for the last slide. |

`kicker` is the small label above the heading. Omit it when the slide has none. `image` is the side image for `split` and `beat`. Omit it when the slide has no image.

A beat uses three `###` headings so the right rail stays in order: `Users this serves`, `Unmet needs this addresses`, and `Solutions we deliver`.

## Theme

`assets/default.css` is the layout snapshot from the slide templates, written when the deck is created. Do not edit it for a one-off color.

Deck-wide changes go in `assets/custom.css`. This turns the highlight red into blue:

```css
:root {
  --slide-accent: #0066cc;
}
```

A change that applies to one slide only goes in that slide's `custom.css`. Rules are scoped to that slide when the viewer is built:

```css
h1 { color: navy; }
```

Create either file only when there is a real override. The viewer does not load fonts from the network. Red Hat is used when it is installed; otherwise the deck uses Helvetica or Arial.

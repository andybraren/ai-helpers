# Slide markdown

`slides.md` is the source of truth. Slides are separated by a line that contains only `---`. Layout comes from the template CSS, not from the markdown.

## Slide directive

Put directives in HTML comments at the top of a slide.

| Comment | Meaning |
|---|---|
| `<!-- type: title -->` | Opening or closing cover. Heading, optional subheading. |
| `<!-- type: section -->` | Section divider. Heading only. |
| `<!-- type: content -->` | Heading plus short copy or bullets. |
| `<!-- type: split -->` | Copy on the left, a local image on the right. |
| `<!-- type: quote -->` | A quotation, with the heading as attribution when you need one. |
| `<!-- type: closing -->` | Same visual role as a title slide. Use it for the last slide. |
| `<!-- kicker: Findings -->` | Small label above the heading. |
| `<!-- image: assets/screen.png -->` | Side image for a split slide. |
| `<!-- notes` ... `-->` | Speaker notes. They are not drawn on the slide. |

A slide without a type is treated as `title` when it is only a heading and subheading, and as `content` otherwise. Name the type anyway.

```markdown
<!-- type: split -->
<!-- kicker: Observation -->
<!-- image: assets/catalog-list.png -->
<!-- notes
Start with what the researcher could not find.
-->
# The list hides the next step

Researchers can see model names and still cannot tell which one they can deploy.

- The primary action sits below the fold
- License and status are easy to miss
```

## What can go in the body

- `#` heading, once
- `##` subheading, once
- `###` a short group label
- `-` bullets, five or fewer
- `>` a quote
- `![alt](assets/file.png)` an inline image
- one fenced code block when the audience needs the source text
- `**bold**`, `` `code` ``, and `[label](https://...)` inside a line

Do not use tables. Do not use a remote or absolute image path. Copy files into `assets/` and use a relative path that starts with `assets/`.

## metadata.json

```json
{
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

`status` is `draft` while the markdown is the working copy. After Google Slides or Figma Slides publish succeeds, set `status` to `published` and set `canonical` to `{ "target", "url", "publishedAt" }`. The markdown stays the authoring source. The URL is the shared copy. Editing the markdown again sets `status` back to `draft` and keeps `canonical` so the viewer can show that the shared copy is stale.

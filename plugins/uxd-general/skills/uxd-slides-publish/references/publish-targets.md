# Publish targets

The shared copy is either a Google Slides presentation or a Figma Slides file. The local viewer is not a publish target.

| Target | Flag | Shared URL | metadata `canonical.target` |
|---|---|---|---|
| Google Slides | `--target google` | `https://docs.google.com/presentation/d/.../edit` | `google-slides` |
| Figma Slides | `--target figma` | `https://www.figma.com/slides/...` | `figma-slides` |

`status: "published"` means that URL is the copy to share. The markdown in `slides/` is still what a later edit starts from. Set `status` back to `draft` when the markdown changes, and keep `canonical` so the viewer can point at the last shared copy.

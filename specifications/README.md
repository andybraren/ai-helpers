# Specifications

Skills in this repository produce artifacts: a slide deck, a prototype, a canvas, a doc. An artifact is enough for a skill to write and for another skill to read. It is not enough once a person needs to open it in a viewer, edit it, discuss it, or review it.

Those interfaces have to know what a compliant artifact contains. A slides viewer has to know where slide 2 lives, which file is the speaker notes, and what `specVersion` `0.1.0` means. A prototype controller has to know the same kind of thing for a prototype. A review surface has to know how to read the artifact it is commenting on. That contract is a specification version on the artifact itself.

`specVersion` is the version of that contract. It is also the version a later API can promise: given an artifact at this version, these fields and paths are what a client can rely on. When the contract changes, an upgrade script rewrites an older artifact forward and bumps `specVersion`. Interfaces then keep one reader per version, or only the current one after the upgrade.

Each artifact type gets a directory here. That directory holds the current version, one document per version, and an `upgrades/` directory for the scripts that move an older artifact to a newer spec.

| Artifact | Spec |
|---|---|
| Slides | [slides](slides/README.md) |

Slides is the first one. The same need applies to prototypes, where a viewer or editor has to open a prototype and know how it is laid out, and to later artifacts such as canvases and docs. Those specs are not written yet.

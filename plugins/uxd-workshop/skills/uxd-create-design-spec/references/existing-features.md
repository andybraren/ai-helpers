# Existing Feature Detection

Use this when the design target is an existing product UI. The expensive mistake is designing a replacement for something the app already has.

## What to check

- Does the app already have the requested feature (assistant, notifications, search, etc.)?
- What components or patterns does it use?
- How is it triggered (button, FAB, shortcut)?
- What is its visual design (layout, copy, interactions)?

## By build strategy

### modify-source

- Scan `package.json` for related PatternFly extension packages (e.g. `@patternfly/chatbot`)
- Scan `src/` for related imports and usage
- Read README / component docs
- Distinguish "installed but not wired" vs "fully integrated"

**If found:** Spec should extend or wire up the existing feature, not replace it wholesale.

### dom-injection

- Search JS bundles for related class names / panel patterns
- Search CSS for positioning / visibility patterns
- Capture native visual design so any custom surface can match it

**If the native feature is functional:** Prefer **discoverability surfaces** (masthead entry points, hints, contextual links) that point users at the existing feature. Do not build a duplicate.

**If partial or non-functional:** Spec may describe a custom surface that **matches** the native visual design, opened from discoverability affordances.

**If interactive detection was not performed:** Default to treating a detected feature as functional. Note the assumption.

## Interactive detection (when browser automation is available)

1. Navigate to the target URL
2. Baseline screenshot
3. Click the feature trigger
4. Wait briefly for DOM updates
5. Post-click screenshot + accessibility tree snapshot
6. Classify: functional / partial / non-functional

If browser automation is unavailable, use static detection only and add a limitation note to the spec.

## Runtime note for dom-injection

Framework-rendered UIs (React, Angular, Vue, etc.) manage visibility through internal state. Programmatic clicks from external scripts do not reliably open those features. Detection-time browser testing is fine; do not design the prototype to depend on triggering native framework state from injected code.

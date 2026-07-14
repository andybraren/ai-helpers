---
name: uxd-draft-acceptance-criteria
description: >-
  Produce testable Given/When/Then acceptance criteria from a design spec.
  Use when turning a design spec into engineering-ready AC, covering states,
  interactions, accessibility, or dom-injection app-preservation checks.
---

# Draft Acceptance Criteria

Turn a design spec into acceptance criteria that engineering can verify by looking at the built UI. "Looks good" is not testable. "User can sort the table by clicking any column header, and the sort indicator updates to show the current direction" is.

Works standalone on any design spec. Pairs with `uxd-create-design-spec` upstream and with Jira / handoff workflows downstream when available.

## Inputs

| Input | Type | Required | Default |
|-------|------|----------|---------|
| Design spec | Spec from `uxd-create-design-spec` or equivalent (component mapping, interactions, a11y) | Yes | — |
| Mode | `interactive` or `pipeline` | No | `interactive` |

## Process

### 1. Extract testable interactions

From the design spec, identify every:

- User-initiated action (click, type, drag, keyboard shortcut)
- System-initiated transition (loading, error, success, timeout)
- State change (open/close, expand/collapse, sort, filter, paginate)

### 2. Draft AC in Given/When/Then format

For each interaction:

```markdown
**AC-[N]: [Short name]**

Given [precondition / initial state]
When [user action or system event]
Then [observable result the tester can verify]
```

### 3. Cover all states

For each component in the design spec, ensure AC exist for:

- **Default** — first load
- **Interactive** — hover, active, focus, selected
- **Error** — failure plus recovery path
- **Empty** — no data
- **Loading** — async in progress
- **Disabled** — when and why

If the design spec omits a state, write an AC that flags it as "not specified, verify with designer."

### 4. Draft app-preservation AC (dom-injection only)

When the design spec's build strategy is `dom-injection`, also draft AC that the original app is unharmed:

- Original layout, navigation, and content render identically to the unmodified version
- Injected styles do not override or reassign original CSS classes
- Injected CSS uses a scoped class prefix with no naming collisions
- Original JavaScript behavior (interactions, routing, state) is unaffected
- Removing the injection files leaves the original app intact

Omit this section for greenfield or modify-source builds.

### 5. Draft accessibility AC

From the design spec's accessibility requirements:

- Keyboard navigation path for each interactive element
- Screen reader announcement for state changes
- Focus management after actions (modal open/close, drawer toggle)
- Color contrast verification
- ARIA attribute presence

### 6. Quality check

Every AC must be:

- **Testable** — pass/fail by looking at the UI (not by reading code)
- **Specific** — names a component, state, or behavior
- **Independent** — verifiable without relying on other AC first
- **Complete** — covers both the action and the expected result

Minimum: **3 AC per major interaction** documented in the design spec.

## Output

Use the template in [references/ac-template.md](references/ac-template.md).

In `pipeline` mode, also append the YAML summary block from that template.

## Guardrails

- Do not write AC that can only be tested by reading code.
- Do not skip accessibility AC — they are required.
- Do not invent behavior the design spec does not specify; flag gaps as "not specified."
- Do not write vague AC ("the page looks correct", "the component works properly").
- Do not assume missing states; flag them for designer review.

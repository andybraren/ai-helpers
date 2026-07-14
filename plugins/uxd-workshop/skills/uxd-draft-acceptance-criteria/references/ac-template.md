# Acceptance Criteria Output Template

```markdown
## Acceptance Criteria

### [Section/Feature Name]

**AC-1: [Short descriptive name]**
Given [precondition]
When [action]
Then [result]

**AC-2: [Short descriptive name]**
Given [precondition]
When [action]
Then [result]

### App Preservation (dom-injection only)

**AC-P1: Original app renders identically**
Given the injection CSS and JS are loaded
When the page renders
Then the original app layout, navigation, charts, and cards appear identical to the unmodified version

**AC-P2: Scoped CSS with zero collisions**
Given the injection stylesheet is loaded
When inspecting the injected elements
Then all injected CSS classes use the scoped prefix and no original app classes are overridden

[Include only when design spec build strategy is dom-injection.]

### Accessibility

**AC-A1: [Keyboard nav for component]**
Given [component is focused]
When [user presses Tab/Enter/Escape/Arrow keys]
Then [expected focus behavior]

**AC-A2: [Screen reader for state change]**
Given [screen reader is active]
When [state changes]
Then [announcement is made: "[expected text]"]

### State Coverage Matrix

| Component | Default | Hover | Active | Error | Empty | Loading | Disabled |
|-----------|---------|-------|--------|-------|-------|---------|----------|
| [component] | AC-N | AC-N | AC-N | AC-N | AC-N | AC-N | AC-N |

### Summary
- **Total AC:** [N]
- **Interaction AC:** [N]
- **App preservation AC:** [N, or 0 if not dom-injection]
- **Accessibility AC:** [N]
- **States not specified in design spec:** [list, flagged for designer review]
```

## Pipeline mode summary

When `mode` is `pipeline`, append:

```yaml
ac_summary:
  total_count: [N]
  interaction_count: [N]
  preservation_count: [N]
  accessibility_count: [N]
  unspecified_states: [N]
  min_per_interaction_met: true | false
```

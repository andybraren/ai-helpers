---
name: pf-form-gen
description: Generate PatternFly form components with validation, layout, and accessibility. Use when building forms, adding form fields, or creating validated input workflows.
---

# PF Form Generator

Generate a complete PatternFly React form component with proper structure, validation, and accessibility.

Use the PatternFly MCP server as the primary source for up-to-date component APIs and prop signatures.

## Input

The user provides one of:
- A description of the form's purpose and fields (e.g., "create a user registration form with name, email, and password")
- A TypeScript interface or type definition to generate a form for
- An existing form component to refactor into PatternFly patterns

## Context Detection

First, confirm the project uses PatternFly. If the user explicitly requests a non-PatternFly framework (Material UI, Chakra, Ant Design, plain HTML) or the project has no `@patternfly/react-core` dependency, decline generation and explain this skill is PatternFly-specific.

Then determine the form complexity:
- **Simple form**: Few fields, no conditional logic, single submit action
- **Complex form**: Conditional fields, multi-section layout, field groups, async validation
- **Wizard form**: Multi-step form — defer to PatternFly Wizard component instead of generating a monolithic form

## How to Generate

1. Read the user's requirements and identify all fields, their types, and validation rules.
2. Look up PatternFly form components via MCP to confirm current prop signatures.
3. Generate the form using the structure and rules below.

## Form Structure

All form components import from `@patternfly/react-core`.

```tsx
import {
  Form,
  FormGroup,
  FormHelperText,
  HelperText,
  HelperTextItem,
  TextInput,
  ActionGroup,
  Button,
} from "@patternfly/react-core";
```

Basic form skeleton:

```tsx
<Form onSubmit={handleSubmit}>
  <FormGroup label="Username" isRequired fieldId="username">
    <TextInput
      isRequired
      id="username"
      value={username}
      onChange={(_event, value) => setUsername(value)}
      validated={usernameValidated}
    />
    <FormHelperText>
      <HelperText>
        <HelperTextItem variant={usernameValidated}>
          {usernameHelperText}
        </HelperTextItem>
      </HelperText>
    </FormHelperText>
  </FormGroup>
  <ActionGroup>
    <Button variant="primary" type="submit">Submit</Button>
    <Button variant="link" type="reset">Cancel</Button>
  </ActionGroup>
</Form>
```

## Rules

**Structure:**
- Every input must be wrapped in `FormGroup` with a `label` and unique `fieldId`
- `fieldId` on `FormGroup` must match `id` on the input control
- Place `ActionGroup` as the last child of `Form` for submit/cancel buttons
- Use `FormSection` to visually group related fields with a title
- Use `FormFieldGroup` with `FormFieldGroupHeader` for collapsible field clusters

**Validation:**
- Use the `validated` prop on inputs with values `"default"`, `"success"`, `"warning"`, or `"error"`
- Display validation messages via `FormHelperText > HelperText > HelperTextItem` — set the `variant` prop to match the validated state
- Mark required fields with `isRequired` on both `FormGroup` and the input control
- Validate on blur by default for individual fields, on submit for the complete form — use validate-on-change for fields that need immediate feedback (password strength, character limits, availability checks)
- Use `FormAlert` at the top of complex forms to display a summary of validation errors

**Layout:**
- Default to vertical layout — add `isHorizontal` on `Form` only when labels are short and the form is wide
- Use `isWidthLimited` on `Form` to constrain width in full-page layouts
- Use `Grid` or `Flex` inside `FormGroup` only when placing multiple inputs side by side (e.g., first name + last name)

**Input controls** — use the right PatternFly control for each field type:
- Free text → `TextInput`
- Multi-line text → `TextArea`
- Selection from list → `FormSelect` or `Select` (typeahead)
- Boolean toggle → `Checkbox` or `Switch`
- Date → `DatePicker`
- File → `FileUpload`

**Accessibility:**
- Every `FormGroup` must have a `label` — use visible label text, not placeholder-only labeling
- Associate helper text with the input using matching `fieldId`/`id`
- Inputs with validation errors must be announced — `HelperTextItem` with `variant="error"` handles this

**States:**
- Disable submit button and form controls during async submission
- Handle loading, error, and empty states appropriate to the form context

## Output

Output the complete form component ready to save. Include the import block, component function with state and validation logic, and the JSX form structure.

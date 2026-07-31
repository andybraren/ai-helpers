---
name: pf-table-gen
description: Generate PatternFly table components with sorting, filtering, pagination, and expandable rows. Use when building data tables, adding table features, or migrating HTML tables to PatternFly.
---

# PF Table Generator

Generate a complete PatternFly React table component using the composable table API.

Use the PatternFly MCP server as the primary source for up-to-date component APIs and prop signatures.

## Input

The user provides one of:
- A description of the data and desired table features (e.g., "sortable table of users with name, email, role, and bulk select")
- A TypeScript interface or type definition for the row data
- An existing table to refactor into PatternFly patterns

## Context Detection

First, confirm the project uses PatternFly. If the user explicitly requests a non-PatternFly framework (Material UI, Chakra, Ant Design, plain HTML) or the project has no `@patternfly/react-core` dependency, decline generation and explain this skill is PatternFly-specific.

Then determine the table complexity:
- **Simple table**: Static data, no interactions beyond display
- **Interactive table**: Sorting, filtering, pagination, or selection
- **Compound table**: Expandable rows, nested data, tree table, or inline editing

## How to Generate

1. Read the user's requirements and identify columns, data types, and interactive features.
2. Look up PatternFly table components via MCP to confirm current prop signatures.
3. Generate the table using the composable API and rules below.

## Table Structure

Table components import from `@patternfly/react-table`.

```tsx
import { Table, Thead, Tbody, Tr, Th, Td } from "@patternfly/react-table";
```

Basic table skeleton:

```tsx
<Table aria-label="Users table" variant="compact">
  <Thead>
    <Tr>
      <Th>Name</Th>
      <Th>Email</Th>
      <Th>Role</Th>
    </Tr>
  </Thead>
  <Tbody>
    {rows.map((row) => (
      <Tr key={row.id}>
        <Td dataLabel="Name">{row.name}</Td>
        <Td dataLabel="Email">{row.email}</Td>
        <Td dataLabel="Role">{row.role}</Td>
      </Tr>
    ))}
  </Tbody>
</Table>
```

## Rules

**Composable API — required:**
- Always use the composable API: `Table > Thead > Tr > Th` and `Table > Tbody > Tr > Td`
- Never place `Tr` directly under `Table` — always wrap in `Thead` or `Tbody`
- Never use `Th` in body rows or `Td` in header rows

**Data labels:**
- Every `Td` must have a `dataLabel` prop matching the column header text — this enables the responsive stacked layout on small screens
- `Table` must have an `aria-label` describing the data

**Sorting:**
- Use the `sort` prop on `Th` with a sort configuration object
- Manage sort state with `activeSortIndex` and `activeSortDirection` in component state
- Only mark sortable columns with `sort` — not every column needs sorting

```tsx
const getSortParams = (columnIndex: number): ThProps["sort"] => ({
  sortBy: { index: activeSortIndex, direction: activeSortDirection },
  onSort: (_event, index, direction) => {
    setActiveSortIndex(index);
    setActiveSortDirection(direction);
  },
  columnIndex,
});

<Th sort={getSortParams(0)}>Name</Th>
```

**Selection:**
- Use the `select` prop on `Th` for header checkbox (select all) and `Td` for row checkbox
- Track selected rows with a `Set<string>` keyed by row ID
- Bulk select in the header typically toggles all visible rows — if the design calls for selecting across pages, add a secondary "Select all N items" action

**Expandable rows:**
- Use `expand` prop on `Td` for the toggle cell
- Render expanded content in a separate `Tr` with a single `Td` spanning all columns using `colSpan`
- Wrap expanded content in `ExpandableRowContent`
- Track expanded state with a `Set<string>` keyed by row ID

**Row actions:**
- Use `ActionsColumn` from `@patternfly/react-table` for kebab or action menus on each row
- Pass an `items` array of action objects with `title` and `onClick` handlers
- Place the actions cell as the last `Td` in each row

**Toolbar integration:**
- Import `Toolbar`, `ToolbarContent`, `ToolbarItem`, `ToolbarFilter` from `@patternfly/react-core`
- Place a `Toolbar` above the `Table` for filters, bulk actions, and pagination
- Wrap toolbar content in `ToolbarContent` — items go inside `ToolbarItem` or `ToolbarFilter`
- Place `Pagination` in a `ToolbarItem` aligned to the end

**Pagination:**
- Use the `Pagination` component from `@patternfly/react-core`
- Manage `page` and `perPage` in component state
- Slice data based on pagination state, not the component's internal handling

**Empty state:**
- Compose with `EmptyState` from `@patternfly/react-core` when the table has no data — render it inside a `Tbody > Tr > Td` spanning all columns

## Output

Output the complete table component ready to save. Include the import block, type definitions for row data, component function with state management, and the JSX table structure.

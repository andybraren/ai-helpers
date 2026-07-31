---
name: pf-chart-gen
description: Generate PatternFly chart components with theming, responsive sizing, and accessibility. Use when building charts, data visualizations, or dashboards with PatternFly.
---

# PF Chart Generator

Generate a complete PatternFly React chart component using PatternFly's Victory-based chart wrappers with proper theming and accessibility.

Use the PatternFly MCP server as the primary source for up-to-date component APIs and prop signatures.

## Input

The user provides one of:
- A description of the chart type and data (e.g., "bar chart showing monthly revenue by region")
- A data structure or API response to visualize
- An existing chart to refactor into PatternFly patterns

## Context Detection

First, confirm the project uses PatternFly. If the user explicitly requests a non-PatternFly framework (Material UI, Chakra, Ant Design, plain HTML) or the project has no `@patternfly/react-core` dependency, decline generation and explain this skill is PatternFly-specific.

Then determine the chart type:
- **Comparison**: Bar, grouped bar → `ChartBar`, `ChartGroup`; stacked bar → `ChartBar`, `ChartStack`
- **Trend**: Line, area → `ChartLine`, `ChartArea`
- **Proportion**: Donut, pie → `ChartDonut`, `ChartPie`
- **Threshold**: Bullet, utilization → `ChartBullet`, `ChartDonutUtilization`
- **Dashboard tile**: Small inline chart → use `sparkline` variant or mini donut

## How to Generate

1. Read the user's data structure and determine the best chart type for the data relationship.
2. Look up PatternFly chart components via MCP to confirm current prop signatures.
3. Generate the chart using the imports, structure, and rules below.

## Chart Setup

**Dependencies:**

```bash
npm install @patternfly/react-charts victory
```

**CSS — required in the app entry point:**

```tsx
import "@patternfly/patternfly/patternfly-charts.css";
```

**Import path — critical:**

```tsx
import { Chart, ChartBar, ChartAxis, ChartGroup, ChartVoronoiContainer }
  from "@patternfly/react-charts/victory";
```

Always import from `@patternfly/react-charts/victory` — never from `@patternfly/react-charts` root. The bare root import is a PF5 pattern that breaks tree-shaking in PF6.

## Chart Structure

Basic bar chart example:

```tsx
<Chart
  ariaTitle="Monthly revenue"
  ariaDesc="Bar chart showing revenue by month"
  containerComponent={
    <ChartVoronoiContainer
      labels={({ datum }) => `${datum.x}: ${datum.y}`}
    />
  }
  domainPadding={{ x: [30, 25] }}
  height={250}
  width={600}
  padding={{ bottom: 50, left: 50, right: 50, top: 20 }}
>
  <ChartAxis />
  <ChartAxis dependentAxis showGrid />
  <ChartGroup>
    <ChartBar data={chartData} />
  </ChartGroup>
</Chart>
```

## Rules

**Imports:**
- Always `from "@patternfly/react-charts/victory"` — never the bare root
- Require `@patternfly/patternfly/patternfly-charts.css` in the app CSS setup

**Theming:**
- PatternFly charts use a built-in theme by default — do not set custom Victory themes
- Use `ChartThemeColor` for standard color schemes: `blue`, `cyan`, `gold`, `gray`, `green`, `multi`, `orange`, `purple`
- Use `themeColor` prop on the `Chart` wrapper to apply a scheme
- Never hardcode hex colors — use the theme system for consistency with the design system

**Accessibility:**
- Every `Chart` must have `ariaTitle` and `ariaDesc` props describing the data
- Use `ChartVoronoiContainer` as the `containerComponent` to provide interactive tooltips — this gives keyboard and screen reader users access to data values
- For donut/pie charts, include a `ChartLegend` with `legendData` and `legendPosition` so the segments are labeled without relying on color alone

**Responsive sizing:**
- Set explicit `height` and `width` on the `Chart` component
- For responsive behavior, wrap in a container `div` and recalculate `width` on resize
- Do not rely on Victory's default auto-sizing — it doesn't account for PatternFly layout context

**Composition:**
- `ChartGroup` wraps multiple data series for grouped/clustered charts — set `offset` for grouped bars
- `ChartStack` wraps multiple data series for stacked charts — do not use `ChartGroup` for stacking
- `ChartAxis` for the independent axis, `ChartAxis dependentAxis` for the Y axis
- Add `showGrid` on the dependent axis for readability
- Use `domainPadding` on `Chart` to prevent bars from touching the axis edges

**Donut/pie specifics:**
- `ChartDonut` is self-contained — it renders labels and a center label by default
- Use `subTitle` and `title` props for the center content (e.g., "100 Total")
- Use `constrainToVisibleArea` on tooltip containers to prevent overflow

**Empty state:**
- When data is absent or loading, render an `EmptyState` or skeleton placeholder instead of an empty chart

## Output

Output the complete chart component ready to save. Include the import block, data transformation if needed, and the JSX chart structure with proper theming and accessibility.

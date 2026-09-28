# Eval tooling (local dev)

Scripts here mirror the paths used by `/eval-iterate` and the Langfuse pipeline guide.
They symlink to the canonical copies in `plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/`.

## Setup

```bash
eval "$(make langfuse-env)"
make langfuse-smoke
make langfuse-verify
```

## Canonical direct-API pipeline

```bash
eval "$(make langfuse-env)"
make langfuse-pipeline KEY=RHAISTRAT-1492 \
  URL=http://127.0.0.1:3000 \
  WORKSPACE=/path/to/prototype \
  JIRA_CONTEXT=tmp/benchmarks/RHAISTRAT-1492/jira-context.json \
  ESTIMATE_ONLY=1
```

The old per-skill `langfuse-compare-models.py` harness was retired. Use the
canonical pipeline estimate and review its bounded phase costs before any
provider-backed run.

## Pre-run cost estimate (zero-spend)

```bash
eval "$(make langfuse-env)"
make langfuse-cost-estimate KEY=RHAISTRAT-1492          # median of matching prior runs
make langfuse-cost-estimate KEY=RHAISTRAT-1492 BUDGET_USD=5.00   # exit 2 if over budget
```

Evidence tiers per phase: `[calibrated]` (matching past runs) → `[similar]`
(other tier, same run/fix mode) → `[bound]` (worst-case `OPENAI_PHASE_BOUNDS`).
Overrides via `CONFIG=docs/cost-experiments/cost-estimate-config.example.json`.
`--offline-fixture docs/cost-experiments/fixtures/cost-estimate-fixture.json`
tests without a Langfuse instance.

## Orchestrator

Use `/eval-iterate RHAISTRAT-1492 <URL> --workspace=<rhoai-path>` in Cursor.
The active pipeline uses bounded direct OpenAI API calls. Personal runs default
to metadata-only Langfuse traces; controlled benchmarks require full-content
trace capture and fail closed when Langfuse is unavailable. The removed MLflow
and per-skill model-comparison harnesses are not supported.

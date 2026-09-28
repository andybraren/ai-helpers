# Tracing and Budget Tracking Guide

This guide covers the direct-API prototype creator and evaluator. It explains
which data each path sends to Langfuse, where credentials and cost ledgers live,
and how to estimate before approving a paid creator phase.

## Architecture and privacy boundaries

The creator and evaluator are separate components with separate Langfuse
projects, credential files, run records, and budget ledgers. The direct-API
runner calls a bounded phase adapter; Langfuse receives either allowlisted
metadata or the content allowed by that run's trace profile. API keys are
provided through environment variables and are not written to usage journals
or artifact manifests.

| Path | Langfuse content | Cost authority |
| --- | --- | --- |
| Deterministic creator intake, serve, and verification | `metadata_only`: phase, status, HTTP results, run identity, and hashes. No source or page body. | Creator ledger remains local. Deterministic phases invoke no model and cost `$0`. |
| Creator paid phase runner | `full_raw`: provider request/response, tool exchanges, and phase artifact content, with credential redaction. | Creator-only `$15` cap and `openai-budget-ledger-creator.json`. |
| Creator artifact-manifest recorder | Content-free manifest: file URIs, sizes, hashes, phase usage, and ledger summary. File bodies are not uploaded by the manifest. | Reads the creator ledger; invokes no model. |
| Evaluator personal run | Defaults to metadata. `--trace-content sanitized` or `--trace-sanitized-artifacts` adds allowlisted structured results. | Evaluator-only `$25` cap and `openai-budget-ledger.json`. |
| Controlled evaluator benchmark | Full model, tool, artifact, and usability content is required by the benchmark trace policy. The run fails closed if Langfuse cannot accept that trace. | Evaluator-only `$25` cap and its benchmark ledger. |

The creator always loads the repository's `.env.creator` for paid phases. It
does not fall back to the evaluator's `.env.local`. Paid creator phases require
`OPENAI_API_KEY` and the creator Langfuse keys in `.env.creator`; missing keys
block execution. Evaluator commands load `.env.local` through
`scripts/eval-env.sh` or the evaluator preflight. Keep both files untracked and
owner-only readable/writable (mode `0600`), with keys for their own Langfuse
projects. Never copy creator project keys into the evaluator environment or
vice versa.

Usage journals are local append-only records. Each provider response's token
usage is persisted before the next phase step. A later timeout or process
failure therefore preserves known cost; a request without a provider usage
response remains unknown and retains its reservation. Price-card estimates are
budget bounds, not provider invoices. Cache effects and provider billing can
change actual cost.

Creator phases reuse one `--run-id` and a private trace-context file under
`.artifacts/{KEY}/benchmark/`; deterministic serve and manifest observations
attach to that run's trace. Evaluator phases use their own context file and the
same run ID when explicitly coordinated. The projects and budget ledgers stay
separate.

Text and structured fields are recursively scrubbed for API keys, bearer
credentials, cookies, and secret-valued fields. Credential-named files are
omitted from full artifact bundles. Screenshot bytes are carried as image data
and are not OCR-scanned, so visible credentials in an image are not reliably
removed. Review benchmark fixtures for credentials before enabling full-content
tracing.

## Resolve a workspace

Resolve and clone the GitLab project before using a paid phase runner. The
resolver creates `.artifacts/{KEY}/code` under the current directory and emits
the resolved checkout path:

```bash
python3 plugins/uxd-prototype/skills/uxd-prototype-create/scripts/resolve_workspace.py \
  https://gitlab.cee.redhat.com/uxd/prototypes/rhoai \
  --rfe-key RHAISTRAT-432
```

The resolver prints the cloned path, normally `.artifacts/RHAISTRAT-432/code`.
Set the repository path before changing directory, then run the estimate and
phase commands from that cloned workspace root. This keeps the estimate,
artifacts, and manifest beneath the same `.artifacts/RHAISTRAT-432/` directory.
The estimate command below accepts the URL for context and does not clone it.
`creator-phase-runner.py` requires a local workspace directory, and its prompt
file must exist inside that directory. Resolve the URL first and use the
resulting local path for the phase runner.

## Zero-spend estimate check

This reports the configured creator phase ceilings and cost card, initializes
the separate creator ledger under `.artifacts/RHAISTRAT-432/benchmark/`, and
sets `model_invoked` to `false`. It does not call OpenAI or require a provider
key.

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKSPACE="$REPO_ROOT/.artifacts/RHAISTRAT-432/code"
cd "$WORKSPACE"

python3 "$REPO_ROOT/plugins/uxd-prototype/skills/uxd-prototype-create/scripts/pipeline_mode.py" \
  --key RHAISTRAT-432 \
  --workspace https://gitlab.cee.redhat.com/uxd/prototypes/rhoai \
  --estimate-only
```

Review `estimated_openai_cost_usd`, `remaining_cap_after_estimate_usd`, and each
entry under `paid_phases`. Stop if the estimate is blocked or if a prior unknown
reservation is still active.

## Phase estimate, approval, and run

Save the phase prompt under the cloned workspace, for example at
`.artifacts/RHAISTRAT-432/creator-task.md`. Run estimate-only first. Keep the
phase, workspace, prompt, run ID, and model unchanged when repeating the
command with `--approve-estimate`; that second command invokes the provider and
uploads full phase content to the creator Langfuse project.

```bash
REPO_ROOT="$(git -C /Users/ejaquez/Desktop/ai-helpers rev-parse --show-toplevel)"
WORKSPACE="$REPO_ROOT/.artifacts/RHAISTRAT-432/code"
cd "$WORKSPACE"

PROMPT_FILE="$WORKSPACE/.artifacts/RHAISTRAT-432/creator-task.md"
RUN_ID="create-RHAISTRAT-432-canary"
RUNNER="$REPO_ROOT/plugins/uxd-prototype/skills/uxd-prototype-create/scripts/creator-phase-runner.py"

python3 "$RUNNER" \
  --key RHAISTRAT-432 \
  --phase create-plan \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --run-id "$RUN_ID" \
  --estimate-only

# After reviewing the exact estimate and approving this phase:
python3 "$RUNNER" \
  --key RHAISTRAT-432 \
  --phase create-plan \
  --workspace "$WORKSPACE" \
  --prompt-file "$PROMPT_FILE" \
  --run-id "$RUN_ID" \
  --approve-estimate
```

Each paid creator phase has its own estimate, approval, and reservation. The
creator ledger is separate from the evaluator's ledger and cannot spend the
evaluator's `$25` authority.

## Deterministic intake, serve, and manifest checks

The deterministic phase recorder writes an allowlisted local event without
loading provider credentials or invoking a model:

```bash
python3 "$REPO_ROOT/plugins/uxd-prototype/skills/uxd-prototype-create/scripts/pipeline_mode.py" \
  --key RHAISTRAT-432 \
  --program-run-id create-RHAISTRAT-432-check \
  --record-phase create-intake
```

After the checkout has a build script and a built page, serve and verify its
root and journey route. This may install dependencies and run the repository's
build script; inspect those scripts before running them in an unfamiliar
checkout. Add `--env-file .env.creator` only when intentionally exporting the
metadata-only create-serve trace to the creator Langfuse project.

```bash
python3 "$REPO_ROOT/plugins/uxd-prototype/skills/uxd-prototype-create/scripts/pipeline_mode.py" \
  --key RHAISTRAT-432 \
  --program-run-id create-RHAISTRAT-432-check \
  --workspace "$WORKSPACE" \
  --journey-route / \
  --expected-text "RHOAI"
```

The serve check rejects non-HTTP-200 routes and login pages. It writes only
allowlisted metadata locally. If Langfuse export is requested, it performs a
read-only health/auth preflight and records the deterministic event without
source or rendered page text.

After creator artifacts exist, append the content-free manifest to the
creator-project trace. This requires `.env.creator` or an explicit creator
environment file, but does not invoke OpenAI:

```bash
python3 "$REPO_ROOT/plugins/uxd-prototype/skills/uxd-prototype-create/scripts/record_creator_artifact_manifest.py" \
  --key RHAISTRAT-432 \
  --workspace "$WORKSPACE" \
  --run-id create-RHAISTRAT-432-check \
  --comparison-id creator-RHAISTRAT-432-deterministic-check \
  --env-file "$REPO_ROOT/.env.creator"
```

Stop the local server after verification:

```bash
python3 "$REPO_ROOT/plugins/uxd-prototype/skills/uxd-prototype-create/scripts/pipeline_mode.py" \
  --key RHAISTRAT-432 --stop
```

## Active tracing and cost-authority files

The sanitized/direct-API evaluator path uses
`langfuse-trace-pipeline.py` as its controller,
`langfuse_trace.py` for trace and cost authority,
`verify-langfuse.py` for preflight, and `usage_journal.py` for response-level
usage recovery. The creator path uses `pipeline_mode.py` for estimate and
deterministic phases, `creator-phase-runner.py` for approved model phases, and
`record_creator_artifact_manifest.py` for content-free artifact lineage.
`log-cost-ledger.js` remains an active evaluator ledger writer, and
`langfuse-eval.py` remains the explicit Langfuse-side evaluator entry point.

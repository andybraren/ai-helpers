# Evaluator pipeline audit

Living baseline for the active OpenAI/Langfuse evaluator path.

## Current status

| Field | Value |
|---|---|
| Baseline audited | 2026-09-22 |
| Repository commit | `3abf5fc` |
| Scope | OpenAI direct pipeline only; Anthropic-compatible path excluded |
| Evidence level | Static source/schema/docs review plus offline fixtures |
| Offline suite | `bash plugins/uxd-workshop/skills/uxd-prototype-evaluate/tests/run-script-tests.sh` |
| Offline result | **PASS — 27/27** (2026-09-23) |
| Paid evidence | Three evaluator attempts in recent price-tracking validation; newest stopped at eval-usability. No retries after the latest failure. |

### Scorecard

| Area | Status | Main result |
|---|---|---|
| Data flow | Risk | Canonical and legacy artifacts are both live contracts. |
| Cache | Risk | Full-cache restore does not satisfy current report-runner inputs. |
| Phase boundaries | Risk | Model phases mix canonical inputs with legacy outputs. |
| Report contract | Risk | Renderer virtualizes legacy projections; runner still requires legacy files. |
| Cost and telemetry | Improved; invoice unverified | Direct phases record model/provider, input, cache reads/writes, output and cache-aware standard-price estimates in Langfuse and the per-run ledger. Estimates are not provider invoices. |

Status meanings: **Pass** = verified contract and test coverage; **Needs audit** = not yet reviewed; **Risk** = verified mismatch or missing proof; **Blocked** = cannot verify without user-provided environment or authority.

## Audit protocol

Run this cycle after a material evaluator-pipeline change:

1. Record commit, scope, audit date, and no-cost command result in **Current status**.
2. Inspect the five areas below with `rg`, source/schema comparison, and docs-to-runtime checks.
3. Run offline fixtures. Do not run a paid model call, use credentials, or write production artifacts without a separate request.
4. Update existing finding IDs rather than creating duplicates. Add a dated entry to **Audit log**.
5. Keep **Next audit** to five actions or fewer.

Communication during a future audit:

1. Start: `Step N/5: <area>. Files: <paths>. Method: <check>. ETA: <time>.`
2. After each step: state one verified result, then the highest-risk finding.
3. End: state five scorecard results, test result, and one next action.

## Findings

| ID | Severity | Status | Area | Evidence | Impact | Recommended next action |
|---|---|---|---|---|---|---|
| DATA-01 | High | Open | Data flow | [`assemble-phase-a-canonical.js`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/assemble-phase-a-canonical.js) builds canonical files from `extract-state.json`, `evaluation-report.csv`, `consistency-report.json`, and `prototype-evidence.json`; [`sync-phase-b-canonical.js`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/sync-phase-b-canonical.js) merges legacy phase output back into canonical files. | Two mutable representations can disagree; ownership is not one-way. | Select one authoritative runtime contract. During migration, allow canonical-to-legacy projection only for named consumers. |
| CACHE-01 | High | Open | Cache and report | [`xray-cache.js`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/xray-cache.js) stores/restores only five canonical files. [`run-report.js`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/run-report.js) requires `extract-state.json`, `evaluation-report.csv`, `journey-log.json`, and `persona-results.json`. Full-cache restore installs only canonical files plus legacy action files. | A valid full-cache hit can bypass paid phases then fail before report rendering because required legacy inputs are absent. | Make `run-report.js` accept canonical input, or materialize all required legacy report artifacts on a cache hit. Add one full-cache-to-report fixture test. |
| PHASE-01 | Medium | Open | Phase boundaries | [`langfuse-trace-pipeline.py`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/langfuse-trace-pipeline.py) declares canonical inputs for `eval-journey`, but outputs `journey-log.json`; visual and usability phases consume/produce legacy artifacts. | Phase contracts are mixed, increasing adapter and stale-artifact surface. | Define canonical phase payloads or explicitly mark legacy files as bounded provider transports with a single canonical merge boundary. |
| REPORT-01 | High | Open | Report contract | [`report-inputs.js`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/report-inputs.js) creates in-memory legacy projections from canonical files. [`render-report.js`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/render-report.js) reads those virtual files. [`canonical-artifacts.md`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/references/canonical-artifacts.md) says report reads canonical JSON directly, while `run-report.js` blocks canonical-only input. | Docs overstate migration completion; the runner and renderer disagree about accepted input. | Change runner to use `loadReportInputs`, or narrow docs to say renderer—not report runner—accepts canonical data through compatibility projections. |
| TELEMETRY-01 | High | Resolved (2026-09-23) | Cost ledger | `langfuse-trace-pipeline.py` appends exactly one `cost-ledger.jsonl` row on each completed or failed invocation; offline fixture verifies `api` row shape and totals. | Durable per-run estimates are available beside evaluation artifacts. | Keep the append idempotent per run ID before allowing pipeline resume. |
| TELEMETRY-02 | Medium | Resolved (2026-09-23) | Telemetry schema | [`ledger-schema.json`](cost-experiments/ledger-schema.json) now accepts `invocation: api`, `evaluator-*` run IDs, model/provider/status, and cache writes. | The schema accepts direct pipeline rows and cache-aware cost details. | Validate every ledger row against this schema in CI. |
| TELEMETRY-03 | High | Open | Interrupted reservations / historical estimates | The personal-run ledger retains an active $1.987562 `eval-consistency-visual` reservation from a client timeout with unknown provider usage. That pre-long-context hold was based on short-context pricing; the current 991,781-input/400-output bound is $3.973124 at GPT-6 Sol long-context rates. Historical per-run rows also lack per-response usage needed to reprice context tiers. | Unknown billed usage remains unreconciled; the old hold is below the current worst-case bound, while the pending-unknown gate still blocks new reservations in that ledger. | Reconcile the timed-out request from provider usage/billing before releasing or resizing the hold; do not reprice completed historical rows without request-level usage. |

## Ownership map

| Artifact or boundary | Producer | Current consumer | Authority today | Validation / cache |
|---|---|---|---|---|
| `extract-state.json`, `mr-delta.json` | Deterministic Jira extraction | Classify, Phase A assembly, fix, usability, runner | Legacy transport | Local phase validators |
| `evaluation-report.csv` | Classification; journey may update it | Phase A assembly, fix, report runner, ledger quality reader | Legacy report/fix transport | Classify/verdict validators |
| `consistency-report.json` | Deterministic source then visual phase | Phase A assembly, Phase B sync, renderer | Legacy transport | Consistency validator |
| `prototype-evidence.json` | Evidence capture | Phase A assembly, visual phase | Legacy transport | Portable-evidence tests |
| Five canonical files | Phase A assembly; Phase B sync | Structured journey input, cache, virtual report inputs | Cache contract / normalized snapshot | Canonical schemas and cross-file validator |
| `journey-log.json`, `persona-results.json` | Structured journey; live usability | Visual phase, Phase B sync, report runner | Legacy model output | Structured/live-provider validators |
| HTML report and summary | Renderer | Publish and user | Final presentation | Rendering validator |
| Langfuse trace | Pipeline trace helpers | Langfuse UI | Runtime telemetry | Langfuse tracing tests |
| Cost ledger | Standalone ledger writer | Cost experiments | Intended durable cost record | Schema exists; direct-pipeline wiring absent |

## Phase map

| Phase | Execution | Inputs | Outputs | Gate / failure boundary |
|---|---|---|---|---|
| `eval-consistency-source` | Local | Workspace source, Jira context | `consistency-report.json` | Deterministic result required before Phase A assembly |
| `eval-extract` | Local | Jira context, workspace | `extract-state.json`, `mr-delta.json` | Extraction failure stops pipeline |
| `eval-classify` | Local | Extracted ACs | `evaluation-report.csv` | Classification failure stops Phase A |
| Evidence capture | Local | Prototype URL | `prototype-evidence.json` | Capture failure stops Phase A |
| Phase A assembly | Local | Four legacy artifacts plus CSV | Canonical five; action projections | Schema + parity checks; cache lookup/store |
| `eval-journey` | OpenAI | Canonical five | `journey-log.json` | Structured output; Phase B sync follows success |
| `eval-fix` | OpenAI | Legacy suggestions/CSV/extract | `fix-log.json` | Bounded workspace changes; out of canonical flow |
| `eval-consistency-visual` | OpenAI | Legacy consistency/journey/evidence | `consistency-report.json` | Structured output; merged during Phase B sync |
| `eval-usability` | OpenAI/browser | Legacy extract/journey | `persona-results.json`, `journey-log.json` | Live browser output; merged during Phase B sync |
| Phase B sync | Local | Canonical five plus legacy model outputs | Updated canonical five; full cache | Canonical validation required |
| `eval-report` | Local | Legacy runner inputs; renderer supports virtual canonical projections | HTML, summary, metrics | Runner currently rejects canonical-only directory |

## Evidence checked

- Pipeline controller: `scripts/langfuse-trace-pipeline.py`
- Canonical assembly and merge: `scripts/assemble-phase-a-canonical.js`, `scripts/sync-phase-b-canonical.js`
- Cache: `scripts/xray-cache.js`, `tests/test-xray-cache.js`
- Report: `scripts/run-report.js`, `scripts/render-report.js`, `scripts/report-inputs.js`
- Telemetry: `scripts/langfuse_trace.py`, `scripts/log-cost-ledger.js`, `docs/cost-experiments/ledger-schema.json`
- Contracts: `references/canonical-artifacts.md`, `references/caching-and-routing.md`, `references/langfuse-conventions.md`

## Data-flow LLM judge draft

The Langfuse-side rubric and evaluator setup are in
[`data-flow-judge-rubric.yaml`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/config/data-flow-judge-rubric.yaml)
and
[`data-flow-judge-evaluator.yaml`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/config/data-flow-judge-evaluator.yaml).
The judge scores lineage completeness, authority, contract compatibility,
cache completeness, phase handoffs, and verification/observability. It is
designed to receive a sanitized per-run artifact-flow manifest.

**Wiring status: manifest emission implemented.** Each run emits an
`eval-data-flow-audit` child observation with a sanitized manifest of phase
inputs/outputs, artifact hashes, cache identity, validation, and report status.
On a completed report, `eval-report-quality-audit` carries a separate manifest
that compares canonical score/counts with the report and checks each embedded
PNG digest against the local prototype captures. Neither observation uploads
source, Jira text, HTML, or image bytes. They are deterministic audits (zero
OpenAI tokens); Qwen judge inference/cost is separate. Scope Langfuse evaluator
rules to these two names, not the ordinary paid-phase outputs. A digest match
does not prove the screenshot depicts the correct visual state: the report
judge must disclose this limitation rather than claim independent visual review.

The report judge contract is in
[`report-quality-judge-rubric.yaml`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/config/report-quality-judge-rubric.yaml)
and
[`report-quality-judge-evaluator.yaml`](../plugins/uxd-workshop/skills/uxd-prototype-evaluate/config/report-quality-judge-evaluator.yaml).

Price display contract: per-phase model slug is explicit in observation
metadata; OpenAI token usage includes cache reads and writes separately.
Cost is a standard short-context **price-card estimate** computed from the
provider's usage, not a provider invoice. Local phases report model_invoked=false
and zero cost. The creator's create-serve identity bridge remains deterministic
and zero-cost, while `creator-phase-runner.py` now reports bounded paid
`create-plan`, `create-generate`, and `create-refine` usage against its separate
$15 ledger. Ordinary OpenCode creator generations outside that runner must be
reported separately; missing OpenCode/Qwen pricing must not be presented as free.

Langfuse evaluator rules are enabled in the prototype-evaluator project for
`metadata.audit_type=evaluator-pipeline-data-flow` (evaluator
`cmueasm8y00bc1i02847sn91k`, rule `cmueatl0200bm1i023ok1zusm`) and
`metadata.audit_type=evaluator-report-quality` (evaluator
`cmueasmbr00bh1i02eo7yeqqy`, rule `cmueatl2u00br1i02sh2k4m5g`). Both
select SPAN observations. The Qwen evaluator's asynchronous scores and model
provider bill must be checked separately; creation of the rule does not prove
that a judge ran or produced a score.

Read-only check of trace `evaluator-20260923-181112-3c95c8` confirmed one
`evaluation/<run_id>` root and paid-generation metadata `model=gpt-6-sol` with
direct estimated `costDetails`. Langfuse's `modelId` is still null because this
project has no matching native model definition; the explicit model slug is in
observation metadata and the ledger. Neither new judge had emitted a score at
the last check. The report-quality observation is correctly absent because the
pipeline failed before report rendering.

## Audit log

### 2026-09-27 — cold/light gates and creator pricing path

- Compared the canonical creator with Andy `main` at `96905d2`; the current
  main path is `plugins/uxd-prototype/skills/uxd-prototype-create`. Removed the
  workshop eval-only duplicate after confirming its cases are identical to the
  canonical plugin's cases; retained the local GPT-6 eval settings.
- Added bounded OpenAI creator phases (`create-plan`, `create-generate`,
  `create-refine`) with GPT-6 defaults, a `$15` separate reservation ledger,
  zero-spend estimates, exact estimate matching, explicit approval, no-retry
  attempt records, and metadata-only Langfuse generation observations.
- The evaluator direct runner now filters `eval-fix` and report rendering when
  the corresponding flags are supplied, applies no-fix to its pre-run estimate,
  and passes cold runs to Phase A's full and phase-cache bypass. The normal
  cached/full-report path remains available when light flags are absent.
- Python creator/evaluator tests and the consistency-checker suite passed.
  The cache-bypass JavaScript fixture was added but could not be executed in
  this environment because Node.js is unavailable; rerun it in CI before a
  paid light trace.

### 2026-09-23 — tracing, judge, and price-card update

- Verified phase model metadata, token buckets, direct estimated costs, and the `api` cost-ledger row on Langfuse trace `f72af007ed148494f316f28dcb689b44`.
- Added deterministic `eval-data-flow-audit` and completed-run-only `eval-report-quality-audit` observations. The report manifest checks canonical parity and exact PNG hashes, and explicitly does not claim to visually inspect screenshots.
- Created and activated two Qwen evaluator definitions and observation rules. No score records were present at read-only verification time.
- Added cache-read/cache-write price-card settlement and per-run designer-facing `evaluation-cost.json` plus HTML cost disclosure. Historical cap-ledger entries are not retroactively reconciled; an interrupted $1.987562 reservation remains held because billed usage is unknown.
- Latest evaluator attempt stopped at `eval-usability` with an ungrounded `cross_persona_handoffs` claim. A narrower offline grounding fix was added and unit-tested; no paid retry was made.
- Creator test served the new ticket prototype at `http://127.0.0.1:63946/playground`; standalone consistency passed 24/24 with 0 violations and 0 warnings.
- Offline evaluator suite passed **27/27**; consistency checker suite passed **14/14**; OpenCode trace tests passed **5/5**.

### 2026-09-22 — baseline

- Scope limited to direct OpenAI pipeline; no credentials, paid model calls, or production artifacts.
- Static review completed for data flow, cache, phase boundaries, report contract, and telemetry.
- Offline suite passed: **25/25**.
- Opened `DATA-01`, `CACHE-01`, `PHASE-01`, `REPORT-01`, `TELEMETRY-01`, and `TELEMETRY-02`.
- Added a Langfuse data-flow judge rubric/config; integration awaits the dedicated sanitized manifest observation.
- No pipeline implementation files changed by this audit.

## Next audit

1. Add a fixture proving full-cache restore reaches report rendering without legacy source files.
2. Decide canonical or legacy authority, then document a one-way compatibility boundary.
3. Wire and validate one cost-ledger row from the direct OpenAI pipeline.
4. Align ledger `invocation` schema with telemetry conventions and test `api`.
5. Re-run this audit after report-runner or cache changes.

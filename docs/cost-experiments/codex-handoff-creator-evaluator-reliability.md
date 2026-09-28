# Codex handoff: creator/evaluator runner and observability remediation

**Purpose:** give a new Codex agent the context and ordered work needed to make
`uxd-prototype-create` and `uxd-prototype-evaluate` reliable, cost-accountable
pipeline runners, with complete Langfuse traces for controlled benchmark runs.

**Execution status:** plan only. Do not launch another paid pipeline run until
the user explicitly approves the canary estimate.

## Desired outcome

1. Every provider response contributes its usage and estimated cost, including
   failed, interrupted, or turn-bounded runs. A run with unknown usage is never
   reported as `$0`.
2. A selected full-trace benchmark records the prompts, model responses, tool
   calls/results, generated artifacts, and usability evidence in Langfuse.
3. One stable run identity organizes the full creator/evaluator pipeline under
   one Langfuse trace, with ordered phase and tool observations and a final
   artifact/data-flow manifest.
4. The executable pipeline is driven by explicit phase contracts and narrow
   runners. Prose skills remain designer-facing instructions and references;
   they are not passed wholesale to an open-ended shell agent as the runtime.
5. Cost and quality are comparable across skill revisions, models, runs, and
   the `prototype-create` / `prototype-evaluator` Langfuse projects.

## Repository and current-run context

- Repo: `/Users/ejaquez/Desktop/ai-helpers`.
- Canonical creator: `plugins/uxd-prototype/skills/uxd-prototype-create/`.
- Evaluator: `plugins/uxd-workshop/skills/uxd-prototype-evaluate/`.
- Shared direct-API agent and Langfuse implementation:
  - `plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/openai_api_agent.py`
  - `plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/langfuse_trace.py`
- Main evaluator orchestrator:
  `plugins/uxd-workshop/skills/uxd-prototype-evaluate/scripts/langfuse-trace-pipeline.py`.
- Creator paid-phase runner:
  `plugins/uxd-prototype/skills/uxd-prototype-create/scripts/creator-phase-runner.py`.
- Current Jira experiment: `RHAISTRAT-1745`, scratch workspace
  `/tmp/creator-cost-test-rhaistrat-1745`.
- Successful creator phases, price-card estimates (not provider invoices):
  - `create-plan`: 21,460 input / 1,621 output tokens, 4 rounds, `$0.041702`.
  - `create-generate`: 345,437 input / 22,553 output tokens, 17 rounds,
    `$0.3899016`.
  - Corrected `create-refine`: 83,219 input / 1,980 output tokens, 12 rounds,
    `$0.0727011`; consistency check found 24 passes, zero violations, zero
    warnings.
- Successful plan and generator/refiner phases used different recovery run IDs.
  The generator/refiner trace is
  `https://langfuse-ux-eval.apps.rosa.uxdpoc7.9hji.p3.openshiftapps.com/project/cmualk91e001f1i02s1usk3fn/traces/dc95b1e14d024262e1484c9551fb31a9`.
  A content-free artifact manifest was added to that trace with local file URIs,
  hashes, file sizes, phase usage, and ledger state. The plan generation itself
  remains a child of an earlier trace, but its phase record/link is included in
  the consolidated manifest.
- Settled cost across all RHAISTRAT-1745 attempts is `$0.6644403`. An older
  interrupted `create-generate` attempt still holds a `$3.84`
  usage-unknown reservation in
  `.artifacts/RHAISTRAT-1745/benchmark/openai-budget-ledger-creator.json`.
  Preserve that reservation unless its usage is reconciled; it is not known
  spend and must not be relabeled as zero.
- The prototype and its source artifacts are under
  `/tmp/creator-cost-test-rhaistrat-1745/.artifacts/RHAISTRAT-1745/`.
- The working tree already contains broad unrelated changes. Inspect
  `git status --short --branch` and targeted diffs before editing. Preserve
  existing work; do not reset, clean, stage, or commit it.

## Verified code facts and hypotheses to test

### Trace content and privacy

- `langfuse-trace-pipeline.py` currently selects `full_raw` for an injected
  Langfuse context, `sanitized_artifact_output` with
  `--trace-sanitized-artifacts`, and otherwise `metadata_only`.
- `LivePipelineTrace.raw_capture` currently depends on injected trace context,
  not solely on `privacy_mode`. `start_phase` hashes/counts input but sends
  `input=None` without raw capture. `finish_phase` sends no output in
  `metadata_only`, and only a passed sanitized output in sanitized mode.
- `docs/cost-experiments/end-to-end-observability-plan.md` still says
  metadata-only and excludes Jira bodies, screenshots, report HTML, and tool
  I/O. Update this conflicting project guidance as part of the implementation.
- The user's requested benchmark behavior is full data-flow visibility in the
  Langfuse project, including Jira acceptance criteria, generated prototype
  output, tool exchanges, and usability evidence. Implement that for the
  controlled creator/evaluator benchmark path. Continue to redact API keys,
  bearer tokens, cookies, and other credentials; raw user/product content is
  distinct from credentials.

### Usage loss and turn caps

- `langfuse-trace-pipeline.py` catches `RuntimeError` / `ValueError` from phase
  runners and currently fabricates a failed result with empty `token_usage` and
  `cost_usd: 0`. This is a confirmed zero-cost-mirage path.
- `openai_api_agent.run_agent` now returns usage on normal completion, its
  artifact/token/cost gates, and explicit `OpenAIResponseError` HTTP responses.
  Generic network errors/process loss can still bypass the return value after
  earlier paid turns; audit and fix all callers, not only creator.
- The creator is configured for no fixed tool-round limit, but has cumulative
  input/output token bounds, a phase reservation-cost bound, artifact feedback,
  and an artifact freshness gate. Keep bounded inputs/cost and recovery
  telemetry; do not restore unbounded exploratory shell access.
- Creator errors previously lost partial usage on HTTP 400 and could strand a
  reservation. A prior fix now catches explicit response errors and settles
  known usage. Regression-test this behavior across Python and Node wrappers.
- `openai-browser-persona.js` currently sets `store: false` and manually sends
  the prior response output plus function-call outputs into the next request;
  it does **not** currently use `previous_response_id` in this file.
  `openai_api_agent.py` does use `previous_response_id`, but does not set
  `store: false`. The reported combination may refer to another revision/path;
  verify request payloads and reproduce before claiming it is the cause.
- The persona wrapper has `LiveUsabilityError` carrying accumulated usage and
  emits it as JSON on handled errors. But Python's `openai_live_usability.py`
  raises on invalid/missing JSON stdout, and the evaluator orchestrator's broad
  error fallback can then discard usage. Also test process crash/signal paths
  where the Node catch block never gets to serialize its result.

### Pipeline architecture

- The creator's `SKILL.md` describes an interactive, multi-step designer
  workflow. The paid `creator-phase-runner.py` currently feeds a phase prompt to
  a generic `run_shell` agent and relies on post-hoc file validation. Recent
  artifact gates caught a real stale-output false pass in `create-refine`; a
  fresh changeset/report is now required.
- The evaluator already has useful deterministic phase packets, required-input
  checks, output validators, specialized structured/browser runners, phase
  reservations, and Langfuse phase names. Extend these patterns rather than
  passing all of `SKILL.md` to a general shell agent.

## Proposed design

### A. Durable usage/result contract

Create one shared result/event contract for Python and Node phase adapters. At
minimum record:

```json
{
  "run_id": "…",
  "attempt_id": "…",
  "phase": "eval-usability",
  "request_id": "provider response ID or local idempotency key",
  "status": "completed | failed | interrupted | usage_unknown",
  "usage_known": true,
  "input_tokens": 0,
  "output_tokens": 0,
  "cached_input_tokens": 0,
  "cache_write_tokens": 0,
  "reasoning_tokens": 0,
  "estimated_cost_usd": 0,
  "billing_source": "pinned-price-card-estimate",
  "error_category": null
}
```

- Append and flush an idempotent usage event after **each** successful provider
  response and before the next tool call/request. Maintain per-phase totals and
  settle the shared ledger from these events; deduplicate by provider response
  ID/local request ID.
- Use `null`/`usage_unknown` when a request may have been billed but no usage
  response arrived. Never coerce unavailable usage to zero. Keep the budget
  reservation active until reconciliation.
- Ensure all exception types carry partial usage, turn count, known/unknown
  state, and error class. Explicit HTTP rejections can report known usage from
  completed prior turns; network timeout/child-process crash may be
  usage-unknown for the in-flight request.
- Persist a sidecar usage journal for the Node persona child process so Python
  can recover known usage even if Node exits before writing its final JSON
  envelope.

### B. Responses API state correctness

- Add request-contract tests for every multi-turn path. Every function call
  returned by the API must receive exactly one matching `function_call_output`,
  including scope-denied, timeout, and tool-start failures.
- Choose and document one conversation mode per adapter:
  - **Stateless replay:** `store: false`, no `previous_response_id`, replay all
    required response items and function outputs; or
  - **Stored chain:** use `previous_response_id` only when the previous response
    is actually stored and accessible.
- Do not combine contradictory state modes. Verify provider error behavior with
  mocked HTTP responses and a no-paid live preflight, not a full expensive run.

### C. Pipeline runner boundaries

- Keep `SKILL.md` as the designer-facing procedure and source of truth; do not
  ask a generic agent to search the repo and rediscover that procedure on every
  paid call.
- Convert each paid phase into a narrow adapter with a compact, staged context
  packet, strict input/output schema, explicit writable paths, and named
  actions. Host code should own file listing, path validation, schema checking,
  consistency checks, and artifact manifests.
- Creator phases:
  - `create-plan`: structured user-stories/journeys/scenarios response; host
    validates and writes exact files.
  - `create-generate`: provide validated plan artifacts and only required
    product/PatternFly references; output allowed prototype files/metadata.
  - `create-refine`: provide the current consistency report and bounded target
    files; require refreshed `changeset.md` and fresh validation output.
- Evaluator phases: preserve deterministic Phase A and existing phase packets;
  keep browser personas on browser-only functions and make report/fix tools
  explicit. Do not give persona agents shell or source-tree exploration.
- Replace broad `run_shell` exploration with purpose-built read/write/validate
  tools. If shell remains for a phase, allowlist commands/paths and set tool
  call, output-byte, timeout, and phase-token ceilings. Persist diagnostics
  without silently truncating away why a tool was denied.
- Derive round/tool limits from successful fixtures and artifact completion;
  keep a hard ceiling as a safety stop, but account usage on the limit path.
  A limit is a failed/incomplete phase, never a zero-cost phase.

### D. Langfuse content capture and trace tree

- Introduce an explicit `trace_content` policy independent of host/IDE bridge
  context. For controlled cost/quality benchmark runs, use **full content** by
  default as requested: model inputs, outputs, tool calls/results, generated
  artifacts, and usability evidence. Keep a metadata-only option for unrelated
  runs, but do not silently fall back to it for the benchmark path.
- Redact credentials before persistence; add fixtures proving API keys,
  bearer tokens, cookies, and secret environment values never enter Langfuse.
  Do not redact ordinary Jira criteria, Figma URLs, prompts, or prototype code
  in the explicitly full benchmark profile.
- Use one root trace per full run, one pipeline span, ordered phase generations,
  child tool-call observations, per-request usage/cost observations, artifact
  observations, and a final run summary. Make deterministic and paid phases
  visible in the same tree. Each record carries run/attempt ID, phase order,
  component, skill revision/config hash, model, comparison ID, status, and
  artifact links.
- The interactive estimate/approval flow currently invokes phases in separate
  CLI processes. Test the Langfuse SDK's persisted parent-span context. Prefer a
  single long-lived orchestrator that pauses for approval; otherwise persist a
  root/parent observation ID and reattach subsequent invocations as child spans.
  Verify the result through the Langfuse read API: one trace ID and one coherent
  root, not multiple unrelated roots that merely share tags.
- Attach full outputs or accessible artifact links to Langfuse. The current
  content-free file-URI/hash manifest is useful provenance, but does not satisfy
  the requested full-content experiment on its own.

### E. Skill-effectiveness measurement

Record, per phase and full run:

- repository SHA, skill-file SHA, runner version, routing/config hash, prompt
  template hash, input artifact hashes, model/provider, run mode, trace profile,
  phase attempts and retries;
- API request count, tool calls/failures, rounds, duration, input/output/cache/
  reasoning tokens, estimated cost, reservation/settlement, and unknown usage;
- artifact validation, schema/consistency outcomes, acceptance-criteria
  coverage, persona task completion, and whether outputs were fresh;
- Langfuse trace ID/link and local/hosted artifact links.

Keep direct API costs separate from OpenCode/Codex orchestration-session costs.
Label price-card estimates as estimates, not invoices.

## Ordered work plan

### Work package 0 — inspect and reproduce without paid calls

1. Read current `git status`, targeted diffs, all runner code, and the relevant
   Langfuse/privacy docs. Preserve the dirty worktree.
2. Add deterministic failure fixtures: exception after response 1/2, HTTP 400
   after previous successful turns, Node child crash, invalid stdout JSON,
   timeout, turn/tool limit, missing function-call output, and process kill after
   journal append.
3. Confirm current code facts above. In particular, test `store: false` and
   `previous_response_id` separately and record the exact failing payload.

### Work package 1 — make usage impossible to lose

1. Add the shared result/event schema and durable per-response usage journal.
2. Refactor Python and Node adapters to return/write partial usage on every
   failure path.
3. Change evaluator error fallbacks so they settle known usage, represent
   unknown usage explicitly, and retain reservations instead of setting cost
   to zero.
4. Add tests that fail each phase at every turn and assert ledger/Langfuse
   never reports zero when usage was received.

### Work package 2 — correct API conversation handling

1. Implement the selected stateless or stored-chain request mode consistently.
2. Guarantee a matching output for every tool call, even if tool execution
   fails.
3. Test multi-tool response batches, `store: false`, continuation requests,
   provider 4xx responses, and interrupted child-process output recovery.

### Work package 3 — replace prose-driven runtime behavior

1. Define small phase input/output schemas and deterministic packet builders for
   create and evaluate.
2. Move file reads/writes, source staging, schema validation, consistency
   execution, and manifest generation into host code.
3. Restrict model tools by phase and expose only the required source excerpts
   and writable files. Keep token, output-byte, tool-call, wall-time, and dollar
   bounds enforced in the runner.
4. Keep the human skill flows intact as onboarding/reference docs, then update
   them to delegate to these phase adapters instead of duplicating runner logic.

### Work package 4 — full-content Langfuse and unified run tree

1. Implement the explicit full/sanitized/metadata content profile and secret
   redaction tests.
2. Use one root trace across create/evaluate phases and child observations for
   request rounds, tool I/O, artifacts, and outputs.
3. Store full benchmark artifacts or stable accessible links alongside hashes
   and usage records; verify Jira/Figma/prototype content appears only for the
   explicit full-content run profile.
4. Update `docs/cost-experiments/end-to-end-observability-plan.md` and related
   runner docs so they no longer incorrectly promise metadata-only behavior for
   the requested benchmark profile.

### Work package 5 — controlled validation

1. Run all unit, schema, privacy-redaction, process-crash, and trace-tree tests
   without provider calls.
2. Run a mock end-to-end creator and evaluator pass and inspect serialized
   Langfuse events through the read API.
3. Present the exact zero-spend estimate and proposed full-content trace scope.
   Do **not** run a paid full trace until the user explicitly approves it.
4. After approval, run one small canary per project, reconcile provider usage,
   inspect artifacts/quality, then adjust phase bounds from measured successful
   runs rather than guessing.

## Acceptance criteria

- No caught exception path turns received provider usage into empty usage or
  `$0`; unknown in-flight usage is explicit and retains its reservation.
- A forced failure after N successful responses yields the sum of those N
  responses in the event journal, local ledger, and Langfuse.
- Every Responses API function call is answered exactly once; request state
  mode is tested and documented.
- Full benchmark mode records the requested input/output/tool/artifact evidence
  in the correct project, with credentials redacted and no silent metadata-only
  downgrade.
- A run has one stable trace root and all creator/evaluator phase, tool,
  artifact, and cost observations are queryable beneath it.
- Phase execution is driven by deterministic inputs, tools, and schemas; the
  model cannot spend most of its budget exploring unrelated repository files.
- Test suite proves output freshness and schema validation, not just file
  existence.
- No paid experiment is launched by the new agent without explicit user
  approval.

## Copy/paste kickoff prompt for the new Codex agent

> Read `docs/cost-experiments/codex-handoff-creator-evaluator-reliability.md`
> completely. Inspect `git status --short --branch` and targeted diffs before
> editing; this checkout has existing user work, so do not reset, clean, stage,
> or commit it. First perform Work Package 0 and report verified root causes
> with file paths and tests. Then implement Work Packages 1–4 in small tested
> increments across the canonical creator and evaluator paths. The user wants
> full-content Langfuse tracing for controlled benchmark runs; preserve secret
> redaction, but do not silently reduce raw benchmark I/O to metadata-only.
> Keep creator/evaluator projects and budgets separate. Use deterministic
> runners and explicit artifact contracts rather than feeding whole prose
> skills to open-ended shell agents. Add mock tests for every failure path and
> for one-root trace continuity across phases. Do not launch paid model calls
> or a complete trace; stop after offline tests and present the exact canary
> estimate and what content will be uploaded for approval.

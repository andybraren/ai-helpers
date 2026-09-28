# End-to-end observability plan — 3 MR corpus

**Status:** Draft for review  
**Corpus:** RHAISTRAT-1492 (MR 170), RHAISTRAT-1527 (MR 168), RHAISTRAT-133 (MR 169)  
**Tied to:** Langfuse hybrid plan CP0–CP5, success gate ≥40% `llm_cost_usd` reduction with no quality regression

---

## 1. Goals (unchanged from project start)

| Goal | How we prove it |
|------|-----------------|
| See **full pipeline cost** per run | `cost-ledger.jsonl` + Langfuse trace totals |
| See **tokens/cost by phase** (not one blob) | Langfuse child spans per `eval-*` phase + generation observations |
| See **artifact generation cost** (non-LLM) | Langfuse events: `render-report.js`, `playwright-run`, `validate-artifact-schemas` with `duration_ms` + `output_bytes`, `llm_cost_usd: 0` |
| Compare **CLI vs Cursor** runs | `invocation: cli \| cursor` on every trace |
| Run **3 MRs** with same dimensions | Repeat golden + matrix per key |
| **Cheaper models** without breaking AC/usability | Subskill probes → full pipeline only after per-phase sign-off |
| **Cursor thought process** for review | Phase spans + optional transcript link (metadata only) |

**Trace content:** controlled runs that set a benchmark name, comparison ID, or
condition default to `trace_content=full`. Langfuse receives complete model
inputs and outputs, tool requests/results, generated artifacts, screenshots,
and usability evidence after credential redaction. Full mode stops before model
invocation if Langfuse is unavailable; it does not fall back to metadata-only.
Use `--trace-content metadata` for unrelated runs that should not upload content.
The creator and evaluator keep separate Langfuse projects. Each has one
project-local trace tree, correlated by the same stable `eval_run_id` / trace ID;
Langfuse does not provide one cross-project trace object.

### Prototype creator pricing

The canonical creator lives at
`plugins/uxd-prototype/skills/uxd-prototype-create`. Its measured OpenAI path
uses `scripts/creator-phase-runner.py` and `config/model-routing.json`:

| Phase | Default model | Bound | Trace data |
|-------|---------------|-------|------------|
| `create-plan` | `gpt-6-sol` | 500K input / 20K output tokens; 48 tool calls; 1.5 MB output | usage, cache buckets, estimated cost, full phase inputs/outputs, artifact validation |
| `create-generate` | `gpt-6-sol` | 1.6M input / 64K output tokens; 120 tool calls; 8 MB output | same, plus source artifacts and consistency results |
| `create-refine` | `gpt-6-sol` | 500K input / 24K output tokens; 64 tool calls; 4 MB output | same, plus refreshed changeset and validation results |

Creator phases use the separate `$15` ledger and require estimate-only followed
by explicit approval. `gpt-6-luna` is the configured judge. These estimates use
the pinned OpenAI price card, not an invoice. The deterministic create-serve
bridge is zero LLM cost. OpenCode orchestration generations are separate from
the direct phase ledger and must be counted separately when pricing a manual
session.

---

## 2. What to track (data model)

### 2.1 Run envelope (one per `/eval-iterate` or `/uxd-prototype-evaluate`)

| Field | Source | Langfuse | Ledger |
|-------|--------|----------|--------|
| `eval_run_id` | `eval-state.yaml` | `trace_id` (derived hash) + metadata | row key |
| `prototype_key` | CLI arg | metadata | ✓ |
| `experiment` | e.g. `golden-a-opus-nofix`, `matrix-f-nf` | metadata | ✓ |
| `run_mode` | `fresh` \| `incremental` | metadata | ✓ |
| `fix_mode` | `no_fix` \| `iterate` | metadata | ✓ |
| `model_tier` | premium / standard / budget | metadata | ✓ |
| `invocation` | `cli` \| `cursor` | metadata | ✓ |
| `iterate_flags` | raw flags string | metadata | ✓ |
| `llm_cost_usd` | CLI stream-json | root span + scores | `totals.llm_cost_usd` |
| `observability_cost_usd` | env estimate | metadata | `totals.observability_cost_usd` |
| `langfuse_trace_url` | SDK | — | ✓ |
| `mlflow_run_id` | pipeline | tag (optional) | ✓ |

### 2.2 Phase layer (orchestrator steps)

Each phase is a **generation observation** under the run's pipeline span. The
trace stores complete phase input/output and request/response/tool exchanges in
full benchmark mode. Tool functions are scoped per phase; the evaluator fix
runner can write only the fix log and suggestion-target files. Deterministic
steps remain events under the same run tree.

| Phase | Default model | Track |
|-------|---------------|-------|
| `eval-extract` | Sonnet | input/output tokens, `llm_cost_usd`, duration |
| `eval-classify` | Sonnet | same |
| `eval-consistency-source` | Opus | same |
| `eval-journey` | Opus | same + `playwright-run` event |
| `eval-fix` | Opus | same (iterate only) |
| `eval-consistency-visual` | Opus | same |
| `eval-usability` | Opus | same + persona id hash |
| `eval-report` | Sonnet | same |
| `render-report.js` | — | **event:** `duration_ms`, `output_bytes`, cost 0 |
| `validate-artifact-schemas` | — | **event:** pass/fail counts |
| `playwright-run` | — | **event:** duration, screenshot count |

**Historical note:** MLflow observability was retired in favor of Langfuse. The
current pipeline records per-phase Langfuse observations.

### 2.3 Quality layer (for cost/quality tradeoffs)

| Metric | Langfuse | Evaluator source |
|--------|----------|------------------|
| `ac_pass_rate` | score on trace | eval-journey |
| `ac_fail` / `ac_flagged` | metadata | ledger from artifacts |
| `usability_score` | score | eval-usability |
| `golden_verdict` | metadata | human sign-off |

### 2.4 Cursor “thought process” (what we can and cannot store)

| Capturable in Langfuse | Not stored |
|------------------------|------------|
| Phase timestamps, prompts, model outputs, and tool exchanges in a consented full benchmark | Hidden model reasoning |
| Jira criteria, prototype source/output, screenshots, and usability evidence after credential redaction | API keys, bearer tokens, cookies, and other detected credentials |
| Run/attempt IDs, phase order, status, usage, cost estimate, and artifact hashes | Direct provider credentials or request authorization headers |

Non-benchmark sessions stay metadata-only unless their trace-content policy is
explicitly changed. Full benchmark mode records product and evaluation content,
not hidden model reasoning or credential headers.

---

## 3. How it is tracked (by path)

```mermaid
flowchart TB
  subgraph run [One eval_run_id]
    ROOT[Langfuse root: eval-iterate/KEY]
    ROOT --> P1[eval-extract generation]
    ROOT --> P2[eval-journey generation]
    ROOT --> P3[eval-usability generation]
    ROOT --> E1[render-report.js event]
    ROOT --> E2[playwright-run event]
  end
  ROOT --> LEDGER[cost-ledger.jsonl]
  CURSOR[Cursor /eval-iterate] -->|phase start/end| ROOT
  CLI[claude --print pipeline] -->|stream-json + dual-write| ROOT
```

### Path A — CLI (authoritative $)

```bash
eval "$(make langfuse-local-env)"
make langfuse-pipeline KEY=RHAISTRAT-1492 URL=http://localhost:9000 \
  ITERATE_FLAGS="--fresh --no-fix --max-iterations=1" EXPERIMENT=golden-a-opus-nofix
```

- **Cost authority:** `claude --print` stream-json → `llm_cost_usd`
- **Langfuse:** `langfuse-trace-pipeline.py` → `langfuse_trace.log_pipeline_run`
- **Ledger:** `log-cost-ledger.js` appended per run

### Path B — Cursor (authoritative workflow, coarse $)

Orchestrator follows `orchestration.md`:

```bash
python3 scripts/langfuse_trace.py phase \
  --artifacts-dir "$ARTIFACTS_DIR" --phase eval-journey --action start
# ... run phase ...
python3 scripts/langfuse_trace.py phase \
  --artifacts-dir "$ARTIFACTS_DIR" --phase eval-journey --action end --duration-ms N
```

- Same `eval_run_id` in `eval-state.yaml` before any phase
- `invocation: cursor` on all spans
- No per-token $ unless user runs subskill via CLI compare

### Path C — Langfuse Cursor plugin (review, not ingest)

After runs:

```bash
eval "$(make langfuse-local-env)"
npx langfuse-cli api observations list --limit 50 --json
```

In Cursor chat: *"Use Langfuse skill — compare matrix-f-it vs matrix-i-it by metadata.run_mode"*

---

## 4. Implementation phases (work remaining)

### CP-E2E-1 — Per-phase CLI instrumentation (highest value)

**Problem:** Pipeline trace collapses to one generation; can't see journey vs usability cost.

**Fix:**

1. After each Task/subskill in orchestrator, parse subskill `run_result` or stream capture → `langfuse_trace.py log-pipeline` phase entry
2. Run controlled Langfuse benchmark conditions one phase at a time.
3. Extend `_build_phases_from_usage` to read per-phase token files if subskills write them

**Verify:** Langfuse trace shows ≥8 named children for a full no-fix run.

### CP-E2E-2 — Three-MR rollout

| MR | Golden A/B | Matrix 4-cell | When |
|----|------------|---------------|------|
| RHAISTRAT-1492 | ✓ done | ✓ done | now |
| RHAISTRAT-1527 | pending | pending | after CP-E2E-1 on 1492 |
| RHAISTRAT-133 | pending | pending | after 1527 |

Requires artifacts/workspace per key (clone + `npm run start:dev` or shared URL strategy).

### CP-E2E-3 — Cursor transcript linking

1. On pipeline start: write `eval-state.yaml` field `cursor_session_id` or transcript path
2. Langfuse root metadata: `cursor_transcript_ref` (hash or file path)
3. Document: open transcript in Cursor for reasoning; Langfuse for cost timeline

### CP-E2E-4 — Dashboards (Langfuse UI)

Build saved views / filters:

- Cost by `metadata.experiment`
- Cost by `metadata.run_mode` × `metadata.fix_mode`
- Cost by phase name (generation children)
- Artifact bytes: sum `output_bytes` on `render-report.js` events

---

## 5. Should we test individual subskills?

**Yes — do this before more full-pipeline Opus runs.** Aligns with Phase 4 and cursor-efficiency (isolate variables).

| Approach | Command | Purpose |
|----------|---------|---------|
| **Fixture tests** | `make test-subskills KEY=RHAISTRAT-1492` | Schema/contract, no $ |
| **Single-skill LLM probe** | Controlled Langfuse benchmark phase | Cost + quality for one phase |
| **Recommended matrix** | extract, classify → Haiku/Sonnet; journey, usability → Sonnet/Opus | Find downgrade candidates |

**Order:**

1. Subskill probes on **RHAISTRAT-1492** only (cheapest signal)
2. Promote winning model per phase to full pipeline
3. Re-run golden on all 3 MRs only after ≥40% savings hypothesis holds on 1492

**Do not** change model + run_mode in the same experiment day.

---

## 6. Review checklist (for you)

After each corpus key:

- [ ] Root trace in Langfuse with correct `eval_run_id`, `run_mode`, `fix_mode`
- [ ] Ledger row matches trace URL
- [ ] Per-phase costs visible (or documented gap)
- [ ] `render-report.js` shows `output_bytes` (artifact size trend)
- [ ] Langfuse quality scores ≥ golden quality bar
- [ ] Cursor run: phase spans present if invoked from IDE

**Local UI:** http://localhost:3000/project/uxd-eval-local/traces  
**Review guide:** [langfuse-benchmark-review.md](langfuse-benchmark-review.md)

---

## 7. Immediate next actions

1. **You:** Review benchmark traces in Langfuse (4 matrix + 2 golden)
2. **Implement CP-E2E-1:** per-phase Langfuse children from orchestrator
3. **Run subskill matrix** after zero-spend Langfuse preflight and explicit approval.
4. **Golden on RHAISTRAT-1527** once artifacts exist
5. **Defer cluster Langfuse** until local E2E model is stable

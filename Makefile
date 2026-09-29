.PHONY: validate lint security scaffold help docs cluster-env \
	langfuse-env langfuse-smoke langfuse-deps langfuse-eval langfuse-pipeline eval-onboard \
	langfuse-verify langfuse-preflight langfuse-cost-estimate \
	test-subskills backfill-ledger

cluster-env: ## Print export PATH for oc/node (eval "$(make cluster-env)")
	@echo 'export PATH="$(CURDIR)/.local/node/bin:$$PATH"'

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

validate: ## Run manifest and doc validation (same as CI)
	@bash scripts/validate-manifests.sh
	@bash scripts/validate-skills.sh
	@bash scripts/generate-plugins-md.sh
	@echo "Checking generated docs are up to date..."
	@if ! git diff --quiet PLUGINS.md README.md CONTRIBUTING-SKILLS.md \
		plugins/*/README.md plugins/*/*/README.md 2>/dev/null; then \
		echo "Error: Generated docs are out of date. Run 'make docs' and commit the result."; \
		exit 1; \
	fi

lint: ## Run skillsaw content linter (zero-install via uvx)
	@command -v uvx >/dev/null 2>&1 || { \
		echo "Error: uvx not found. Install uv: https://docs.astral.sh/uv/getting-started/installation/"; \
		exit 1; \
	}
	@echo "Running skillsaw..."
	@uvx skillsaw lint .

security: ## Run AI Guardian security scan (zero-install via uvx)
	@command -v uvx >/dev/null 2>&1 || { \
		echo "Error: uvx not found. Install uv: https://docs.astral.sh/uv/getting-started/installation/"; \
		exit 1; \
	}
	@echo "Running AI Guardian..."
	@uvx ai-guardian scan plugins/ --exclude '**/eval/cases/**'

docs: ## Regenerate PLUGINS.md, README plugin table, and CONTRIBUTING-SKILLS.md
	@bash scripts/generate-plugins-md.sh

scaffold: ## Scaffold a new skill: make scaffold PLUGIN=pf-react SKILL=pf-my-skill
ifndef PLUGIN
	$(error PLUGIN is required. Usage: make scaffold PLUGIN=pf-react SKILL=pf-my-skill)
endif
ifndef SKILL
	$(error SKILL is required. Usage: make scaffold PLUGIN=pf-react SKILL=pf-my-skill)
endif
	@bash scripts/scaffold-skill.sh $(PLUGIN) $(SKILL)

# ── Eval Pipeline ───────────────────────────────────────────────────
EVAL_SKILL = plugins/uxd-workshop/skills/uxd-prototype-evaluate
EVAL_SCRIPTS = $(EVAL_SKILL)/scripts
EVAL_TESTS = $(EVAL_SKILL)/tests
LANGFUSE_POC7_URI = https://langfuse-ux-eval.apps.rosa.uxdpoc7.9hji.p3.openshiftapps.com
PYTHON_RUN = $(if $(wildcard .venv/bin/python),.venv/bin/python,$(if $(shell command -v uv 2>/dev/null),uv run python3,python3))
EVAL_RUN = bash scripts/eval-run.sh

KEY ?=
URL ?=
SCORERS ?= pipeline-output
MODEL ?=
SKILLS ?=
EVAL_PROVIDER ?=
EVAL_PLATFORM ?=
MAX_TURNS ?=
EVAL_ONBOARD_ARGS ?=

langfuse-eval: ## Score eval artifacts locally and log quality to Langfuse
	@if [ -z "$(KEY)" ]; then echo "Usage: make langfuse-eval KEY=RHAISTRAT-1492"; exit 1; fi
	@if [ -d .artifacts/$(KEY)/eval ]; then ARTIFACTS=.artifacts/$(KEY)/eval; \
	elif [ -d .artifacts/$(KEY) ]; then ARTIFACTS=.artifacts/$(KEY); \
	else echo "Missing .artifacts/$(KEY) or .artifacts/$(KEY)/eval"; exit 1; fi; \
	$(EVAL_RUN) $(PYTHON_RUN) $(EVAL_SCRIPTS)/langfuse-eval.py \
		$$ARTIFACTS \
		--model $(if $(MODEL),$(MODEL),unknown) \
		--prototype-key $(KEY) \
		--scorers $(SCORERS)

langfuse-pipeline: ## MCP-staged direct API pipeline with Langfuse
	@if [ -z "$(KEY)" ] || [ -z "$(URL)" ] || [ -z "$(WORKSPACE)" ] || [ -z "$(JIRA_CONTEXT)" ]; then \
		echo "Usage: make langfuse-pipeline KEY=RHAISTRAT-1492 URL=http://127.0.0.1:3000 WORKSPACE=/path/to/prototype JIRA_CONTEXT=tmp/benchmarks/RHAISTRAT-1492/jira-context.json"; exit 1; fi
	$(EVAL_RUN) $(PYTHON_RUN) $(EVAL_SCRIPTS)/langfuse-trace-pipeline.py \
		--key $(KEY) --url $(URL) --workspace $(WORKSPACE) --jira-context $(JIRA_CONTEXT) \
		$(if $(BENCHMARK_DIR),--benchmark-dir $(BENCHMARK_DIR),) \
		$(if $(PREFLIGHT_ONLY),--preflight-only,) \
		$(if $(DETERMINISTIC_ONLY),--deterministic-only,) \
		$(if $(PHASE_PLAN_ONLY),--phase-plan-only,) \
		$(if $(BASE_REF),--base-ref $(BASE_REF),) \
		$(if $(ALL_FILES),--all-files,) \
		$(if $(MODEL),--model $(MODEL),) \
		$(if $(EVAL_PROVIDER),--provider $(EVAL_PROVIDER),) \
		$(if $(EVAL_PLATFORM),--platform $(EVAL_PLATFORM),) \
		$(if $(MAX_TURNS),--max-turns $(MAX_TURNS),) \
		$(if $(ITERATE_FLAGS),--iterate-flags="$(ITERATE_FLAGS)",) \
		$(if $(EXPERIMENT),--experiment-label="$(EXPERIMENT)",) \
		$(if $(BENCHMARK_NAME),--benchmark-name "$(BENCHMARK_NAME)",) \
		$(if $(CONDITION),--condition $(CONDITION),) \
		$(if $(SCREENSHOT_MODE),--screenshot-mode $(SCREENSHOT_MODE),) \
		$(if $(ARTIFACT_MODE),--artifact-mode $(ARTIFACT_MODE),) \
		$(if $(CSV_USED),--csv-used $(CSV_USED),) \
		$(if $(REASONING_EFFORT),--reasoning-effort $(REASONING_EFFORT),) \
		$(if $(ESTIMATE_ONLY),--estimate-only,) \
		$(if $(APPROVE_ESTIMATE),--approve-estimate,) \
		$(if $(SOURCE_REVISION),--source-revision $(SOURCE_REVISION),) \
		$(if $(PERSONAS),--personas $(PERSONAS),) \
		$(foreach state,$(CANONICAL_STATES),--canonical-state $(state)) \
		$(foreach workspace,$(CONDITION_WORKSPACES),--condition-workspace $(workspace)) \
		$(if $(WARM_CACHE_ROOT),--warm-cache-root $(WARM_CACHE_ROOT),) \
		$(if $(PAIRED_COLD_STATE),--paired-cold-state $(PAIRED_COLD_STATE),) \
		$(if $(ENV_FILE),--env-file $(ENV_FILE),) \
		$(if $(TRACE_SANITIZED_ARTIFACTS),--trace-sanitized-artifacts,)

langfuse-env: ## Export Langfuse env for UXDPOC7 (eval "$(make langfuse-env)")
	@echo 'export LANGFUSE_HOST=$(LANGFUSE_POC7_URI)'
	@echo 'export LANGFUSE_ENABLED=1'
	@echo 'export LANGFUSE_OBS_COST_PER_RUN=0.05'
	@echo '# Set keys from Langfuse UI (not committed):'
	@echo '# export LANGFUSE_PUBLIC_KEY=pk-lf-...'
	@echo '# export LANGFUSE_SECRET_KEY=sk-lf-...'

langfuse-deps: ## Install Python deps for Langfuse SDK (creates .venv)
	@python3 -m venv .venv
	@.venv/bin/pip install -q langfuse
	@echo "Use: source .venv/bin/activate  (or make langfuse-smoke uses .venv automatically)"

eval-onboard: ## Read-only first-run setup check for prototype evaluation
	@bash scripts/eval-onboard.sh $(EVAL_ONBOARD_ARGS)

langfuse-smoke: ## Langfuse SDK smoke trace (dry-run if keys unset)
	$(EVAL_RUN) $(PYTHON_RUN) $(EVAL_SCRIPTS)/langfuse_trace.py smoke

langfuse-verify: ## Verify Langfuse health/auth and emit a metadata-only smoke trace
	$(EVAL_RUN) $(PYTHON_RUN) $(EVAL_SCRIPTS)/verify-langfuse.py

langfuse-preflight: ## Zero-spend benchmark preflight; requires BENCHMARK_PREFLIGHT_ARGS
	@if [ -z "$(BENCHMARK_PREFLIGHT_ARGS)" ]; then echo "Usage: make langfuse-preflight BENCHMARK_PREFLIGHT_ARGS='--key ... --url ... --workspace ... --jira-context ... --source-revision ... --personas ... --canonical-state legacy=... --canonical-state optimized-cold=... --canonical-state optimized-warm=... --condition-workspace legacy=... --condition-workspace optimized-cold=... --condition-workspace optimized-warm=...'"; exit 1; fi
	$(EVAL_RUN) $(PYTHON_RUN) $(EVAL_SCRIPTS)/verify-langfuse.py --preflight $(BENCHMARK_PREFLIGHT_ARGS)

langfuse-cost-estimate: ## Zero-spend pre-run cost estimate from Langfuse trace history (KEY required)
	@if [ -z "$(KEY)" ]; then echo "Usage: make langfuse-cost-estimate KEY=RHAISTRAT-1492 [RUN_MODE=fresh] [FIX_MODE=no_fix] [MODEL_TIER=premium] [ITERATIONS=1] [LIMIT_DAYS=90] [CONFIG=...] [BUDGET_USD=...] [JSON=1]"; exit 1; fi
	$(EVAL_RUN) $(PYTHON_RUN) $(EVAL_SCRIPTS)/langfuse-cost-estimate.py \
		--key $(KEY) \
		$(if $(RUN_MODE),--run-mode $(RUN_MODE),) \
		$(if $(FIX_MODE),--fix-mode $(FIX_MODE),) \
		$(if $(MODEL_TIER),--model-tier $(MODEL_TIER),) \
		$(if $(ITERATIONS),--iterations $(ITERATIONS),) \
		$(if $(LIMIT_DAYS),--limit-days $(LIMIT_DAYS),) \
		$(if $(CONFIG),--config $(CONFIG),) \
		$(if $(BUDGET_USD),--budget-usd $(BUDGET_USD),) \
		$(if $(JSON),--json,)

backfill-ledger: ## Backfill cost ledger from existing artifacts
	@python3 scripts/backfill-cost-ledger.py

test-subskills: ## Run subskill validation tests against fixtures
	bash $(EVAL_TESTS)/run-script-tests.sh
	bash plugins/uxd-prototype/skills/uxd-prototype-create/tests/run-tests.sh

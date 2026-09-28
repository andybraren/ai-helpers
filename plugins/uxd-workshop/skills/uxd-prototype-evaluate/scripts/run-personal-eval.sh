#!/usr/bin/env bash
# Run one designer-style evaluator session with Langfuse tracking enabled.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../.." && pwd)"
PYTHON="${REPO_ROOT}/.venv/bin/python"

if [[ ! -x "${PYTHON}" ]]; then
  echo "Missing ${PYTHON}. Run: make langfuse-deps" >&2
  exit 2
fi

if [[ "$#" -lt 3 ]]; then
  echo "Usage: $0 <JIRA_KEY> <PROTOTYPE_URL> <WORKSPACE> [extra pipeline flags]" >&2
  exit 2
fi

KEY="$1"
URL="$2"
WORKSPACE="$3"
shift 3
BENCHMARK_DIR="${REPO_ROOT}/tmp/personal-runs/${KEY}"
JIRA_CONTEXT="${BENCHMARK_DIR}/jira-context.json"

if [[ ! -f "${JIRA_CONTEXT}" ]]; then
  echo "Missing ${JIRA_CONTEXT}; stage Jira context before running." >&2
  exit 2
fi

# Link the designer run to the cluster-side Qwen LLM-as-a-judge. The
# prototype-evaluator project's evaluation rule is scoped to
# benchmark_name=designer-phase-costs + privacy_mode:sanitized_artifact_output,
# so we pin that benchmark name and opt into sanitized (scored) outputs.
# Set UXD_EVAL_NO_QWEN_JUDGE=1 to run the designer path without the judge.
QWEN_JUDGE_FLAGS=()
if [[ "${UXD_EVAL_NO_QWEN_JUDGE:-0}" != "1" ]]; then
  QWEN_JUDGE_FLAGS=(
    --qwen-quality-judge
    --benchmark-name "${UXD_EVAL_BENCHMARK_NAME:-designer-phase-costs}"
  )
fi

exec "${REPO_ROOT}/scripts/eval-run.sh" "${PYTHON}" "${SCRIPT_DIR}/langfuse-trace-pipeline.py" \
  --personal-run \
  --key "${KEY}" \
  --url "${URL}" \
  --workspace "${WORKSPACE}" \
  --jira-context "${JIRA_CONTEXT}" \
  --benchmark-dir "${BENCHMARK_DIR}" \
  --env-file "${REPO_ROOT}/.env.local" \
  --trace-sanitized-artifacts \
  --iterate-flags="--max-iterations=1" \
  ${QWEN_JUDGE_FLAGS[@]+"${QWEN_JUDGE_FLAGS[@]}"} \
  "$@"

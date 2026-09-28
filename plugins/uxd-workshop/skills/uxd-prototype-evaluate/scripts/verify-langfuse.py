#!/usr/bin/env python3
"""Verify Langfuse endpoint/auth and emit one metadata-only smoke trace."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import base64
import hashlib
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import langfuse_trace  # noqa: E402
from jira_context import load_jira_context  # noqa: E402
from model_routing import route_for  # noqa: E402


CANONICAL_FILES = ("brief.json", "evaluation.json", "evidence.json", "actions.json", "state.json")
QWEN_CONNECTION = "Qwen3.8"
QWEN_MODEL = "Qwen3.8-27B"
QWEN_EVALUATOR_NAME = "uxd-prototype-quality-qwen-v1"
QWEN_SCORE_NAMES = "uxd-prototype-quality-qwen-v1"
OPENAI_PHASE_MODELS = {
    phase: route_for(phase, "api")["model"]
    for phase in ("eval-journey", "eval-fix", "eval-consistency-visual", "eval-heuristic", "eval-usability")
}


def load_qwen_rubric() -> dict[str, str]:
    """Read pinned judge identity from versioned config without a YAML runtime dependency."""
    path = Path(__file__).resolve().parent.parent / "config" / "qwen-quality-rubric.yaml"
    try:
        fields = {}
        for line in path.read_text().splitlines():
            match = re.fullmatch(r"(version|connection|model):\s*([^#\s]+)", line.strip())
            if match:
                fields[match.group(1)] = match.group(2)
    except OSError as error:
        raise RuntimeError(f"Qwen quality rubric is unavailable: {path}") from error
    if fields.get("connection") != QWEN_CONNECTION or fields.get("model") != QWEN_MODEL:
        raise RuntimeError("Qwen quality rubric does not pin Qwen3.8 / Qwen3.8-27B")
    if not fields.get("version"):
        raise RuntimeError("Qwen quality rubric has no version")
    return fields


def check_health(host: str) -> None:
    url = host.rstrip("/") + "/api/public/health"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"health endpoint returned HTTP {response.status}")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"health endpoint returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"cannot reach Langfuse host: {error.reason}") from error


def check_auth(host: str, public_key: str, secret_key: str) -> None:
    """Validate project keys against Langfuse's read-only public API."""
    url = host.rstrip("/") + "/api/public/projects"
    request = urllib.request.Request(
        url,
        headers=_basic_headers(public_key, secret_key),
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"authenticated API returned HTTP {response.status}")
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise RuntimeError("Langfuse project keys were rejected") from error
        raise RuntimeError(f"authenticated API returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"cannot reach authenticated Langfuse API: {error.reason}") from error


def _basic_headers(public_key: str, secret_key: str) -> dict[str, str]:
    token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    return {"Accept": "application/json", "Authorization": f"Basic {token}"}


def _get_json(url: str, headers: dict[str, str], label: str) -> dict:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f"{label} returned HTTP {response.status}")
            payload = json.loads(response.read())
            if not isinstance(payload, dict):
                raise RuntimeError(f"{label} returned a non-object JSON response")
            return payload
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{label} returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"cannot reach {label}: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{label} returned invalid JSON") from error


def check_langfuse_scores_api(host: str, public_key: str, secret_key: str) -> dict[str, str]:
    """Probe score-read API shape with read-only, documented v3 parameters."""
    headers = _basic_headers(public_key, secret_key)
    v2_endpoint = host.rstrip("/") + "/api/public/v2/scores"
    try:
        _get_json(v2_endpoint, headers, "Langfuse Scores API v2")
        v2_status = "available"
    except RuntimeError as error:
        v2_status = str(error)
    now = datetime.now(timezone.utc)
    query = urllib.parse.urlencode({
        "name": QWEN_SCORE_NAMES, "fields": "details,subject", "limit": "1",
        "fromTimestamp": (now - timedelta(minutes=1)).isoformat(),
        "toTimestamp": now.isoformat(),
    })
    v3_endpoint = host.rstrip("/") + "/api/public/v3/scores"
    payload = _get_json(
        f"{v3_endpoint}?{query}", headers, "Langfuse Scores API v3"
    )
    if not isinstance(payload.get("data"), list) or not isinstance(payload.get("meta"), dict):
        raise RuntimeError("Langfuse Scores API v3 returned unexpected data/meta shape")
    filter_value = json.dumps([{
        "type": "string", "column": "id", "operator": "=",
        "value": "__uxd_preflight_read_probe__",
    }], separators=(",", ":"))
    observation_query = urllib.parse.urlencode({
        "filter": filter_value, "fields": "core,basic,metadata,trace_context,usage", "limit": "1",
    })
    observations = _get_json(
        f"{host.rstrip('/')}/api/public/v2/observations?{observation_query}",
        headers, "Langfuse Observations API v2",
    )
    if not isinstance(observations.get("data"), list) or not isinstance(observations.get("meta"), dict):
        raise RuntimeError("Langfuse Observations API v2 returned unexpected data/meta shape")
    return {
        "primary_endpoint": "/api/public/v3/scores",
        "parameters_verified": "scores name,fields,limit,fromTimestamp,toTimestamp; observations filter,fields,limit",
        "v2_endpoint": "/api/public/v2/scores",
        "v2_status": v2_status,
    }


def check_openai_auth(api_key: str, base_url: str | None = None) -> None:
    """Validate OpenAI credentials via the non-inference Models read endpoint."""
    base = (base_url or "https://api.openai.com/v1").rstrip("/")
    if base.endswith("/responses"):
        base = base[: -len("/responses")]
    _get_json(
        f"{base}/models",
        {"Accept": "application/json", "Authorization": f"Bearer {api_key}"},
        "OpenAI Models API",
    )


def check_langfuse_qwen_config(host: str, public_key: str, secret_key: str) -> None:
    """Read Langfuse configuration; this never invokes the Qwen provider."""
    headers = _basic_headers(public_key, secret_key)
    connections = _get_json(
        host.rstrip("/") + "/api/public/llm-connections", headers, "Langfuse LLM connections API"
    )
    models = _get_json(
        host.rstrip("/") + "/api/public/models", headers, "Langfuse Models API"
    )
    serialized_connections = json.dumps(connections, sort_keys=True)
    serialized_models = json.dumps(models, sort_keys=True)
    if QWEN_CONNECTION not in serialized_connections:
        raise RuntimeError(f"Langfuse connection is not configured: {QWEN_CONNECTION}")
    if QWEN_MODEL not in serialized_models:
        raise RuntimeError(f"Langfuse model is not configured: {QWEN_MODEL}")


def check_langfuse_qwen_evaluator(
    host: str, public_key: str, secret_key: str, benchmark_name: str | None
) -> dict[str, str]:
    """Read-only assertion for the cluster-side paid-phase Qwen judge."""
    if not benchmark_name:
        raise RuntimeError("Qwen judge assertion requires --benchmark-name")
    evaluators = _get_json(
        host.rstrip("/") + "/api/public/v2/evaluators",
        _basic_headers(public_key, secret_key),
        "Langfuse evaluators API",
    )
    candidates = (evaluators.get("data") or evaluators.get("evaluators") or [])
    evaluator = next(
        (item for item in candidates if isinstance(item, dict) and item.get("name") == QWEN_EVALUATOR_NAME),
        None,
    )
    if evaluator is None:
        raise RuntimeError(
            f"Langfuse Qwen evaluator is not configured: {QWEN_EVALUATOR_NAME}"
        )
    status = str(evaluator.get("status", "")).lower()
    if evaluator.get("enabled") is not True and status not in {"enabled", "active"}:
        raise RuntimeError(f"Langfuse Qwen evaluator is not enabled: {QWEN_EVALUATOR_NAME}")
    serialized_evaluator = json.dumps(evaluator, sort_keys=True)
    if QWEN_CONNECTION not in serialized_evaluator or QWEN_MODEL not in serialized_evaluator:
        raise RuntimeError("Langfuse Qwen evaluator does not pin the configured connection/model")

    # ponytail: one API page is sufficient for this named judge/rule; upgrade to
    # cursor pagination if a project config grows beyond the default page size.
    rules = _get_json(
        host.rstrip("/") + "/api/public/v2/evaluation-rules",
        _basic_headers(public_key, secret_key),
        "Langfuse evaluation rules API",
    )
    serialized_rules = json.dumps(rules, sort_keys=True)
    paid_phases = ("eval-journey", "eval-fix", "eval-consistency-visual", "eval-heuristic", "eval-usability")
    evaluator_id = str(evaluator.get("id", ""))
    # ponytail: the cluster filter UI silently drops metadata keys no
    # observation has written yet (qwen_quality_judge), so it cannot be a
    # pre-run rule condition. Scoping still holds: only benchmark-tagged
    # runs reach the judge, and the trace writer sets output=None unless
    # privacy_mode is sanitized_artifact_output, so raw content cannot be
    # judged. Upgrade path: re-add the metadata condition once the first
    # benchmark observation exists.
    if (
        not evaluator_id
        or evaluator_id not in serialized_rules
        or f"benchmark_name={benchmark_name}" not in serialized_rules
        or "sanitized_artifact_output" not in serialized_rules
        or any(phase not in serialized_rules for phase in paid_phases)
    ):
        raise RuntimeError(
            "Langfuse Qwen rule must target the named evaluator, all paid phases, "
            "and benchmark_name=<benchmark-name>"
        )
    return {"evaluator_id": evaluator_id, "benchmark_name": benchmark_name}


def load_env_file(env_file: Path | None = None) -> Path | None:
    """Load simple dotenv values without shell evaluation or printing secret values."""
    configured = os.environ.get("UXD_EVAL_ENV_FILE")
    candidate = env_file or (Path(configured) if configured else None)
    if candidate is None:
        candidate = Path(__file__).resolve().parents[5] / ".env.local"
    candidate = candidate.expanduser().resolve()
    if not candidate.is_file():
        return None
    for raw_line in candidate.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        if not separator or not name.replace("_", "").isalnum():
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)
    return candidate


def check_prototype_url(url: str) -> None:
    request = urllib.request.Request(url, headers={"Accept": "text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if not 200 <= response.status < 400:
                raise RuntimeError(f"prototype URL returned HTTP {response.status}")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"prototype URL returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"cannot reach prototype URL: {error.reason}") from error


def workspace_revision(workspace: Path, expected: str) -> str:
    if not workspace.is_dir():
        raise RuntimeError(f"workspace does not exist: {workspace}")
    completed = subprocess.run(
        ["git", "-C", str(workspace), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    actual = completed.stdout.strip()
    if completed.returncode or not actual:
        raise RuntimeError("workspace must be a Git checkout with a checked-out source revision")
    if actual != expected:
        raise RuntimeError(f"workspace revision does not match supplied source revision: {expected}")
    return actual


def _compound_key(identity: dict) -> str:
    keys = ("intent_key", "build_key", "evaluator_key")
    if any(not isinstance(identity.get(key), str) or not identity[key].startswith("sha256:") for key in keys):
        raise RuntimeError("canonical state has an incomplete cache identity")
    encoded = json.dumps({key: identity[key] for key in keys}, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def load_canonical_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text())
        identity = state["identity"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RuntimeError(f"canonical state is invalid: {path}") from error
    compound = _compound_key(identity)
    if identity.get("compound_key") != compound:
        raise RuntimeError("canonical state compound key does not match its identity")
    return {"path": str(path.resolve()), "compound_key": compound, "identity": identity}


def validate_cache_entry(cache_root: Path, state: dict) -> dict:
    entry = cache_root.resolve() / state["compound_key"].split(":", 1)[1]
    manifest_path = entry / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"warm cache manifest is missing or invalid: {manifest_path}") from error
    if manifest.get("compound_key") != state["compound_key"]:
        raise RuntimeError("warm cache manifest compound key does not match preflight state")
    records = {record.get("name"): record for record in manifest.get("files", [])}
    for filename in CANONICAL_FILES:
        record = records.get(filename)
        content_path = entry / filename
        if not record or not content_path.is_file():
            raise RuntimeError(f"warm cache entry is missing {filename}")
        content = content_path.read_bytes()
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        if record.get("bytes") != len(content) or record.get("sha256") != digest:
            raise RuntimeError(f"warm cache manifest checksum fails for {filename}")
    validator = Path(__file__).resolve().parent / "validate-canonical-artifacts.js"
    validated = subprocess.run(
        ["node", str(validator), str(entry), "--json"],
        capture_output=True, text=True, check=False,
    )
    if validated.returncode:
        raise RuntimeError("warm cache entry fails canonical artifact validation")
    return {"cache_root": str(cache_root.resolve()), "entry": str(entry), "manifest": str(manifest_path)}


def validate_condition_workspaces(args, states: dict[str, dict], source_revision: str) -> dict[str, str]:
    """Require one disposable, revision-matched workspace per benchmark condition."""
    workspaces: dict[str, Path] = {}
    for item in getattr(args, "condition_workspace", []) or []:
        condition, separator, raw_path = item.partition("=")
        if not separator or condition not in states or condition in workspaces:
            raise RuntimeError(
                "condition workspaces must use unique CONDITION=PATH entries for every canonical state"
            )
        workspaces[condition] = Path(raw_path).expanduser().resolve()
    if set(workspaces) != set(states):
        raise RuntimeError("one condition workspace is required for legacy, optimized-cold, optimized-warm")
    for condition, workspace in workspaces.items():
        workspace_revision(workspace, source_revision)
        expected_state = workspace / ".artifacts" / args.key / "eval" / "state.json"
        if states[condition]["path"] != str(expected_state.resolve()):
            raise RuntimeError(
                f"{condition} state must be deterministic output in its condition workspace"
            )
    return {condition: str(path) for condition, path in workspaces.items()}


def expected_openai_cost() -> dict:
    phases = []
    for phase, model in OPENAI_PHASE_MODELS.items():
        input_tokens, output_tokens = langfuse_trace.OPENAI_PHASE_BOUNDS[phase]
        phases.append({
            "phase": phase, "model": model, "input_tokens_bound": input_tokens,
            "output_tokens_bound": output_tokens,
            "openai_cost_usd": langfuse_trace.estimated_cost(
                model, input_tokens, output_tokens
            ),
        })
    one_cold_run = round(sum(item["openai_cost_usd"] for item in phases), 6)
    conditions = {
        "calibration": {"repetitions": 1, "openai_cost_usd": one_cold_run},
        "legacy": {"repetitions": 3, "openai_cost_usd": round(one_cold_run * 3, 6)},
        "optimized-cold": {"repetitions": 3, "openai_cost_usd": round(one_cold_run * 3, 6)},
        "optimized-warm": {"repetitions": 3, "openai_cost_usd": 0.0},
    }
    return {
        "phases": phases,
        "conditions": conditions,
        "program_openai_cost_usd": round(sum(item["openai_cost_usd"] for item in conditions.values()), 6),
        "estimate_label": "prior (pre-calibration)",
        "qwen_cost": "unavailable until provider billing data is returned",
        "openai_cap_usd": langfuse_trace.OPENAI_CAP_USD,
    }


def run_preflight(args) -> dict:
    env_path = load_env_file(Path(args.env_file) if args.env_file else None)
    required = ("OPENAI_API_KEY", "LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"missing required environment variables: {', '.join(missing)}")
    workspace = Path(args.workspace).expanduser().resolve()
    context = Path(args.jira_context).expanduser().resolve()
    source_revision = workspace_revision(workspace, args.source_revision)
    load_jira_context(context, args.key)
    personas = [persona.strip() for persona in args.personas.split(",") if persona.strip()]
    if len(personas) != 2 or len(set(personas)) != 2:
        raise RuntimeError("exactly two distinct personas are required")
    qwen_rubric = load_qwen_rubric()
    states = {}
    for item in args.canonical_state:
        condition, separator, raw_path = item.partition("=")
        if not separator or condition not in {"legacy", "optimized-cold", "optimized-warm"}:
            raise RuntimeError("canonical states must use CONDITION=PATH for legacy, optimized-cold, optimized-warm")
        if condition in states:
            raise RuntimeError(f"duplicate canonical state for {condition}")
        states[condition] = load_canonical_state(Path(raw_path).expanduser())
    if set(states) != {"legacy", "optimized-cold", "optimized-warm"}:
        raise RuntimeError("canonical state is required for legacy, optimized-cold, and optimized-warm")
    compound_keys = {item["compound_key"] for item in states.values()}
    if len(compound_keys) != 1:
        raise RuntimeError("benchmark conditions do not share one canonical compound key")
    condition_workspaces = validate_condition_workspaces(args, states, source_revision)
    expected_cost = expected_openai_cost()
    if expected_cost["program_openai_cost_usd"] > expected_cost["openai_cap_usd"]:
        raise RuntimeError(
            "benchmark OpenAI upper-bound estimate "
            f"${expected_cost['program_openai_cost_usd']:.6f} exceeds the "
            f"${expected_cost['openai_cap_usd']:.2f} program cap"
        )
    check_openai_auth(os.environ["OPENAI_API_KEY"], os.environ.get("OPENAI_BASE_URL"))
    host = os.environ["LANGFUSE_HOST"]
    check_health(host)
    check_auth(host, os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])
    # With the judge requested, its evaluator assertion is authoritative for the
    # connection/model pin. Some clusters omit evaluator-bound models from the
    # generic Models catalog, so requiring both creates a false preflight gate.
    if not getattr(args, "qwen_quality_judge", False):
        check_langfuse_qwen_config(
            host, os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"]
        )
    qwen_assertion = None
    score_api = None
    if getattr(args, "qwen_quality_judge", False):
        score_api = check_langfuse_scores_api(
            host, os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"]
        )
        qwen_assertion = check_langfuse_qwen_evaluator(
            host, os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"],
            getattr(args, "benchmark_name", None),
        )
    check_prototype_url(args.url)
    return {
        "status": "ready", "model_invoked": False,
        "environment_file_loaded": bool(env_path),
        "jira_key": args.key, "prototype_url": args.url,
        "workspace": str(workspace), "source_revision": source_revision,
        "personas": personas, "canonical_compound_key": next(iter(compound_keys)),
        "condition_states": {name: {"path": data["path"], "compound_key": data["compound_key"]} for name, data in states.items()},
        "condition_workspaces": condition_workspaces,
        "qwen": {
            **qwen_rubric,
            "evaluator_checked": bool(getattr(args, "qwen_quality_judge", False)),
            "assertion": qwen_assertion,
            "score_api": score_api,
            "provider_inference": "not run",
        },
        "expected_cost": expected_cost,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Langfuse and zero-spend benchmark prerequisites"
    )
    parser.add_argument("--read-only", action="store_true", help="Skip metadata-only smoke trace")
    parser.add_argument("--preflight", action="store_true", help="Run zero-spend benchmark preflight")
    parser.add_argument("--env-file", default=None, help="Secure dotenv file; defaults to primary-worktree .env.local")
    parser.add_argument("--key")
    parser.add_argument("--url")
    parser.add_argument("--workspace")
    parser.add_argument("--jira-context")
    parser.add_argument("--source-revision")
    parser.add_argument("--personas", help="Exactly two comma-separated persona identifiers")
    parser.add_argument(
        "--canonical-state", action="append", default=[], metavar="CONDITION=PATH",
        help="State files for legacy, optimized-cold, optimized-warm",
    )
    parser.add_argument(
        "--condition-workspace", action="append", default=[], metavar="CONDITION=PATH",
        help="Disposable workspace that deterministically produced each canonical state",
    )
    parser.add_argument("--warm-cache-root")
    parser.add_argument("--optimized-cold-state")
    parser.add_argument("--benchmark-name")
    parser.add_argument(
        "--warm-preflight", action="store_true",
        help="Read-only cache validation required before one optimized-warm repetition",
    )
    parser.add_argument(
        "--qwen-quality-judge", action="store_true",
        help="Also require the configured Qwen evaluator; does not invoke Qwen",
    )
    args = parser.parse_args()
    if args.warm_preflight:
        if not args.warm_cache_root or not args.optimized_cold_state:
            parser.error("--warm-preflight requires --warm-cache-root and --optimized-cold-state")
        try:
            state = load_canonical_state(Path(args.optimized_cold_state).expanduser())
            print(json.dumps({
                "status": "ready", "model_invoked": False,
                "warm_cache": validate_cache_entry(Path(args.warm_cache_root).expanduser(), state),
            }, indent=2))
            return 0
        except RuntimeError as error:
            print(f"Warm preflight failed: {error}", file=sys.stderr)
            return 1
    if args.preflight:
        required_args = ("key", "url", "workspace", "jira_context", "source_revision", "personas")
        missing_args = [name.replace("_", "-") for name in required_args if not getattr(args, name)]
        if missing_args:
            parser.error("--preflight requires " + ", ".join("--" + name for name in missing_args))
        try:
            print(json.dumps(run_preflight(args), indent=2))
            return 0
        except RuntimeError as error:
            print(f"Preflight failed: {error}", file=sys.stderr)
            return 1

    if args.env_file:
        parser.error("--env-file is only valid with --preflight")
    required = ("LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
        return 2

    host = os.environ["LANGFUSE_HOST"]
    print(f"Checking Langfuse health: {host}")
    try:
        check_health(host)
        print("Health: PASS")
    except RuntimeError as error:
        print(f"Health: FAIL — {error}", file=sys.stderr)
        return 1

    try:
        check_auth(host, os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])
        print("Credentials: PASS")
    except RuntimeError as error:
        print(f"Credentials: FAIL — {error}", file=sys.stderr)
        return 1

    if args.read_only:
        print("Read-only verification: PASS")
        return 0

    if not langfuse_trace.is_enabled():
        print("Langfuse SDK/auth configuration is disabled", file=sys.stderr)
        return 1

    model = os.environ.get("LANGFUSE_VERIFY_MODEL", "gpt-6-sol")
    payload = {
        "prototype_key": "LANGFUSE-VERIFY",
        "eval_run_id": langfuse_trace.make_eval_run_id("LANGFUSE-VERIFY", seed="verify"),
        "experiment": "langfuse-openai-verify",
        "invocation": os.environ.get("AI_HELPERS_PLATFORM", "api"),
        "provider": "openai",
        "model": model,
        "billing_source": "provider_estimate",
        "run_result": {
            "cost_usd": 0.0,
            "token_usage": {"input_tokens": 1, "output_tokens": 1},
        },
        "phases": [{
            "phase": "langfuse-verify",
            "provider": "openai",
            "model": model,
            "input_tokens": 1,
            "output_tokens": 1,
            "llm_cost_usd": 0.0,
        }],
        "quality": {"langfuse_configured": 1},
    }
    result = langfuse_trace.log_pipeline_run(payload)
    print(json.dumps(result, indent=2))
    if not result.get("logged"):
        print("Smoke trace: FAIL — SDK could not confirm export", file=sys.stderr)
        return 1
    print("Smoke trace: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

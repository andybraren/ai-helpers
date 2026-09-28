#!/usr/bin/env python3
"""Read Qwen judge scores through Langfuse's authenticated public API."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
VERIFY_SPEC = importlib.util.spec_from_file_location("verify_langfuse", SCRIPT_DIR / "verify-langfuse.py")
assert VERIFY_SPEC and VERIFY_SPEC.loader
verify_langfuse = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(verify_langfuse)

QWEN_EXPECTATION_USD = 10.0
# ponytail: Langfuse names the score after the evaluator, so a single numeric
# score is the contract. Upgrade path: a separate categorical verdict
# evaluator if a 0-100 score stops being enough.
QWEN_SCORE_NAMES = ("uxd-prototype-quality-qwen-v1",)
RUBRIC_PATH = SCRIPT_DIR.parent / "config" / "qwen-quality-rubric.yaml"
QUALITY_JUDGE_PHASES = frozenset({
    "eval-journey", "eval-fix", "eval-consistency-visual", "eval-heuristic", "eval-usability",
})


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _verdict_thresholds() -> tuple[float, float]:
    """Load score bands from the versioned rubric without a YAML dependency."""
    values: dict[str, float] = {}
    for raw_line in RUBRIC_PATH.read_text().splitlines():
        key, separator, raw_value = raw_line.strip().partition(":")
        if separator and key in {"pass_min", "review_min"}:
            values[key] = float(raw_value.strip())
    if set(values) != {"pass_min", "review_min"} or values["pass_min"] <= values["review_min"]:
        raise RuntimeError(f"Qwen verdict thresholds are invalid: {RUBRIC_PATH}")
    return values["pass_min"], values["review_min"]


def _derived_verdict(value: float) -> str:
    pass_min, review_min = _verdict_thresholds()
    return "pass" if value >= pass_min else "review" if value >= review_min else "fail"


def _objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value] + [item for child in value.values() for item in _objects(child)]
    if isinstance(value, list):
        return [item for child in value for item in _objects(child)]
    return []


def _fallback_records(payload: Any) -> list[dict[str, Any]]:
    records = []
    for item in _objects(payload):
        name = str(item.get("name") or item.get("score_name") or item.get("evaluator") or "")
        value = _number(item.get("quality_score", item.get("value", item.get("score"))))
        if value is None or (name and "qwen" not in name.lower() and "quality" not in name.lower()):
            continue
        records.append({
            "phase": str(item.get("phase") or item.get("observation_name") or "unknown"),
            "quality_score": value,
            "verdict": item.get("verdict"),
            "reasoning": item.get("reasoning"),
            "trace_id": item.get("trace_id") or item.get("traceId"),
            "trace_link": item.get("trace_url") or item.get("traceUrl") or item.get("trace_link"),
            "qwen_cost_usd": _number(item.get("qwen_cost_usd", item.get("cost_usd", item.get("cost")))),
        })
    return records


def benchmark_window(benchmark_dir: Path) -> tuple[str, str] | None:
    """Use persisted reserve time as the start of a condition's score-read window."""
    try:
        ledger = json.loads((benchmark_dir / "openai-budget-ledger.json").read_text())
        starts = [event["at"] for event in ledger.get("events", []) if event.get("event") == "reserve"]
    except (OSError, TypeError, KeyError, json.JSONDecodeError):
        return None
    if not starts:
        return None
    return min(starts), datetime.now(timezone.utc).isoformat()


def _paginate_scores(host: str, headers: dict[str, str], window: tuple[str, str]) -> list[dict[str, Any]]:
    params = {
        "name": ",".join(QWEN_SCORE_NAMES), "fields": "details,subject", "limit": "100",
        "fromTimestamp": window[0], "toTimestamp": window[1],
    }
    # ponytail: one benchmark window is expected to contain <=40 Qwen scores;
    # upgrade to a server-side benchmark-tag score filter if Langfuse adds one.
    scores: list[dict[str, Any]] = []
    while True:
        payload = verify_langfuse._get_json(
            f"{host.rstrip('/')}/api/public/v3/scores?{urllib.parse.urlencode(params)}",
            headers, "Langfuse Scores API v3",
        )
        data = payload.get("data")
        if not isinstance(data, list):
            raise RuntimeError("Langfuse Scores API v3 returned data outside its verified list shape")
        scores.extend(item for item in data if isinstance(item, dict))
        cursor = (payload.get("meta") or {}).get("cursor")
        if not cursor:
            return scores
        params["cursor"] = str(cursor)


def _observation(host: str, headers: dict[str, str], observation_id: str) -> dict[str, Any] | None:
    # ponytail: deduped per-id reads cover <=40 benchmark scores; upgrade to a
    # documented batched-ID filter if Langfuse publishes one.
    filter_value = json.dumps([{
        "type": "string", "column": "id", "operator": "=", "value": observation_id,
    }], separators=(",", ":"))
    query = urllib.parse.urlencode({
        "filter": filter_value, "fields": "core,basic,metadata,trace_context,usage", "limit": "1",
    })
    payload = verify_langfuse._get_json(
        f"{host.rstrip('/')}/api/public/v2/observations?{query}", headers,
        "Langfuse Observations API v2",
    )
    data = payload.get("data") or []
    return data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else None


def _matches_benchmark(observation: dict[str, Any], benchmark_name: str) -> bool:
    metadata = observation.get("metadata") or {}
    tags = observation.get("tags") or (observation.get("traceContext") or {}).get("tags") or []
    return (
        observation.get("name") in QUALITY_JUDGE_PHASES
        and metadata.get("quality_judge_eligible") is True
        and (metadata.get("benchmark_name") == benchmark_name or f"benchmark_name={benchmark_name}" in tags)
    )


def fetch_public_api_scores(
    host: str,
    public_key: str,
    secret_key: str,
    benchmark_name: str,
    window: tuple[str, str],
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Fetch named Qwen scores for eligible paid observations in one run."""
    headers = verify_langfuse._basic_headers(public_key, secret_key)
    observations: dict[str, dict[str, Any] | None] = {}
    grouped: dict[str, dict[str, Any]] = {}
    for score in _paginate_scores(host, headers, window):
        subject = score.get("subject") or {}
        if subject.get("kind") != "observation" or not subject.get("id"):
            continue
        if trace_id and subject.get("traceId") != trace_id:
            continue
        observation_id = str(subject["id"])
        if observation_id not in observations:
            observations[observation_id] = _observation(host, headers, observation_id)
        observation = observations[observation_id]
        if not observation or not _matches_benchmark(observation, benchmark_name):
            continue
        metadata = score.get("metadata") or {}
        record = grouped.setdefault(observation_id, {
            "phase": observation.get("name", "unknown"), "quality_score": None,
            "verdict": None, "verdict_source": "derived_from_score",
            "reasoning": score.get("comment") or metadata.get("reasoning"),
            "trace_id": subject.get("traceId") or observation.get("traceId"),
            "trace_link": None, "qwen_cost_usd": _number(metadata.get("qwen_cost_usd")),
        })
        if record["trace_id"]:
            record["trace_link"] = f"{host.rstrip('/')}/trace/{record['trace_id']}"
        if score.get("name") == "uxd-prototype-quality-qwen-v1":
            value = _number(score.get("value"))
            record["quality_score"] = value
            if value is not None:
                record["verdict"] = _derived_verdict(value)
    return {
        "records": [record for record in grouped.values() if record["quality_score"] is not None],
        "endpoint": "/api/public/v3/scores",
        "parameters": "name,fields,limit,fromTimestamp,toTimestamp,cursor; observations filter,fields,limit",
        "window": {"fromTimestamp": window[0], "toTimestamp": window[1]},
        "trace_id": trace_id,
    }


def build_report(
    public_api_payload: dict[str, Any] | None = None,
    data_mcp_payload: Any | None = None,
    local_payload: Any | None = None,
    public_api_error: str | None = None,
) -> dict[str, Any]:
    """Public API first; exports are explicit, non-blocking fallbacks."""
    if public_api_payload is not None:
        source, scores = "langfuse_public_api", public_api_payload["records"]
    elif data_mcp_payload is not None:
        source, scores = "data_mcp_export_fallback", _fallback_records(data_mcp_payload)
    elif local_payload is not None:
        source, scores = "python_exporter_local_capture_fallback", _fallback_records(local_payload)
    else:
        source, scores = "unavailable", []
    known_costs = [record["qwen_cost_usd"] for record in scores if record.get("qwen_cost_usd") is not None]
    qwen_cost = sum(known_costs) if known_costs else None
    links = sorted({record["trace_link"] for record in scores if record.get("trace_link")})
    exception = None
    if qwen_cost is not None and qwen_cost > QWEN_EXPECTATION_USD:
        exception = {
            "kind": "qwen_declared_expectation_exceeded",
            "declared_expectation_usd": QWEN_EXPECTATION_USD,
            "actual_qwen_cost_usd": qwen_cost,
            "trace_links": links,
        }
    return {
        "model_invoked": False, "score_source": source,
        "public_api": public_api_payload or {"status": "unavailable", "detail": public_api_error},
        "judge_scores": scores, "qwen_cost_usd": qwen_cost,
        "qwen_cost_status": "provider_reported" if qwen_cost is not None else "unavailable",
        "judge_spend_exception": exception,
    }


def _read_json(path: Path | None) -> Any | None:
    return json.loads(path.read_text()) if path else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Langfuse Qwen judge score report")
    parser.add_argument("--benchmark-dir", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--benchmark-name", required=True)
    parser.add_argument("--trace-id", help="Read scores for this exact Langfuse trace only")
    parser.add_argument("--data-mcp-export", type=Path, help="Explicit fallback only")
    parser.add_argument("--local-score-capture", type=Path, help="Explicit fallback only")
    args = parser.parse_args()
    try:
        verify_langfuse.load_env_file()
        window = benchmark_window(Path(args.benchmark_dir))
        if window is None:
            raise RuntimeError("public score read unavailable: benchmark ledger has no reserve event for a time window")
        public_api_payload = fetch_public_api_scores(
            os.environ["LANGFUSE_HOST"], os.environ["LANGFUSE_PUBLIC_KEY"],
            os.environ["LANGFUSE_SECRET_KEY"], args.benchmark_name, window, args.trace_id,
        )
        public_api_error = None
    except (KeyError, RuntimeError) as error:
        public_api_payload, public_api_error = None, str(error)
    try:
        report = build_report(
            public_api_payload, _read_json(args.data_mcp_export), _read_json(args.local_score_capture), public_api_error
        )
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"cannot read score fallback: {error}")
    report.update({"condition": args.condition, "benchmark_name": args.benchmark_name})
    target = Path(args.benchmark_dir) / f"qwen-judge-scores-{args.condition}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

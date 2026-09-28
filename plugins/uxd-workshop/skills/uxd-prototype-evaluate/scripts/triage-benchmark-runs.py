#!/usr/bin/env python3
"""Triage benchmark metrics into a specific, copy-paste optimization brief.

Reads only staged JSON in the benchmark dir (no network, no model). Pairs
each paid phase's ledger reserve/settle against its Qwen quality score,
buckets phases into "doing well" vs "not at optimal", and emits a brief with a
specific goal per failing phase — not a generic "improve cost" prompt.

Sources:
  openai-budget-ledger.json   per-phase reserve/settle (budget signal)
  qwen-judge-scores-*.json    per-phase quality_score (job-done signal)
  calibration-report.json     provider-reported tokens (cost ceiling)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

# Qwen numeric score bands. Thresholds are the optimization trigger, not a
# product verdict — a phase at "review" is exactly what an optimization pass
# should target, so it is bucketed with failures, not passes.
PASS_MIN = 80
REVIEW_MIN = 40
UNDER_RESERVE_RATIO = 1.0   # settled > reserved  -> under-reserved (cap risk)
OVER_RESERVE_RATIO = 0.5    # settled < 0.5*reserved -> over-reserved (wasted headroom)


def _json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _score_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("judge_scores", "public_api", "data_mcp", "local_export"):
        node = report.get(key)
        if isinstance(node, dict) and isinstance(node.get("records"), list):
            return node["records"]
        if isinstance(node, list):
            return node
    return []


def _phase_ledger(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    phases: dict[str, dict[str, Any]] = {}
    for event in ledger.get("events", []):
        phase = event.get("phase")
        if not phase:
            continue
        entry = phases.setdefault(phase, {"model": event.get("model")})
        if event.get("event") == "reserve":
            entry["reserved_usd"] = event.get("reserved_usd")
            entry["input_tokens_bound"] = event.get("input_tokens_bound")
        elif event.get("event") == "settle":
            entry["settled_usd"] = event.get("settled_usd")
    return phases


def _budget_bucket(reserved: Any, settled: Any) -> str | None:
    if not isinstance(reserved, (int, float)) or not isinstance(settled, (int, float)):
        return None
    if settled > reserved * UNDER_RESERVE_RATIO:
        return "under-reserved"
    if reserved > 0 and settled < reserved * OVER_RESERVE_RATIO:
        return "over-reserved"
    return "on-budget"


def _quality_bucket(score: Any) -> str | None:
    if not isinstance(score, (int, float)):
        return None
    if score >= PASS_MIN:
        return "pass"
    if score >= REVIEW_MIN:
        return "review"
    return "fail"


def _state(quality: str | None, budget: str | None) -> str:
    if quality in ("fail", "review") or budget == "under-reserved":
        return "failing"
    if budget == "over-reserved":
        return "opportunity"
    return "optimal"


def _goals(phase: str, state: str, budget: str, quality: str, settled: Any, reserved: Any) -> list[str]:
    goals: list[str] = []
    if state == "optimal":
        return [f"{phase} is at optimal (quality pass, on-budget). Do not change it."]
    if quality in ("fail", "review"):
        goals.append(
            f"Raise {phase} quality from {quality} to pass (>= {PASS_MIN}): inspect the failing "
            f"output and fix the specific rubric dimensions the judge missed before touching cost."
        )
    if budget == "under-reserved":
        goals.append(
            f"{phase} settled ${settled} against a ${reserved} reserve: the OPENAI_PHASE_BOUNDS "
            f"input_tokens_bound is too low. Re-anchor the bound to the measured provider input "
            f"tokens so the $25 cap is not hit mid-run."
        )
    if budget == "over-reserved":
        goals.append(
            f"{phase} settled ${settled} against a ${reserved} reserve: the reserve is "
            f"holding cap headroom the phase does not use. Lower the bound to free headroom for "
            f"phases that actually run over."
        )
    return goals


def triage(benchmark_dir: Path, *, trace_id: str | None = None) -> dict[str, Any]:
    ledger = _json(benchmark_dir / "openai-budget-ledger.json") or {}
    calibration = _json(benchmark_dir / "calibration-report.json") or {}
    score_reports = [
        (path.stem.removeprefix("qwen-judge-scores-"), value)
        for path in sorted(benchmark_dir.glob("qwen-judge-scores-*.json"))
        if (value := _json(path)) is not None
    ]
    scores_by_phase: dict[str, dict[str, Any]] = {}
    for _condition, report in score_reports:
        for record in _score_records(report):
            if trace_id and record.get("trace_id") != trace_id:
                continue
            if record.get("phase"):
                scores_by_phase[record["phase"]] = record

    rows: list[dict[str, Any]] = []
    for phase, led in sorted(_phase_ledger(ledger).items()):
        score = scores_by_phase.get(phase, {})
        quality = _quality_bucket(score.get("quality_score"))
        budget = _budget_bucket(led.get("reserved_usd"), led.get("settled_usd"))
        state = _state(quality, budget)
        rows.append(
            {
                "phase": phase,
                "model": led.get("model"),
                "reserved_usd": led.get("reserved_usd"),
                "settled_usd": led.get("settled_usd"),
                "budget": budget,
                "quality_score": score.get("quality_score"),
                "quality": quality,
                "state": state,
                "trace_link": score.get("trace_link"),
                "goals": _goals(phase, state, budget or "on-budget", quality or "pass", led.get("settled_usd"), led.get("reserved_usd")),
            }
        )
    failing = [r for r in rows if r["state"] == "failing"]
    opportunity = [r for r in rows if r["state"] == "opportunity"]
    passing = [r for r in rows if r["state"] == "optimal"]
    provider_tokens = calibration.get("provider_reported_input_tokens")
    return {
        "rows": rows,
        "failing": failing,
        "opportunity": opportunity,
        "passing": passing,
        "provider_reported_input_tokens": provider_tokens,
        "openai_completed_usd": ledger.get("completed_openai_usd"),
        "cap_usd": ledger.get("cap_usd"),
    }


def _fmt_usd(value: Any) -> str:
    return f"${value:.4f}" if isinstance(value, (int, float)) else "n/a"


def render_brief(data: dict[str, Any], benchmark_name: str) -> str:
    lines = [
        f"# Benchmark optimization brief — {benchmark_name}",
        "",
        f"- OpenAI spent: `{_fmt_usd(data['openai_completed_usd'])}` / "
        f"`{_fmt_usd(data['cap_usd'])}` cap.",
        f"- Provider-reported input tokens (calibration): `{data['provider_reported_input_tokens']}`.",
        "",
        "| Phase | Model | Reserved | Settled | Budget | Qwen | Verdict |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for r in data["rows"]:
        lines.append(
            f"| {r['phase']} | {r['model']} | {_fmt_usd(r['reserved_usd'])} | "
            f"{_fmt_usd(r['settled_usd'])} | {r['budget']} | {r['quality_score']} | {r['quality']} |"
        )
    lines += ["", "## Failing phases (target these)", ""]
    if not data["failing"]:
        lines.append("None — all paid phases are at optimal.")
    for r in data["failing"]:
        lines.append(f"### {r['phase']}")
        if r.get("trace_link"):
            lines.append(f"- Trace: {r['trace_link']}")
        lines += [f"- {goal}" for goal in r["goals"]]
        lines.append("")
    lines += ["## Opportunities (not failing, but reserving unused headroom)", ""]
    if not data["opportunity"]:
        lines.append("None.")
    for r in data["opportunity"]:
        lines += [f"- {r['phase']}: {r['goals'][0]}"]
    lines += ["", "## Passing phases (contrast — do not change)", ""]
    if not data["passing"]:
        lines.append("None.")
    for r in data["passing"]:
        lines.append(f"- {r['phase']}: {r['goals'][0]}")
    lines += ["", "## Agent prompt (copy-paste)", "```", _agent_prompt(data), "```", ""]
    return "\n".join(lines)


def _agent_prompt(data: dict[str, Any]) -> str:
    failing = ", ".join(r["phase"] for r in data["failing"]) or "none"
    opportunity = ", ".join(r["phase"] for r in data["opportunity"]) or "none"
    passing = ", ".join(r["phase"] for r in data["passing"]) or "none"
    return (
        "You are optimizing the uxd-prototype-evaluate pipeline. Specific goals only; do not "
        "refactor beyond them. Failing phases: "
        f"{failing}. Opportunities (re-anchor only, no behavior change): {opportunity}. "
        f"Passing phases (leave unchanged): {passing}. For each failing phase, resolve its "
        "specific goal above: quality-first (fix the rubric dimension the judge missed) before "
        "cost. When a budget bucket is 'under-reserved', re-anchor the OPENAI_PHASE_BOUNDS "
        "input_tokens_bound to the measured provider tokens. Do not weaken the $25 program cap. "
        "Re-run the $0 regression gates (run-script-tests.sh, consistency 14/14, make validate, "
        "git diff --check) before reporting."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage benchmark metrics into an optimization brief")
    parser.add_argument("--benchmark-dir", required=True, type=Path)
    parser.add_argument("--benchmark-name", default="benchmark")
    parser.add_argument("--trace-id", help="Use only judge scores attached to this trace")
    args = parser.parse_args()
    data = triage(args.benchmark_dir, trace_id=args.trace_id)
    out = args.benchmark_dir / "optimization-brief.md"
    out.write_text(render_brief(data, args.benchmark_name))
    print(
        json.dumps(
            {
                "model_invoked": False,
                "brief": str(out),
                "failing": [r["phase"] for r in data["failing"]],
                "opportunity": [r["phase"] for r in data["opportunity"]],
                "passing": [r["phase"] for r in data["passing"]],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

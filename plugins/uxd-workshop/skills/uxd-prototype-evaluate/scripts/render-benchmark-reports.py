#!/usr/bin/env python3
"""Render gitignored benchmark summaries from local ledger and Data MCP exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def report_data(benchmark_dir: Path) -> dict[str, Any]:
    qwen = {
        path.stem.removeprefix("qwen-judge-scores-"): value
        for path in sorted(benchmark_dir.glob("qwen-judge-scores-*.json"))
        if (value := _json(path)) is not None
    }
    ledger = _json(benchmark_dir / "openai-budget-ledger.json") or {}
    calibration = _json(benchmark_dir / "calibration-report.json")
    qwen_costs = [value.get("qwen_cost_usd") for value in qwen.values()]
    known_costs = [cost for cost in qwen_costs if isinstance(cost, (int, float))]
    exceptions = [value["judge_spend_exception"] for value in qwen.values() if value.get("judge_spend_exception")]
    return {
        "openai_completed_usd": ledger.get("completed_openai_usd", 0),
        "openai_active_reservations_usd": ledger.get("active_reservations_usd", 0),
        "openai_cap_usd": ledger.get("cap_usd", 25),
        "qwen_conditions": qwen,
        "qwen_cost_usd": sum(known_costs) if known_costs else None,
        "qwen_cost_status": "provider_reported" if known_costs else "unavailable",
        "qwen_exceptions": exceptions,
        "calibration": calibration,
    }


def render_reports(benchmark_dir: Path) -> tuple[Path, Path]:
    data = report_data(benchmark_dir)
    qwen_rows = []
    for condition, report in data["qwen_conditions"].items():
        qwen_rows.append(
            f"| {condition} | {report.get('score_source')} | {report.get('qwen_cost_usd', 'unavailable')} | "
            f"{len(report.get('judge_scores') or [])} |"
        )
    qwen_table = "\n".join(qwen_rows) or "| none | unavailable | unavailable | 0 |"
    calibration = data["calibration"] or {}
    screenshot_status = calibration.get("measurement_status", "not_measured")
    exceptions = json.dumps(data["qwen_exceptions"], indent=2) if data["qwen_exceptions"] else "none"
    comparison = benchmark_dir / "langfuse-ab-comparison.md"
    designer = benchmark_dir / "designer-phase-costs.md"
    comparison.write_text(
        "# Langfuse A/B comparison\n\n"
        "## Qwen judge score read-back\n\n"
        "| Condition | Source | Qwen cost USD | Scores |\n|---|---|---:|---:|\n"
        f"{qwen_table}\n\n"
        f"Qwen billing: `{data['qwen_cost_status']}`; total: `{data['qwen_cost_usd']}`. "
        "Data MCP is preferred; Python exporter capture is explicitly fallback.\n\n"
        f"Qwen expectation exceptions (>$10):\n\n```json\n{exceptions}\n```\n"
    )
    designer.write_text(
        "# Designer phase costs\n\n"
        f"- OpenAI completed: `${data['openai_completed_usd']}` / `${data['openai_cap_usd']}` cap.\n"
        f"- OpenAI active reservations: `${data['openai_active_reservations_usd']}`.\n"
        f"- Qwen billing: `{data['qwen_cost_status']}`; total: `{data['qwen_cost_usd']}`.\n"
        f"- Auto-detail calibration: `{screenshot_status}`. Do not claim screenshot reduction until measured.\n"
        "- Warm full-cache hits create no paid-phase observations; Qwen spend is $0 by construction.\n"
    )
    return comparison, designer


def main() -> int:
    parser = argparse.ArgumentParser(description="Render zero-spend benchmark summaries")
    parser.add_argument("--benchmark-dir", required=True, type=Path)
    args = parser.parse_args()
    comparison, designer = render_reports(args.benchmark_dir)
    print(json.dumps({"model_invoked": False, "reports": [str(comparison), str(designer)]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

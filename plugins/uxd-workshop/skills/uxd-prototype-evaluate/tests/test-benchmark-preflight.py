#!/usr/bin/env python3
"""Deterministic tests for MCP-first local benchmark preflight."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
MODULE_PATH = SCRIPT_DIR / "langfuse-trace-pipeline.py"
SPEC = importlib.util.spec_from_file_location("langfuse_trace_pipeline", MODULE_PATH)
assert SPEC and SPEC.loader
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)

VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_langfuse", SCRIPT_DIR / "verify-langfuse.py"
)
assert VERIFY_SPEC and VERIFY_SPEC.loader
verify = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(verify)

SCORE_SPEC = importlib.util.spec_from_file_location(
    "read_langfuse_judge_scores", SCRIPT_DIR / "read-langfuse-judge-scores.py"
)
assert SCORE_SPEC and SCORE_SPEC.loader
judge_scores = importlib.util.module_from_spec(SCORE_SPEC)
SCORE_SPEC.loader.exec_module(judge_scores)

REPORT_SPEC = importlib.util.spec_from_file_location(
    "render_benchmark_reports", SCRIPT_DIR / "render-benchmark-reports.py"
)
assert REPORT_SPEC and REPORT_SPEC.loader
benchmark_reports = importlib.util.module_from_spec(REPORT_SPEC)
REPORT_SPEC.loader.exec_module(benchmark_reports)

TRIAGE_SPEC = importlib.util.spec_from_file_location(
    "triage_benchmark_runs", SCRIPT_DIR / "triage-benchmark-runs.py"
)
assert TRIAGE_SPEC and TRIAGE_SPEC.loader
triage = importlib.util.module_from_spec(TRIAGE_SPEC)
TRIAGE_SPEC.loader.exec_module(triage)


def write_warm_cache(root: Path, compound_key: str) -> None:
    entry = root / compound_key.split(":", 1)[1]
    entry.mkdir(parents=True)
    records = []
    for filename in verify.CANONICAL_FILES:
        content = json.dumps({"artifact": filename}).encode()
        (entry / filename).write_bytes(content)
        records.append({
            "name": filename,
            "bytes": len(content),
            "sha256": "sha256:" + verify.hashlib.sha256(content).hexdigest(),
        })
    (entry / "manifest.json").write_text(json.dumps({
        "compound_key": compound_key, "files": records,
    }))


def main() -> int:
    repo_tmp = pipeline.PROJECT_ROOT / "tmp"
    repo_tmp.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=repo_tmp) as temp_dir:
        benchmark = Path(temp_dir).resolve()
        workspace = benchmark / "workspace"
        workspace.mkdir()
        context = benchmark / "jira-context.json"
        context.write_text(json.dumps({
            "schema_version": 1,
            "source": "atlassian-mcp",
            "ticket": {
                "key": "RHOAIUX-3239",
                "summary": "Tool calling visibility",
                "description": "Acceptance Criteria\n- Show tool calls",
            },
        }))

        resolved = pipeline.resolve_local_inputs(
            key="RHOAIUX-3239",
            workspace=str(workspace),
            jira_context_file=str(context),
            benchmark_dir=str(benchmark),
        )
        assert resolved["workspace"] == str(workspace)
        assert resolved["jira_context_file"] == str(context)

        browser_context = benchmark / "jira-browser-context.json"
        browser_context.write_text(json.dumps({
            "source": "jira-authenticated-browser",
            "source_url": "https://redhat.atlassian.net/browse/RHOAIUX-3239",
            "staged_by": "authenticated read-only browser extraction",
            "ticket": {
                "key": "RHOAIUX-3239",
                "summary": "Tool calling visibility",
                "description": "Acceptance Criteria\n- Show tool calls",
            },
        }))
        browser_resolved = pipeline.resolve_local_inputs(
            key="RHOAIUX-3239",
            workspace=str(workspace),
            jira_context_file=str(browser_context),
            benchmark_dir=str(benchmark),
        )
        assert browser_resolved["jira_context_file"] == str(browser_context)

        prompt = pipeline.build_prompt(
            "RHOAIUX-3239",
            "http://localhost:9000",
            str(workspace),
            "--no-fix",
            jira_context_file=str(context),
            benchmark_dir=str(benchmark),
            consistency_report=str(
                workspace
                / ".artifacts"
                / "RHOAIUX-3239"
                / "eval"
                / "consistency-report.json"
            ),
        )
        assert str(pipeline.SKILL_DIR) in prompt
        assert str(context) in prompt
        assert "Validated source consistency report" in prompt
        assert ".claude" in prompt and "Do not discover" in prompt
        assert "credential" in prompt

        invalid_context = benchmark / "invalid.json"
        invalid_context.write_text(json.dumps({
            "source": "manual",
            "ticket": {
                "key": "RHOAIUX-3239",
                "summary": "Invalid",
                "description": "Invalid",
            },
        }))
        try:
            pipeline.resolve_local_inputs(
                key="RHOAIUX-3239",
                workspace=str(workspace),
                jira_context_file=str(invalid_context),
                benchmark_dir=str(benchmark),
            )
        except ValueError as error:
            assert "atlassian-mcp" in str(error)
        else:
            raise AssertionError("non-MCP Jira context should fail")

        identity = {
            "intent_key": "sha256:" + "1" * 64,
            "build_key": "sha256:" + "2" * 64,
            "evaluator_key": "sha256:" + "3" * 64,
        }
        compound_key = verify._compound_key(identity)
        canonical_states = []
        condition_workspaces = []
        for condition in ("legacy", "optimized-cold", "optimized-warm"):
            condition_workspace = benchmark / "conditions" / condition
            state = condition_workspace / ".artifacts" / "RHOAIUX-3239" / "eval" / "state.json"
            state.parent.mkdir(parents=True)
            state.write_text(json.dumps({"identity": {**identity, "compound_key": compound_key}}))
            canonical_states.append(f"{condition}={state}")
            condition_workspaces.append(f"{condition}={condition_workspace}")
        args = SimpleNamespace(
            env_file=None,
            key="RHOAIUX-3239",
            url="http://localhost:9000",
            workspace=str(workspace),
            jira_context=str(context),
            source_revision="a" * 40,
            personas="data-scientist+junior,data-scientist+senior",
            canonical_state=canonical_states,
            condition_workspace=condition_workspaces,
            qwen_quality_judge=False,
            benchmark_name=None,
        )
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "LANGFUSE_HOST": "http://langfuse.test",
            "LANGFUSE_PUBLIC_KEY": "public",
            "LANGFUSE_SECRET_KEY": "secret",
        }, clear=True), patch.object(verify, "workspace_revision", return_value="a" * 40), patch.object(verify, "check_openai_auth"), patch.object(verify, "check_health"), patch.object(verify, "check_auth"), patch.object(verify, "check_langfuse_qwen_config"), patch.object(verify, "check_prototype_url"), patch.object(verify.subprocess, "run", return_value=SimpleNamespace(returncode=0)):
            try:
                verify.run_preflight(args)
            except RuntimeError as error:
                assert "benchmark OpenAI upper-bound estimate $33.840240 exceeds the $25.00 program cap" in str(error)
            else:
                raise AssertionError("over-cap benchmark plan must stop before remote checks")
            safe_cost = verify.expected_openai_cost()
            safe_cost["program_openai_cost_usd"] = 24.0
            with patch.object(verify, "expected_openai_cost", return_value=safe_cost):
                preflight = verify.run_preflight(args)
        cost_estimate = verify.expected_openai_cost()
        assert cost_estimate["program_openai_cost_usd"] == 33.84024
        assert cost_estimate["openai_cap_usd"] == 25
        assert preflight["model_invoked"] is False
        assert preflight["canonical_compound_key"] == compound_key
        assert set(preflight["condition_workspaces"]) == {"legacy", "optimized-cold", "optimized-warm"}
        journey_estimate = next(
            item for item in preflight["expected_cost"]["phases"]
            if item["phase"] == "eval-journey"
        )
        assert journey_estimate == {
            "phase": "eval-journey", "model": "gpt-6-sol",
            "input_tokens_bound": 10_028, "output_tokens_bound": 1_614,
            "openai_cost_usd": 0.036196,
        }
        assert preflight["qwen"]["version"] == "1.0.0"
        assert preflight["qwen"]["provider_inference"] == "not run"

        with patch.object(verify, "_get_json", side_effect=[
            {"data": [{"name": "Qwen3.8"}]}, {"data": [{"name": "other"}]},
        ]):
            try:
                verify.check_langfuse_qwen_config("http://langfuse.test", "public", "secret")
            except RuntimeError as error:
                assert "Qwen3.8-27B" in str(error)
            else:
                raise AssertionError("missing Qwen model should fail")

        with patch.object(verify, "_get_json", side_effect=[
            {"data": [{"id": "judge-1", "name": verify.QWEN_EVALUATOR_NAME, "enabled": True, "connection": "Qwen3.8", "model": "Qwen3.8-27B"}]},
            {"data": [{"evaluatorId": "judge-1", "filter": "benchmark_name=study sanitized_artifact_output eval-journey eval-fix eval-consistency-visual eval-heuristic eval-usability"}]},
        ]):
            assertion = verify.check_langfuse_qwen_evaluator(
                "http://langfuse.test", "public", "secret", "study"
            )
        assert assertion == {"evaluator_id": "judge-1", "benchmark_name": "study"}

        public_report = judge_scores.build_report({"records": [{
            "phase": "eval-journey", "quality_score": 88, "verdict": "pass",
            "trace_link": "https://langfuse.test/trace/one", "qwen_cost_usd": 10.01,
        }]})
        assert public_report["score_source"] == "langfuse_public_api"
        assert public_report["judge_spend_exception"]["trace_links"] == ["https://langfuse.test/trace/one"]
        fallback_report = judge_scores.build_report(None, None, {
            "scores": [{"score_name": "local_artifact_quality", "value": 1, "phase": "artifact-scoring"}],
        })
        assert fallback_report["score_source"] == "python_exporter_local_capture_fallback"
        with patch.object(verify, "_get_json", side_effect=[
            RuntimeError("Langfuse Scores API v2 returned HTTP 404"),
            {"data": [], "meta": {"limit": 1}},
            {"data": [], "meta": {"limit": 1}},
        ]):
            score_api = verify.check_langfuse_scores_api("http://langfuse.test", "public", "secret")
        assert score_api["primary_endpoint"] == "/api/public/v3/scores"
        assert "HTTP 404" in score_api["v2_status"]
        with patch.object(judge_scores.verify_langfuse, "_get_json", side_effect=[
            {"data": [
                {"name": "uxd-prototype-quality-qwen-v1", "value": 88, "comment": "Grounded and actionable.", "subject": {"kind": "observation", "id": "obs-1", "traceId": "trace-1"}, "metadata": {"qwen_cost_usd": 1.5}},
            ], "meta": {"limit": 100}},
            {"data": [{
                "name": "eval-journey", "tags": ["benchmark_name=study"],
                "metadata": {"quality_judge_eligible": True},
            }]},
        ]):
            fetched = judge_scores.fetch_public_api_scores(
                "http://langfuse.test", "public", "secret", "study",
                ("2026-09-17T00:00:00+00:00", "2026-09-17T01:00:00+00:00"),
            )
        assert fetched["records"] == [{
            "phase": "eval-journey", "quality_score": 88.0, "verdict": "pass",
            "verdict_source": "derived_from_score", "reasoning": "Grounded and actionable.",
            "trace_id": "trace-1", "trace_link": "http://langfuse.test/trace/trace-1", "qwen_cost_usd": 1.5,
        }]
        with patch.object(judge_scores.verify_langfuse, "_get_json", side_effect=[
            {"data": [{
                "name": "uxd-prototype-quality-qwen-v1", "value": 88,
                "subject": {"kind": "observation", "id": "obs-other", "traceId": "other-trace"},
            }], "meta": {"limit": 100}},
        ]):
            exact = judge_scores.fetch_public_api_scores(
                "http://langfuse.test", "public", "secret", "study",
                ("2026-09-17T00:00:00+00:00", "2026-09-17T01:00:00+00:00"), "trace-1",
            )
        assert exact["records"] == []
        assert exact["trace_id"] == "trace-1"
        assert judge_scores._derived_verdict(80) == "pass"
        assert judge_scores._derived_verdict(40) == "review"
        assert judge_scores._derived_verdict(39) == "fail"
        assert not judge_scores._matches_benchmark({
            "name": "eval-extract",
            "metadata": {"benchmark_name": "study", "quality_judge_eligible": False},
        }, "study")
        (benchmark / "openai-budget-ledger.json").write_text(json.dumps({
            "events": [{"event": "reserve", "at": "2026-09-17T00:00:00+00:00"}],
        }))
        assert judge_scores.benchmark_window(benchmark)[0] == "2026-09-17T00:00:00+00:00"

        (benchmark / "qwen-judge-scores-legacy.json").write_text(json.dumps(public_report))
        (benchmark / "openai-budget-ledger.json").write_text(json.dumps({
            "cap_usd": 25, "completed_openai_usd": 1.5, "active_reservations_usd": 0,
        }))
        comparison, designer = benchmark_reports.render_reports(benchmark)
        assert "langfuse_public_api" in comparison.read_text()
        assert "OpenAI completed" in designer.read_text()

        personal_args = SimpleNamespace(
            env_file=None,
            key="RHOAIUX-3239",
            url="http://localhost:9000",
            workspace=str(workspace),
            jira_context=str(context),
            personas="data-scientist+junior,data-scientist+senior",
            qwen_quality_judge=True,
            benchmark_name="personal-evaluation",
        )
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "test-key",
            "LANGFUSE_HOST": "http://langfuse.test",
            "LANGFUSE_PUBLIC_KEY": "public",
            "LANGFUSE_SECRET_KEY": "secret",
        }, clear=True), patch.object(pipeline.verify_langfuse, "check_openai_auth"), patch.object(
            pipeline.verify_langfuse, "check_health"
        ), patch.object(pipeline.verify_langfuse, "check_auth"), patch.object(
            pipeline.verify_langfuse, "check_langfuse_scores_api", return_value={}
        ), patch.object(
            pipeline.verify_langfuse,
            "check_langfuse_qwen_evaluator",
            return_value={"evaluator_id": "judge-1", "benchmark_name": "personal-evaluation"},
        ), patch.object(pipeline.verify_langfuse, "check_prototype_url"), patch.object(
            pipeline.importlib.util, "find_spec", return_value=object()
        ):
            personal = pipeline.run_personal_preflight(personal_args)
        assert personal["mode"] == "personal"
        assert personal["model_invoked"] is False
        assert personal["estimate"]["single_run_openai_cost_usd"] == round(sum(
            item["openai_cost_usd"] for item in personal["estimate"]["phases"]
        ), 6)
        assert {item["model"] for item in personal["estimate"]["phases"]} == {"gpt-6-sol"}
        assert personal["qwen"]["assertion"]["evaluator_id"] == "judge-1"

        triage_dir = benchmark / "triage-fixture"
        triage_dir.mkdir()
        (triage_dir / "openai-budget-ledger.json").write_text(json.dumps({
            "cap_usd": 25, "completed_openai_usd": 0.1,
            "events": [
                {"event": "reserve", "phase": "eval-journey", "model": "gpt-5.6-luna", "reserved_usd": 0.1, "input_tokens_bound": 40000},
                {"event": "settle", "phase": "eval-journey", "model": "gpt-5.6-luna", "settled_usd": 0.01},
                {"event": "reserve", "phase": "eval-consistency-visual", "model": "gpt-5.6-luna", "reserved_usd": 0.02, "input_tokens_bound": 60000},
                {"event": "settle", "phase": "eval-consistency-visual", "model": "gpt-5.6-luna", "settled_usd": 0.04},
                {"event": "reserve", "phase": "eval-usability", "model": "gpt-5.6-terra", "reserved_usd": 0.3, "input_tokens_bound": 80000},
                {"event": "settle", "phase": "eval-usability", "model": "gpt-5.6-terra", "settled_usd": 0.2},
            ],
        }))
        (triage_dir / "qwen-judge-scores-calibration.json").write_text(json.dumps({
            "public_api": {"records": [
                {"phase": "eval-journey", "quality_score": 90, "trace_link": "https://langfuse.test/trace/j"},
                {"phase": "eval-consistency-visual", "quality_score": 25, "trace_link": "https://langfuse.test/trace/v"},
                {"phase": "eval-usability", "quality_score": 85, "trace_link": "https://langfuse.test/trace/u"},
            ]},
        }))
        triaged = triage.triage(triage_dir)
        states = {r["phase"]: r["state"] for r in triaged["rows"]}
        assert states["eval-journey"] == "opportunity", states
        assert states["eval-consistency-visual"] == "failing", states
        assert states["eval-usability"] == "optimal", states
        brief = triage.render_brief(triaged, "study")
        assert "Failing phases" in brief and "Opportunities" in brief and "Passing phases" in brief

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

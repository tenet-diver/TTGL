"""Offline bridge checks; scripted responses are not benchmark model results."""
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from ttgl import benchmark, personal, worker


def local_repo(path):
    path.mkdir()
    for args in (["init", "--quiet"], ["config", "user.email", "test@example.invalid"],
                 ["config", "user.name", "Test"]):
        subprocess.run(["git", "-C", str(path), *args], check=True)
    (path / "code.py").write_text("value = 1\n")
    subprocess.run(["git", "-C", str(path), "add", "code.py"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "--quiet", "-m", "base"], check=True)
    return benchmark.git(path, "rev-parse", "HEAD").strip()


@pytest.fixture
def task_manifest(tmp_path):
    path = tmp_path / "tasks.json"
    value = {"schema_version": 1, "dataset_id": "princeton-nlp/SWE-bench_Verified",
             "dataset_revision": "dataset-revision", "harness_commit": "harness-revision",
             "tasks": [{"instance_id": "example__project-1", "repo": "example/project",
                        "base_commit": "a" * 40, "problem_statement": "Fix value."}]}
    path.write_text(json.dumps(value))
    return path


@pytest.fixture
def fake_worker(task_manifest, tmp_path, monkeypatch):
    """Dependency lifecycle fixture, not a Docker or model readiness result."""
    rows = json.loads(task_manifest.read_text())["tasks"]
    path = tmp_path / "worker-config.json"
    config = {"schema_version": 1, "mode": "official_image_development_tools", "tasks": {
        row["instance_id"]: {"image": "swebench/sweb.eval.fixture@sha256:" + "b" * 64,
            "probe_argv": [worker.PYTHON, "-c", "import sys"], "probe_timeout_seconds": 30}
        for row in rows}}
    path.write_text(json.dumps(config))

    class FixtureContainer:
        def __init__(self, workspace, task, entry, owner, **kwargs):
            self.workspace, self.task, self.entry = workspace, task, entry

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def probe(self):
            return {"scope": "dependency_environment_only", "task_id": self.task["instance_id"],
                    "base_commit": self.task["base_commit"], "workspace": str(self.workspace.resolve()),
                    "config_sha256": worker.digest(self.entry), "image": self.entry["image"],
                    "probe_exit_code": 0, "checkout_unchanged": True, "dependency_ready": True,
                    "confirmatory_study_ready": False}

        def instructions(self):
            return "Fixture test environment; not a real container."

    monkeypatch.setattr(worker, "ToolContainer", FixtureContainer)
    return path


def test_rejects_gold_or_duplicate_tasks(task_manifest):
    value = json.loads(task_manifest.read_text())
    value["tasks"][0]["patch"] = "reference fix"
    task_manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="exactly"):
        benchmark.read_tasks(task_manifest)
    del value["tasks"][0]["patch"]
    value["tasks"] *= 2
    task_manifest.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Duplicate"):
        benchmark.read_tasks(task_manifest)


def test_freeze_rejects_mutations_and_preserves_balanced_assignments(task_manifest, tmp_path):
    study, workspaces = tmp_path / "study", tmp_path / "workspaces"
    design = benchmark.initialize(task_manifest, study, workspaces, small_model="small-real-id", large_model="large-real-id")
    assert {x["arm"] for x in design["assignment_order"]} == set(benchmark.ARMS)
    assert len(design["assignment_order"]) == len(benchmark.ARMS)
    benchmark.load_design(study)
    (study / "tasks.json").write_text("{}")
    with pytest.raises(ValueError, match="Frozen"):
        benchmark.load_design(study)
    with pytest.raises(ValueError, match="new study"):
        benchmark.initialize(task_manifest, study, workspaces, small_model="small", large_model="large")


@pytest.mark.parametrize("value", ["../escape", "/absolute", "a/b", "--option"])
def test_rejects_unsafe_task_ids(task_manifest, value):
    data = json.loads(task_manifest.read_text())
    data["tasks"][0]["instance_id"] = value
    task_manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Unsafe"):
        benchmark.read_tasks(task_manifest)


def test_export_includes_new_files_and_rejects_changed_head(tmp_path):
    workspace = tmp_path / "repo"
    base = local_repo(workspace)
    (workspace / "code.py").write_text("value = 2\n")
    (workspace / "new.py").write_text("answer = 42\n")
    patch = benchmark.export_patch({"base_commit": base}, workspace)
    assert "+value = 2" in patch and "+answer = 42" in patch
    subprocess.run(["git", "-C", str(workspace), "add", "."], check=True)
    subprocess.run(["git", "-C", str(workspace), "commit", "--quiet", "-m", "bad worker commit"], check=True)
    with pytest.raises(ValueError, match="HEAD"):
        benchmark.export_patch({"base_commit": base}, workspace)


def prices():
    return {"kind": "api_equivalent", "currency": "USD", "retrieved_at": "2026-10-26",
            "source_url": "https://example.invalid/prices", "models": {"small": {
                "input_per_million": 2.0, "cached_input_per_million": 0.5, "output_per_million": 8.0,
                "accounting": "cached_within_input_reasoning_within_output_cache_write_at_input_rate"}}}


def test_prices_cached_input_once_and_never_adds_reasoning():
    manifest = {"usage_by_model": {"small": {"usage": {
        "input_tokens": 1_000_000, "cached_input_tokens": 200_000, "output_tokens": 100_000,
        "reasoning_output_tokens": 50_000, "cache_write_input_tokens": 800_000}}}}
    result = benchmark.estimate_price(manifest, prices())
    assert result["api_equivalent_usd"] == pytest.approx(2.5)
    assert result["subscription_cash_usd"] is None
    assert result["deployment_cost_usd"] is None
    manifest["usage_by_model"]["small"]["usage"]["cached_input_tokens"] = None
    assert benchmark.estimate_price(manifest, prices())["api_equivalent_usd"] is None
    assert benchmark.estimate_price({}, prices())["api_equivalent_usd"] is None
    assert benchmark.estimate_price(manifest, None)["api_equivalent_usd"] is None


def test_unknown_model_price_does_not_drop_expert_cost():
    manifest = {"usage_by_model": {model: {"usage": {
        "input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 5}}
        for model in ("small", "expert")}}
    result = benchmark.estimate_price(manifest, prices())
    assert result["api_equivalent_usd"] is None
    assert result["incomplete_models"] == ["expert"]
    assert result["by_model"]["small"] > 0


def test_paired_savings_uses_all_costs_and_preserves_missingness():
    design = {"seed": 10, "arms": ["small", "large"], "reference": "large", "task_ids": ["a", "b"]}
    records = [{"task_id": task, "arm": arm, "cost_usd": cost}
               for task in design["task_ids"] for arm, cost in (("small", 1), ("large", 4))]
    result = benchmark.paired_savings(records, design)
    assert result["small"]["estimated_savings_fraction"] == 0.75
    records[0]["cost_usd"] = None
    assert benchmark.paired_savings(records, design)["small"]["estimated_savings_fraction"] is None


class ScriptedBackend:
    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        if request.kind == "router":
            text = {"model": "small", "reason": "fixture"}
        else:
            (request.workspace / "code.py").write_text("value = 2\n")
            text = {"action": "complete", "question": "", "context": "", "summary": "fixture"}
        return personal.Response(text=json.dumps(text), thread_id=f"fixture-{self.calls}",
                                 usage={"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 10})


def test_full_offline_bridge_resume_exports_standard_predictions(task_manifest, fake_worker, tmp_path, monkeypatch):
    source = tmp_path / "source"
    base = local_repo(source)
    data = json.loads(task_manifest.read_text())
    data["tasks"][0]["base_commit"] = base
    task_manifest.write_text(json.dumps(data))
    study = tmp_path / "study"
    benchmark.initialize(task_manifest, study, tmp_path / "workers", small_model="small", large_model="large",
                         worker_config_path=fake_worker)

    def clone_fixture(task, workspace):
        workspace.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", str(source), str(workspace)], check=True)

    monkeypatch.setattr(benchmark, "prepare_workspace", clone_fixture)
    backend = ScriptedBackend()
    with pytest.raises(ValueError, match="preflight"):
        benchmark.run_study(study, backend=backend)
    assert benchmark.preflight(study, backend=backend)["ready"]
    assert backend.calls == 2
    benchmark.run_study(study, backend=backend)
    assert backend.calls == 9
    benchmark.run_study(study, backend=backend, resume=True)
    assert backend.calls == 9
    for arm in benchmark.ARMS:
        prediction = json.loads((study / "predictions" / f"{arm}.jsonl").read_text())
        assert set(prediction) == {"instance_id", "model_name_or_path", "model_patch"}
        assert "+value = 2" in prediction["model_patch"]
    with pytest.raises(ValueError, match="resume"):
        benchmark.run_study(study, backend=backend)

    reports = {}
    for arm in benchmark.ARMS:
        path = tmp_path / arm / "report.json"
        path.parent.mkdir()
        path.write_text(json.dumps({data["tasks"][0]["instance_id"]: {"resolved": arm == "large"}}))
        prediction = json.loads((study / "predictions" / f"{arm}.jsonl").read_text())
        (path.parent / "patch.diff").write_text(prediction["model_patch"])
        reports[arm] = {data["tasks"][0]["instance_id"]: str(path)}
    grades = tmp_path / "grades.json"
    grades.write_text(json.dumps(reports))
    summary = benchmark.analyze(study, grades, tmp_path / "analysis")
    assert summary["arms"]["large"]["resolved"] == 1
    assert summary["arms"]["small"]["resolved"] == 0
    assert summary["savings"]["small"]["estimated_savings_fraction"] is None
    assert summary["arms"]["large"]["total_cost_usd"] is None


def test_grade_requires_exact_generated_patch(tmp_path):
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"task": {"resolved": True}}))
    expected = hashlib.sha256(b"correct patch").hexdigest()
    with pytest.raises(ValueError, match="patch.diff"):
        benchmark.read_grade(report, "task", expected)
    (tmp_path / "patch.diff").write_text("different patch")
    with pytest.raises(ValueError, match="differs"):
        benchmark.read_grade(report, "task", expected)
    (tmp_path / "patch.diff").write_text("correct patch")
    assert benchmark.read_grade(report, "task", expected)[0] is True


def test_official_empty_patch_aggregate_is_failure_only_for_exact_empty_prediction(tmp_path):
    report = tmp_path / "aggregate.json"
    report.write_text(json.dumps({"empty_patch_ids": ["task"], "submitted_ids": ["task"], "resolved_ids": []}))
    empty_hash = hashlib.sha256(b"").hexdigest()
    assert benchmark.read_grade(report, "task", empty_hash)[0] is False
    with pytest.raises(ValueError, match="official per-instance"):
        benchmark.read_grade(report, "task", hashlib.sha256(b"nonempty patch").hexdigest())
    with pytest.raises(ValueError, match="official per-instance"):
        benchmark.read_grade(report, "another-task", empty_hash)
    report.write_text(json.dumps({"empty_patch_ids": ["task"], "submitted_ids": [], "resolved_ids": []}))
    with pytest.raises(ValueError, match="official per-instance"):
        benchmark.read_grade(report, "task", empty_hash)


def test_failed_preflight_stops_before_other_model_and_assignments(task_manifest, tmp_path):
    study = tmp_path / "study"
    benchmark.initialize(task_manifest, study, tmp_path / "workers", small_model="small", large_model="large")

    class FailedBackend:
        calls = 0

        def complete(self, request):
            self.calls += 1
            return personal.Response(status="failed", error_type="runtime_unavailable")

    backend = FailedBackend()
    result = benchmark.preflight(study, backend=backend)
    assert result["ready"] is False
    assert backend.calls == 1
    with pytest.raises(ValueError, match="did not establish"):
        benchmark.run_study(study, backend=backend)
    assert backend.calls == 1


def test_resume_cannot_skip_an_assignment_with_incomplete_metering(task_manifest, fake_worker, tmp_path, monkeypatch):
    source = tmp_path / "source"
    base = local_repo(source)
    data = json.loads(task_manifest.read_text())
    data["tasks"][0]["base_commit"] = base
    task_manifest.write_text(json.dumps(data))
    study = tmp_path / "study"
    benchmark.initialize(task_manifest, study, tmp_path / "workers", small_model="small", large_model="large",
                         conditions=("small", "large"), worker_config_path=fake_worker)

    def clone_fixture(task, workspace):
        workspace.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", str(source), str(workspace)], check=True)

    monkeypatch.setattr(benchmark, "prepare_workspace", clone_fixture)

    class MissingMeterBackend(ScriptedBackend):
        def complete(self, request):
            response = super().complete(request)
            if self.calls > 2:
                response.usage["output_tokens"] = None
            return response

    backend = MissingMeterBackend()
    assert benchmark.preflight(study, backend=backend)["ready"]
    with pytest.raises(RuntimeError, match="incomplete metering"):
        benchmark.run_study(study, backend=backend)
    assert backend.calls == 3
    with pytest.raises(RuntimeError, match="incomplete metering"):
        benchmark.run_study(study, backend=backend, resume=True)
    assert backend.calls == 3  # No second assignment or replay after restart.


def test_missing_worker_config_blocks_scored_calls(task_manifest, tmp_path):
    study = tmp_path / "study"
    benchmark.initialize(task_manifest, study, tmp_path / "workers", small_model="small", large_model="large")
    backend = ScriptedBackend()
    assert benchmark.preflight(study, backend=backend)["ready"]
    with pytest.raises(ValueError, match="Worker dependency configuration"):
        benchmark.run_study(study, backend=backend)
    assert backend.calls == 2
    assert not (study / "runs").exists()


def test_worker_config_is_bound_to_frozen_design(task_manifest, fake_worker, tmp_path):
    study = tmp_path / "study"
    benchmark.initialize(task_manifest, study, tmp_path / "workers", small_model="small", large_model="large",
                         worker_config_path=fake_worker)
    benchmark.load_design(study)
    (study / "worker-config.json").write_text("{}")
    with pytest.raises(ValueError, match="worker configuration"):
        benchmark.load_design(study)


def test_failed_worker_probe_stops_before_model_assignment(task_manifest, fake_worker, tmp_path, monkeypatch):
    source = tmp_path / "source"
    base = local_repo(source)
    data = json.loads(task_manifest.read_text())
    data["tasks"][0]["base_commit"] = base
    task_manifest.write_text(json.dumps(data))
    study = tmp_path / "study"
    benchmark.initialize(task_manifest, study, tmp_path / "workers", small_model="small", large_model="large",
                         worker_config_path=fake_worker)

    def clone_fixture(task, workspace):
        workspace.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", str(source), str(workspace)], check=True)

    original_probe = worker.ToolContainer.probe

    def failed_probe(self):
        return {**original_probe(self), "probe_exit_code": 1, "dependency_ready": False}

    monkeypatch.setattr(benchmark, "prepare_workspace", clone_fixture)
    monkeypatch.setattr(worker.ToolContainer, "probe", failed_probe)
    backend = ScriptedBackend()
    assert benchmark.preflight(study, backend=backend)["ready"]
    with pytest.raises(ValueError, match="dependency readiness"):
        benchmark.run_study(study, backend=backend)
    assert backend.calls == 2
    assert not (study / "runs").exists()
    probe = json.loads((study / "worker-probes.jsonl").read_text())
    assert probe["report"]["dependency_ready"] is False


def test_provider_credit_sums_all_root_roles_and_requires_state_provenance():
    state = {"run_id": "run", "usage_threads": {key: {} for key in ("router", "controller", "expert1", "expert2")},
             "status": "completed_ungraded", "usage_accounting_issues": []}
    report = {"independent_root_threads_attested": True, "selected_states_finalized": True,
              "sources": [{"sha256": "state-hash", "run_id": "run", "finalized": True}],
              "threads": [{"thread_id": key, "status": "available", "usage": {
                  "threadId": key, "estimatedUsageCreditsMicros": 1000000, "estimatedUsageUsdMicros": None}}
                  for key in state["usage_threads"]]}
    result = benchmark.subscription_for_state(state, report, "state-hash")
    assert result["estimated_credits"] == 4
    assert result["estimated_usd"] is None
    assert benchmark.subscription_for_state(state, report, "different-state")["estimated_credits"] is None
    report["threads"].pop()
    assert benchmark.subscription_for_state(state, report, "state-hash")["estimated_credits"] is None
    report["independent_root_threads_attested"] = False
    assert benchmark.subscription_for_state(state, report, "state-hash")["estimated_credits"] is None

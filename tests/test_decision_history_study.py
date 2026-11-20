import json

import pytest

from ttgl.decision_history_study import PUBLIC_TEST, actor_control
from ttgl.decision_history_study_continuation import verified_check
from ttgl.decision_history_study_tasks import tasks
from ttgl.sim_ablation.benchmark import evaluate, qualify


def test_worker_rejection_gives_recovery_instruction_and_default_works():
    assert actor_control() == {"offline_boundary": True, "invalid_timeout_rejected": True,
                               "valid_default_read_edit_check": True}


def test_reference_controls_preserve_the_earlier_checkpoints():
    suite = tasks()
    controls = qualify({task.id: task for case in suite for task in (case.predecessor, case.continuation)})
    assert len(controls) == 4
    for case in suite:
        assert evaluate(case.predecessor, case.continuation.reference).passed


def test_admission_binds_the_public_check_to_the_written_candidate():
    candidate = "answer = 7\n"
    command = "cat > solution.py <<'EOF'\n" + candidate + "EOF\n" + PUBLIC_TEST
    answer = {"exit_code": 0, "timed_out": False, "stderr": "Ran 1 test\n\nOK\n"}
    item = {"id": "item_4", "type": "mcp_tool_call", "server": "worker", "tool": "shell",
            "arguments": {"command": command}, "result": {"content": [{"type": "text", "text": json.dumps(answer)}]}}
    trace = json.dumps({"type": "item.completed", "item": item}).encode()
    assert verified_check(trace, candidate)["item_id"] == "item_4"
    with pytest.raises(ValueError, match="exact predecessor candidate"):
        verified_check(trace, candidate.replace("7", "0"))

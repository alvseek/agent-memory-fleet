"""Dispatch contracts survive compilation; these checks do not run a worker."""

from pathlib import Path

import pytest
from test_compile_procedures import cc

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=["authored", "compiled"])
def procedure(request, tmp_path):
    if request.param == "authored":
        return (ROOT / "procedures" / "dispatch-plan.md").read_text(encoding="utf-8")
    reports = cc.compile_all(ROOT, tmp_path, verbose=False)
    return next(r for r in reports if r.name == "dispatch-plan").out_path.read_text(
        encoding="utf-8"
    )


def test_plan_wizard_and_implementation_procedure_are_loaded(procedure):
    assert "plan's originating wizard procedure" in procedure
    assert "coding layer's `implement-plan` procedure" in procedure
    assert "parent plan or project instructions required by the selected plan" in procedure


def test_ask_agent_owns_worker_launches(procedure):
    assert "fleet's `ask-agent` procedure" in procedure
    assert "An omitted identity means an anonymous worker" in procedure
    assert "Handle simple fixes yourself" in procedure
    assert "Continue the same worker when its assignment needs further work" in procedure


def test_assignment_keeps_only_relevant_context(procedure):
    assert "Which phase, step or longer task to execute" in procedure
    assert "Any necessary context not already included in the plan" in procedure
    assert "Any additional rules relevant to its assignment" in procedure
    assert "Do not invent a custom command or rewrite the implementation procedure" in procedure


def test_delegation_rules_do_not_recursively_propagate(procedure):
    assert (
        "When custom rules instruct you to delegate, apply those instructions yourself" in procedure
    )
    assert "Do not pass them on as instructions for the worker to delegate again" in procedure
    assert "Pass only the assigned work and applicable implementation rules" in procedure
    assert (
        "Further delegation requires an explicit instruction permitting it for that worker"
        in procedure
    )

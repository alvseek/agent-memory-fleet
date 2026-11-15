"""Workspace assignment survives compilation; these checks do not run a worker."""

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


def test_supervisor_prepares_optional_workspace_before_launch(procedure):
    for phrase in (
        "--worktree",
        "--branch",
        "--base",
        "Reject a partial pair or `--base` without the pair",
        "source repository's current `HEAD`",
        "not flags to pass to the Einherjar CLI",
        "supervisor prepares a requested worktree before launching",
        "skip worktree setup",
        "git rev-parse --verify --end-of-options",
        'worktree add -b "<new-branch>"',
    ):
        assert phrase in procedure


def test_preflight_and_recursive_initialization_are_safe(procedure):
    for phrase in (
        "git status --short",
        "git worktree list --porcelain",
        "even if it is a submodule",
        "no automatic stash, commit or copy",
        "Refuse an existing destination, existing local branch",
        "never overwrite, reset or force",
        "Do not fetch or substitute a default branch",
        "submodule update --init --recursive",
        "incomplete initialization or mismatched pins",
        "Do not automatically copy secrets",
        "Worktrees do not isolate databases or ports",
        "STOP without launching a worker",
    ):
        assert phrase in procedure


def test_handoff_keeps_original_documents_and_worktree_identity(procedure):
    for phrase in (
        "absolute paths from the invoking working directory",
        "updates only the original plan's execution log, never a checkout copy",
        "not from the original plan's directory",
        "source repository, worktree path, branch and exact starting commit",
        "do not create another worktree",
        "If a worktree assignment is supplied",
        "exclusive ownership of implementation paths and the original plan log",
        "initial launch and every continuation",
        "same verified implementation directory and branch",
        "check the source checkout for unintended implementation edits",
    ):
        assert phrase in procedure


def test_resume_failure_and_completion_do_not_reset_or_remove(procedure):
    for phrase in (
        "immediately record",
        "--path-format=absolute --git-common-dir",
        "git branch --show-current",
        "before further setup",
        "do not reset it to the starting commit or create a second worktree",
        "never automatically remove the worktree or branch",
        "Include the worktree path and branch in the result",
        "Do not archive, merge, remove a worktree or delete its branch",
        "without human sign-off",
    ):
        assert phrase in procedure

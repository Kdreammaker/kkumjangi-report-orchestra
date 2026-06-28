from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


STEP_COMMANDS: dict[str, list[list[str]]] = {
    "drafting": [
        ["_ai_system/tools/report_gate_status.py", "--project", "{project}"],
        ["_ai_system/tools/report_preflight.py", "--project", "{project}", "--for-drafting"],
        ["_ai_system/tools/validate_report_factory.py", "--project", "{project}"],
    ],
    "review-candidate": [
        ["_ai_system/tools/validate_core_worktree_clean.py"],
        ["_ai_system/tools/report_gate_status.py", "--project", "{project}"],
        ["_ai_system/tools/report_preflight.py", "--project", "{project}", "--for-delivery", "--strict-research"],
        ["_ai_system/tools/validate_report_factory.py", "--project", "{project}", "--strict"],
        ["_ai_system/tools/validate_research_integrity.py", "--project", "{project}"],
        ["_ai_system/tools/validate_report_artifact.py", "--project", "{project}", "--strict-delivery"],
    ],
    "closeout": [
        ["_ai_system/tools/validate_core_worktree_clean.py"],
        ["_ai_system/tools/report_gate_status.py", "--project", "{project}"],
        ["_ai_system/tools/report_preflight.py", "--project", "{project}", "--for-delivery", "--strict-research"],
        ["_ai_system/tools/validate_report_factory.py", "--project", "{project}", "--strict"],
        ["_ai_system/tools/validate_research_integrity.py", "--project", "{project}"],
        ["_ai_system/tools/validate_report_artifact.py", "--project", "{project}", "--strict-delivery"],
        ["_ai_system/tools/validate_export_artifact.py", "--project", "{project}"],
        ["_ai_system/tools/validate_closeout.py", "--project", "{project}"],
        ["_ai_system/tools/validate_workspace_setup.py", "--include-user-flow"],
    ],
    "factory": [
        ["_ai_system/tools/validate_report_factory.py", "--project", "{project}", "--strict"],
    ],
    "export": [
        ["_ai_system/tools/validate_export_artifact.py", "--project", "{project}", "--required", "--strict"],
    ],
    "unverified-handoff": [
        ["_ai_system/tools/build_delivery_outbox.py", "--project", "{project}", "--dry-run"],
    ],
    "handoff": [
        ["_ai_system/tools/validate_core_worktree_clean.py"],
        ["_ai_system/tools/report_gate_status.py", "--project", "{project}"],
        ["_ai_system/tools/report_preflight.py", "--project", "{project}", "--for-delivery", "--strict-research"],
        ["_ai_system/tools/validate_report_factory.py", "--project", "{project}", "--strict"],
        ["_ai_system/tools/validate_research_integrity.py", "--project", "{project}"],
        ["_ai_system/tools/validate_report_artifact.py", "--project", "{project}", "--strict-delivery"],
        ["_ai_system/tools/validate_closeout.py", "--project", "{project}"],
        ["_ai_system/tools/build_delivery_outbox.py", "--project", "{project}", "--dry-run", "--require-active-report"],
    ],
    "workspace": [
        ["_ai_system/tools/validate_workspace_setup.py", "--include-user-flow"],
    ],
}

COMPLETION_LOCKED_STEPS = {"review-candidate", "closeout", "handoff"}


def command_for_project(command: list[str], project: str) -> list[str]:
    return [part.format(project=project) for part in command]


def run_command(command: list[str]) -> dict[str, object]:
    full_command = [sys.executable, *command]
    proc = subprocess.run(
        full_command,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": "python " + " ".join(command),
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def guarded_step(project: str, step: str) -> dict[str, object]:
    if step not in STEP_COMMANDS:
        return {
            "project": project,
            "step": step,
            "errors": [f"unknown guarded step: {step}"],
            "results": [],
        }
    projectless_steps = {"workspace", "system-core"}
    project_dir = PROJECT_ROOT / project
    if step not in projectless_steps and not project_dir.exists():
        return {
            "project": project,
            "step": step,
            "errors": [f"project directory not found: {project_dir}"],
            "results": [],
        }

    results = []
    errors = []
    for command in STEP_COMMANDS[step]:
        result = run_command(command_for_project(command, project))
        results.append(result)
        if result["exit_code"] != 0:
            errors.append(f"guard failed: {result['command']} exited {result['exit_code']}")
            break

    passed = not errors
    status_label = "passed" if passed else "blocked"
    completion_claim_allowed = passed or step not in COMPLETION_LOCKED_STEPS
    if passed:
        user_message = "검증 체인이 통과했습니다. 다만 보고서 내용 판단은 별도 검토 대상입니다."
    elif step in COMPLETION_LOCKED_STEPS:
        user_message = "검증 체인이 차단되었습니다. 최종 완료, closeout 통과, 외부 공유 가능이라고 보고하면 안 됩니다."
    else:
        user_message = "검증 체인이 차단되었습니다. 실패한 첫 항목을 수정한 뒤 다시 실행해야 합니다."

    return {
        "project": project,
        "step": step,
        "passed": passed,
        "status_label": status_label,
        "completion_claim_allowed": completion_claim_allowed,
        "user_message": user_message,
        "errors": errors,
        "results": results,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the required report-factory gate chain for a guarded workflow step.")
    parser.add_argument("--project", default="", help="Project folder name under 00_사용자_작업공간")
    parser.add_argument(
        "--step",
        required=True,
        choices=sorted(STEP_COMMANDS),
        help="Guarded workflow step to validate.",
    )
    args = parser.parse_args()

    project = args.project or "workspace"
    result = guarded_step(project, args.step)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())

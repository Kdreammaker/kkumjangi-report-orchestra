from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from compose_report_context import STAGE_SKILLS
from run_guarded_step import STEP_COMMANDS


REQUIRED_SKILL_KEYS = {
    "interview",
    "architect",
    "source",
    "chapter",
    "visual",
    "chart",
    "assemble",
    "review",
    "export",
    "cloud",
}

REQUIRED_HOOK_STEPS = {
    "drafting",
    "review-candidate",
    "closeout",
    "handoff",
    "unverified-handoff",
    "workspace",
    "system-core",
}


def run_help(script: str) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, script, "--help"],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "script": script,
        "exit_code": proc.returncode,
        "stdout_has_usage": "usage:" in proc.stdout.lower(),
        "stderr_tail": proc.stderr[-500:],
    }


def skill_frontmatter_ok(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text.startswith("---") and "\nname:" in text and "\ndescription:" in text


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    skill_results = []
    for stage, raw_path in sorted(STAGE_SKILLS.items()):
        path = Path(raw_path)
        skill_results.append(
            {
                "stage": stage,
                "path": raw_path,
                "exists": path.exists(),
                "frontmatter_ok": skill_frontmatter_ok(path) if path.exists() else False,
            }
        )

    help_results = [
        run_help("_ai_system/tools/finalize_visual_pass.py"),
        run_help("_ai_system/tools/run_guarded_step.py"),
        run_help("_ai_system/tools/compose_report_context.py"),
    ]

    missing_skill_keys = sorted(REQUIRED_SKILL_KEYS - set(STAGE_SKILLS))
    missing_hook_steps = sorted(REQUIRED_HOOK_STEPS - set(STEP_COMMANDS))
    failures = []
    failures.extend(f"missing stage skill mapping: {item}" for item in missing_skill_keys)
    failures.extend(f"missing guarded hook step: {item}" for item in missing_hook_steps)
    failures.extend(
        f"invalid skill file for {item['stage']}: {item['path']}"
        for item in skill_results
        if not item["exists"] or not item["frontmatter_ok"]
    )
    failures.extend(
        f"help failed for {item['script']}"
        for item in help_results
        if item["exit_code"] != 0 or not item["stdout_has_usage"]
    )

    payload = {
        "passed": not failures,
        "skill_results": skill_results,
        "hook_steps": sorted(STEP_COMMANDS),
        "help_results": help_results,
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

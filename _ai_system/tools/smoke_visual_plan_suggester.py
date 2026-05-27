from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_visual_plan_suggester"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def remove_project(project: Path) -> None:
    if not project.exists():
        return
    target = project.resolve()
    root = PROJECT_ROOT.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {target}") from exc
    shutil.rmtree(target)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    project = PROJECT_ROOT / SMOKE_PROJECT
    try:
        remove_project(project)
        workpack_dir = project / "reports" / "chapter_workpacks"
        workpack_dir.mkdir(parents=True, exist_ok=True)
        (workpack_dir / "ch01_workpack.md").write_text(
            "# ch01 Workpack\n\n"
            "## Reader Decision\n"
            "직접 정산 구조와 3자 정산 구조의 역할, 흐름, 통제 지점을 비교한다.\n\n",
            encoding="utf-8",
            newline="\n",
        )
        (workpack_dir / "ch02_workpack.md").write_text(
            "# ch02 Workpack\n\n"
            "## Reader Decision\n"
            "대안 A와 대안 B의 장단점, 선택 기준, 실행 리스크를 비교한다.\n\n",
            encoding="utf-8",
            newline="\n",
        )
        proc = run(["_ai_system/tools/suggest_visual_plan.py", "--project", SMOKE_PROJECT, "--write-status"])
        payload = json.loads(proc.stdout)
        suggestions = payload.get("suggestions", [])
        visual_types = {row.get("visual_type") for row in suggestions if isinstance(row, dict)}
        status_files = payload.get("status_files") if isinstance(payload.get("status_files"), dict) else {}
        passed = (
            proc.returncode == 0
            and "flow_diagram" in visual_types
            and "decision_matrix" in visual_types
            and (project / str(status_files.get("csv", ""))).exists()
            and (project / str(status_files.get("json", ""))).exists()
        )
        print(
            json.dumps(
                {
                    "passed": passed,
                    "exit_code": proc.returncode,
                    "visual_types": sorted(visual_types),
                    "payload": payload,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if passed else 1
    finally:
        remove_project(project)


if __name__ == "__main__":
    raise SystemExit(main())

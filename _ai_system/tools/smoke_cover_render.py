from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_cover_render"


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
        (project / "reports").mkdir(parents=True, exist_ok=True)
        sample = json.loads(Path("_ai_system/templates/report_html/cover/cover.example.json").read_text(encoding="utf-8"))
        (project / "reports" / "cover.data.json").write_text(
            json.dumps(sample, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        proc = run(["_ai_system/tools/validate_cover_render.py", "--project", SMOKE_PROJECT, "--write-preview"])
        payload = json.loads(proc.stdout)
        preview = project / str(payload.get("preview", ""))
        passed = proc.returncode == 0 and payload.get("passed") is True and preview.exists()
        print(json.dumps({"passed": passed, "exit_code": proc.returncode, "payload": payload}, ensure_ascii=False, indent=2))
        return 0 if passed else 1
    finally:
        remove_project(project)


if __name__ == "__main__":
    raise SystemExit(main())

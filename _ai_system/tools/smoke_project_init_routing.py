from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def main() -> int:
    source_script = Path(__file__).resolve()
    results: dict[str, object] = {"checks": []}

    with tempfile.TemporaryDirectory(prefix="report_factory_project_init_") as tmp:
        root = Path(tmp)
        (root / "_ai_system" / "tools").mkdir(parents=True)
        (root / PROJECT_ROOT).mkdir(parents=True)
        (root / "AGENTS.md").write_text("# Test Router\n", encoding="utf-8")
        shutil.copy2(source_script.with_name("init_project_workspace.py"), root / "_ai_system" / "tools" / "init_project_workspace.py")

        slug = "스모크 경로 테스트 프로젝트"
        bare = run([sys.executable, "_ai_system/tools/init_project_workspace.py", slug], root)
        project_dirs = sorted(p for p in (root / PROJECT_ROOT).iterdir() if p.is_dir())
        expected = project_dirs[0] if project_dirs else root / PROJECT_ROOT / "missing"
        wrong_root = root / slug
        profile_path = expected / "project_profile.json"
        profile = {}
        if profile_path.exists():
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
        forbidden_profile_keys = [
            key
            for key in ["document_classification", "classification", "confidentiality", "confidentiality_status", "is_confidential"]
            if key in profile
        ]
        results["checks"].append(
            {
                "name": "bare_slug_routes_under_project_root",
                "returncode": bare.returncode,
                "expected_exists": expected.exists(),
                "wrong_root_exists": wrong_root.exists(),
                "source_link_register_exists": (expected / "references" / "source_link_register.csv").exists(),
                "worklogs_exists": (expected / "worklogs").exists(),
                "initial_worklog_count": len(list((expected / "worklogs").glob("*_worklog.md"))) if (expected / "worklogs").exists() else 0,
                "project_profile_exists": profile_path.exists(),
                "project_profile_display_name": profile.get("project_name", ""),
                "folder_has_date_prefix": bool(re.match(r"^\d{6}_", expected.name)),
                "dead_output_folder_absent": not (expected / "02_보고서_결과물").exists(),
                "dead_reference_folder_absent": not (expected / "03_참고자료_목록").exists(),
                "project_profile_editor_absent": not (expected / "project_profile_editor.html").exists(),
                "static_dashboard_absent": not (expected / "00_프로젝트_대시보드.html").exists(),
                "brand_assets_exists": (expected / "brand_assets").exists(),
                "project_dashboard_launcher_exists": (expected / "프로젝트_대시보드_실행.vbs").exists(),
                "project_dashboard_batch_exists": (expected / "project_dashboard" / "open_project_dashboard.bat").exists(),
                "legacy_reference_root_launcher_absent": not (expected / "02_참고자료대장_실행.vbs").exists(),
                "legacy_reference_folder_absent": not (expected / "reference_library").exists(),
                "legacy_reference_vbs_absent": not list((expected / "reference_library").glob("*참고자료대장.vbs")),
                "legacy_reference_batch_absent": not (expected / "reference_library" / "open_reference_library.bat").exists(),
                "report_registry_exists": (expected / "reports" / "report_registry.csv").exists(),
                "report_registry_html_absent": not (expected / "reports" / "00_보고서_목록.html").exists(),
                "current_task_exists": (expected / "tasks" / "current_task.md").exists(),
                "task_status_exists": (expected / "tasks" / "task_status.html").exists(),
                "responsible_people_count": len(profile.get("responsible_people", [])) if isinstance(profile.get("responsible_people"), list) else 0,
                "practitioners_count": len(profile.get("practitioners", [])) if isinstance(profile.get("practitioners"), list) else 0,
                "external_contacts_is_list": isinstance(profile.get("external_contacts"), list),
                "forbidden_profile_keys": forbidden_profile_keys,
                "stdout": bare.stdout.strip(),
                "stderr": bare.stderr.strip(),
            }
        )

        outside = run([sys.executable, "_ai_system/tools/init_project_workspace.py", "../outside_project"], root)
        results["checks"].append(
            {
                "name": "outside_relative_path_is_blocked_by_default",
                "returncode": outside.returncode,
                "blocked": outside.returncode == 2,
                "stdout": outside.stdout.strip(),
                "stderr": outside.stderr.strip(),
            }
        )

    failures = [
        item
        for item in results["checks"]
        if not (
            (
                item["name"] == "bare_slug_routes_under_project_root"
                and item["returncode"] == 0
                and item["expected_exists"]
                and not item["wrong_root_exists"]
                and item["source_link_register_exists"]
                and item["worklogs_exists"]
                and item["initial_worklog_count"] >= 1
                and item["project_profile_exists"]
                and item["project_profile_display_name"] == slug
                and item["folder_has_date_prefix"]
                and item["dead_output_folder_absent"]
                and item["dead_reference_folder_absent"]
                and item["project_profile_editor_absent"]
                and item["static_dashboard_absent"]
                and item["brand_assets_exists"]
                and item["project_dashboard_launcher_exists"]
                and item["project_dashboard_batch_exists"]
                and item["legacy_reference_root_launcher_absent"]
                and item["legacy_reference_folder_absent"]
                and item["legacy_reference_vbs_absent"]
                and item["legacy_reference_batch_absent"]
                and item["report_registry_exists"]
                and item["report_registry_html_absent"]
                and item["current_task_exists"]
                and item["task_status_exists"]
                and item["responsible_people_count"] >= 1
                and item["practitioners_count"] >= 1
                and item["external_contacts_is_list"]
                and not item["forbidden_profile_keys"]
            )
            or (item["name"] == "outside_relative_path_is_blocked_by_default" and item["blocked"])
        )
    ]
    results["failures"] = failures
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

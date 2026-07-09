from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_document_adaptation"


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


def remove_smoke_project(project: Path) -> None:
    if not project.exists():
        return
    root = PROJECT_ROOT.resolve()
    target = project.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {target}") from exc
    shutil.rmtree(target)


def parse_payload(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON:\n{proc.stdout}\n{proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise AssertionError("payload was not a JSON object")
    return payload


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        remove_smoke_project(project)
        (project / "01_자료_넣는_곳").mkdir(parents=True, exist_ok=True)
        source = project / "01_자료_넣는_곳" / "source.md"
        source.write_text("# Source\n\nOriginal paragraph with 2026-07-05 and 42% protected values.\n", encoding="utf-8", newline="\n")

        dry_proc = run(
            [
                "_ai_system/tools/init_document_adaptation.py",
                "--project",
                SMOKE_PROJECT,
                "--source",
                "01_자료_넣는_곳/source.md",
                "--goal",
                "Turn the source into a one-page DOCX brief.",
                "--mode",
                "format_adaptation",
                "--target-file-type",
                "docx",
                "--target-format",
                "one-page brief",
                "--dry-run",
            ]
        )
        dry_payload = parse_payload(dry_proc)
        results.append(
            {
                "case": "dry_run_reports_paths_without_writing",
                "passed": dry_proc.returncode == 0
                and dry_payload.get("status") == "dry_run"
                and not (project / "documents").exists(),
                "payload": dry_payload,
            }
        )

        create_proc = run(
            [
                "_ai_system/tools/init_document_adaptation.py",
                "--project",
                SMOKE_PROJECT,
                "--source",
                "01_자료_넣는_곳/source.md",
                "--goal",
                "Turn the source into a one-page DOCX brief.",
                "--mode",
                "format_adaptation",
                "--target-file-type",
                "docx",
                "--target-format",
                "one-page brief",
                "--target-reader",
                "internal executive",
                "--output-language",
                "ko",
            ]
        )
        create_payload = parse_payload(create_proc)
        paths = create_payload.get("paths") if isinstance(create_payload.get("paths"), dict) else {}
        manifest_path = Path(str(paths.get("manifest", "")))
        plan_path = Path(str(paths.get("plan", "")))
        preserved_path = Path(str(paths.get("preserved_copy", "")))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        results.append(
            {
                "case": "create_preserves_source_and_writes_plan_manifest",
                "passed": create_proc.returncode == 0
                and preserved_path.exists()
                and plan_path.exists()
                and manifest_path.exists()
                and manifest.get("request", {}).get("adaptation_mode") == "format_adaptation"
                and manifest.get("verification", {}).get("original_preserved") is True
                and preserved_path.read_text(encoding="utf-8") == source.read_text(encoding="utf-8"),
                "payload": create_payload,
            }
        )

        external_dir = Path(tempfile.mkdtemp(prefix="kkumjangi_doc_adapt_"))
        try:
            external_source = external_dir / "external_source.md"
            external_source.write_text("# External\n\nPath should not leak into the plan.\n", encoding="utf-8", newline="\n")
            external_proc = run(
                [
                    "_ai_system/tools/init_document_adaptation.py",
                    "--project",
                    SMOKE_PROJECT,
                    "--source",
                    str(external_source),
                    "--goal",
                    "Adapt an external source without leaking the absolute path.",
                    "--mode",
                    "light_polish",
                    "--target-file-type",
                    "md",
                ]
            )
            external_payload = parse_payload(external_proc)
            external_paths = external_payload.get("paths") if isinstance(external_payload.get("paths"), dict) else {}
            external_manifest_path = Path(str(external_paths.get("manifest", "")))
            external_plan_path = Path(str(external_paths.get("plan", "")))
            external_manifest = json.loads(external_manifest_path.read_text(encoding="utf-8")) if external_manifest_path.exists() else {}
            external_plan = external_plan_path.read_text(encoding="utf-8") if external_plan_path.exists() else ""
            manifest_source = external_manifest.get("source", {}).get("original_path", "")
            results.append(
                {
                    "case": "external_source_path_is_redacted",
                    "passed": external_proc.returncode == 0
                    and external_payload.get("source") == "external_source/external_source.md"
                    and manifest_source == "external_source/external_source.md"
                    and ":\\" not in external_plan
                    and ":/" not in external_plan
                    and str(external_source) not in external_plan,
                    "payload": external_payload,
                }
            )
        finally:
            shutil.rmtree(external_dir, ignore_errors=True)
    finally:
        remove_smoke_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

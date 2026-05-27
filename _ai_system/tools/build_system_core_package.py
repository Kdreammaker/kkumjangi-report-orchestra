from __future__ import annotations

import argparse
from datetime import date
import json
import shutil
import sys
from pathlib import Path


INCLUDE_ROOT_FILES = [
    "README.md",
    "INSTALL.md",
    "AGENTS.md",
    "START_HERE.html",
    "VERSION.json",
    "CHANGELOG.md",
    "LICENSE",
]
INCLUDE_ROOT_DIRS = [
    "docs",
    ".github",
]
INCLUDE_AI_SYSTEM_DIRS = [
    "governance",
    "environment",
    "design_systems",
    "report_skills",
    "skills",
    "templates",
    "tools",
]
INCLUDE_AI_SYSTEM_FILES = ["DESIGN_DOCUMENT.md", "REFERENCE_INDEX.md", "workspace_config.json"]
EXCLUDE_DIR_NAMES = {"__pycache__"}
EXCLUDE_PARTS = {
    ("_ai_system", "backups"),
    ("_ai_system", "runtime"),
    ("_ai_system", "project_state", "latest_ai_snapshot"),
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".bak", ".tmp", ".log"}
SCRATCH_NAMES = {
    "decoded_report.txt",
    "decode_report.py",
}
SCRATCH_PREFIXES = ("inspect_", "find_")
SCRATCH_SUFFIXES = ("_inspect.txt",)


def should_exclude(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    if any(name in EXCLUDE_DIR_NAMES for name in rel_parts):
        return True
    for excluded in EXCLUDE_PARTS:
        if rel_parts[: len(excluded)] == excluded:
            return True
    if path.is_file() and path.suffix.lower() in EXCLUDE_SUFFIXES:
        return True
    if path.is_file() and path.name == "workspace_config.local.json":
        return True
    name = path.name
    if name in SCRATCH_NAMES or name.startswith(SCRATCH_PREFIXES) or name.endswith(SCRATCH_SUFFIXES):
        return True
    return False


def copy_tree_filtered(source: Path, dest: Path, root: Path) -> None:
    for item in source.rglob("*"):
        if should_exclude(item, root):
            continue
        rel = item.relative_to(root)
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def replace_section(text: str, start_heading: str, end_heading: str, replacement: str) -> str:
    start = text.find(start_heading)
    end = text.find(end_heading, start + len(start_heading)) if start != -1 else -1
    if start == -1 or end == -1:
        return text
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


def apply_public_release_metadata(output: Path, version: str) -> list[str]:
    release_date = date.today().isoformat()
    changed: list[str] = []
    version_payload = {
        "version": version,
        "release_date": release_date,
        "channel": "public",
        "summary": "Initial public release of the Report Integrity Orchestrator system core.",
    }
    (output / "VERSION.json").write_text(
        json.dumps(version_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    changed.append("VERSION.json")

    public_changelog = f"""# Changelog

## {version} - {release_date}

- Initial public release of the Report Integrity Orchestrator system core.
- Includes Apache License 2.0, NOTICE, third-party notices, security guidance, contribution guidance, and GitHub issue templates.
- Includes local-only project workspace generation, server-backed project dashboard, reference intake/normalization/indexing helpers, report-factory governance, reusable report templates, and validation tools.
- Public release packages exclude user workspaces, local runtime assets, backups, snapshots, and local machine identity files.
"""
    (output / "CHANGELOG.md").write_text(public_changelog, encoding="utf-8")
    changed.append("CHANGELOG.md")

    readme_path = output / "README.md"
    if readme_path.exists():
        readme = readme_path.read_text(encoding="utf-8")
        version_section = f"""## 버전

- 공개 버전: `{version}`
- 배포일: `{release_date}`
- 채널: `public`
- 전체 변경 이력: `CHANGELOG.md`

이 공개 레포는 과거 개발용 커밋 기록 없이 시작하는 공개 배포본입니다. 내부 개발 단계의 `0.x` 변경 이력은 포함하지 않고, 공개 사용자는 `1.0.0`부터 버전을 확인하면 됩니다.
"""
        readme = replace_section(readme, "## 버전", "## 설치", version_section)
        public_note = """## 공개 배포 안내

이 저장소는 공개 배포용 시스템 코어입니다. 실제 프로젝트 자료, 보고서 산출물, 원본 파일, 로컬 런타임 asset, 백업, 스냅샷, 기기 식별 파일은 저장소에 포함하지 않습니다.

Apache License 2.0에 따라 사용, 복제, 클론, 포크, 수정, 재배포, 파생 작업이 허용됩니다. 단, 원 저작권 고지, `LICENSE`, `docs/NOTICE`, 필요한 변경 표시를 유지해야 합니다. 원 프로젝트를 자신의 단독 창작물인 것처럼 오인시키는 방식의 사용은 라이선스 취지에 맞지 않습니다.

"""
        if "## 공개 배포 안내" not in readme:
            insert_at = readme.find("## 설치")
            if insert_at != -1:
                readme = readme[:insert_at] + public_note + readme[insert_at:]
        readme_path.write_text(readme, encoding="utf-8")
        changed.append("README.md")
    return changed


def build_package(root: Path, output: Path, force: bool, public_release_version: str | None = None) -> dict[str, object]:
    if output.exists():
        if not force:
            return {"ok": False, "errors": [f"output already exists: {output}"], "files_copied": 0}
        shutil.rmtree(output)
    output.mkdir(parents=True)

    files_copied = 0
    errors: list[str] = []
    for name in INCLUDE_ROOT_FILES:
        source = root / name
        if not source.exists():
            errors.append(f"missing root file: {name}")
            continue
        shutil.copy2(source, output / name)
        files_copied += 1
    for dirname in INCLUDE_ROOT_DIRS:
        source = root / dirname
        if not source.exists():
            errors.append(f"missing root directory: {dirname}")
            continue
        before = sum(1 for _ in output.rglob("*") if _.is_file())
        copy_tree_filtered(source, output, root)
        after = sum(1 for _ in output.rglob("*") if _.is_file())
        files_copied += max(0, after - before)

    ai_target = output / "_ai_system"
    ai_target.mkdir(parents=True, exist_ok=True)
    for name in INCLUDE_AI_SYSTEM_FILES:
        source = root / "_ai_system" / name
        if source.exists():
            target = output / "_ai_system" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            files_copied += 1
    for dirname in INCLUDE_AI_SYSTEM_DIRS:
        source = root / "_ai_system" / dirname
        if not source.exists():
            continue
        before = sum(1 for _ in output.rglob("*") if _.is_file())
        copy_tree_filtered(source, output, root)
        after = sum(1 for _ in output.rglob("*") if _.is_file())
        files_copied += max(0, after - before)

    gitignore_template = root / "_ai_system" / "templates" / "system_core_gitignore_template.txt"
    if gitignore_template.exists():
        shutil.copy2(gitignore_template, output / ".gitignore")
        files_copied += 1

    readme_template = root / "_ai_system" / "templates" / "system_core_README_template.md"
    if not (output / "README.md").exists() and readme_template.exists():
        shutil.copy2(readme_template, output / "README.md")
        files_copied += 1

    install_template = root / "_ai_system" / "templates" / "system_core_INSTALL_template.md"
    if not (output / "INSTALL.md").exists() and install_template.exists():
        shutil.copy2(install_template, output / "INSTALL.md")
        files_copied += 1

    public_release_files: list[str] = []
    if public_release_version:
        public_release_files = apply_public_release_metadata(output, public_release_version)

    return {
        "ok": not errors,
        "errors": errors,
        "output": str(output),
        "files_copied": files_copied,
        "public_release_version": public_release_version or "",
        "public_release_files": public_release_files,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build a clean report-factory system-core package directory.")
    parser.add_argument("--output", required=True, help="Output directory for the clean package.")
    parser.add_argument("--force", action="store_true", help="Replace output directory if it already exists.")
    parser.add_argument(
        "--public-release-version",
        help="Rewrite README, VERSION.json, and CHANGELOG.md for a clean public release version such as 1.0.0.",
    )
    args = parser.parse_args()

    root = Path(".").resolve()
    output = Path(args.output).resolve()
    result = build_package(root, output, args.force, args.public_release_version)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

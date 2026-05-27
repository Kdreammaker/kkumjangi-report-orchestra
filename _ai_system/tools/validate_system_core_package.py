from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_ROOTS = {"00_사용자_작업공간", ".local_state"}
SCRATCH_PATTERNS = [
    r"^inspect_.*\.(?:py|txt)$",
    r"^.*_inspect\.txt$",
    r"^ch\d+_inspect\.txt$",
    r"^decoded_report\.txt$",
    r"^decode_report\.py$",
    r"^find_.*\.py$",
]
TEMP_SUFFIXES = {".bak", ".tmp", ".log", ".pyc", ".pyo"}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def git_tracked(root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def validate(root: Path, package_mode: bool) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    tracked = git_tracked(root)

    for required in [
        "README.md",
        "INSTALL.md",
        "AGENTS.md",
        "START_HERE.html",
        "VERSION.json",
        "CHANGELOG.md",
        "LICENSE",
        "docs/NOTICE",
        "docs/THIRD_PARTY_NOTICES.md",
        "docs/SECURITY.md",
        "docs/CONTRIBUTING.md",
        "docs/USAGE_AND_PERMISSIONS.md",
        "_ai_system/REFERENCE_INDEX.md",
        "_ai_system",
    ]:
        if not (root / required).exists():
            errors.append(f"missing core package item: {required}")

    tools = root / "_ai_system" / "tools"
    scratch_files = []
    if tools.exists():
        for path in tools.iterdir():
            if not path.is_file():
                continue
            if any(re.match(pattern, path.name, flags=re.I) for pattern in SCRATCH_PATTERNS):
                scratch_files.append(rel(path, root))
    if scratch_files:
        errors.append("scratch/inspection files are present in _ai_system/tools: " + " | ".join(scratch_files[:12]))

    temp_files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if rel_parts and rel_parts[0] in FORBIDDEN_ROOTS:
            continue
        parts = set(rel_parts)
        if {"_ai_system", "backups"}.issubset(parts) or "__pycache__" in parts:
            continue
        if path.suffix.lower() in TEMP_SUFFIXES:
            temp_files.append(rel(path, root))
    if temp_files:
        errors.append("temporary/backup files are present in active package area: " + " | ".join(temp_files[:12]))

    gitignore = root / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8", errors="replace")
        if "�" in text:
            errors.append(".gitignore contains replacement characters; Korean path exclusions may be broken")
        if "00_사용자_작업공간/" not in text.replace("\\", "/"):
            errors.append(".gitignore does not explicitly exclude 00_사용자_작업공간/")
        if ".local_state/" not in text.replace("\\", "/"):
            errors.append(".gitignore does not explicitly exclude .local_state/")
    elif package_mode:
        errors.append("package mode requires .gitignore")
    else:
        warnings.append(".gitignore not found; this is acceptable for a local non-git workspace but not for a GitHub core package")

    if tracked:
        forbidden_tracked = [path for path in tracked if any(path == root_name or path.startswith(root_name + "/") for root_name in FORBIDDEN_ROOTS)]
        if forbidden_tracked:
            errors.append("git tracks forbidden user workspace paths: " + " | ".join(forbidden_tracked[:12]))
    elif package_mode:
        warnings.append("not a git repository or no tracked files found; tracked-file package boundary was not verified")

    return {
        "root": str(root),
        "package_mode": package_mode,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "scratch_files": len(scratch_files),
            "temp_files": len(temp_files),
            "git_tracked_files": len(tracked),
            "gitignore_exists": gitignore.exists(),
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Validate a clean report-factory system-core package boundary.")
    parser.add_argument("--root", default=".", help="Workspace or package root to inspect.")
    parser.add_argument("--package-mode", action="store_true", help="Require GitHub/package-ready checks such as .gitignore.")
    args = parser.parse_args()

    payload = validate(Path(args.root).resolve(), args.package_mode)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

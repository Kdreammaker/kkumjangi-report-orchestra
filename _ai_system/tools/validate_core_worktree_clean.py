from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


CORE_PREFIXES = (
    "_ai_system/",
    "_internal/",
    "AGENTS.md",
    "README.md",
    "INSTALL.md",
    "CHANGELOG.md",
    "VERSION.json",
    "START_HERE.html",
    "docs/",
)


def git_status(root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return []
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


def core_dirty_entries(status_lines: list[str]) -> list[str]:
    hits: list[str] = []
    for line in status_lines:
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path.startswith("00_사용자_작업공간/"):
            continue
        if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in CORE_PREFIXES):
            hits.append(line)
    return hits


def validate(root: Path, warn_only: bool) -> dict[str, object]:
    status_lines = git_status(root)
    dirty = core_dirty_entries(status_lines)
    errors = [] if warn_only or not dirty else ["system core files are modified during project workflow"]
    warnings = dirty if warn_only else []
    return {
        "root": str(root),
        "warn_only": warn_only,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "core_dirty_entries": dirty,
        "note": "Project report work should not modify system-core files. Promote intentional core changes through the system-core repository instead.",
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Detect accidental system-core edits during ordinary project work.")
    parser.add_argument("--root", default=".", help="Workspace root.")
    parser.add_argument("--warn-only", action="store_true", help="Report core edits without failing.")
    args = parser.parse_args()
    payload = validate(Path(args.root).resolve(), args.warn_only)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if payload["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

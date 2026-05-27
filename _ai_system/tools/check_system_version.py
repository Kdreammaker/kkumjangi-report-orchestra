from __future__ import annotations

import json
import subprocess
from pathlib import Path


VERSION_FILE = Path("VERSION.json")
CHANGELOG = Path("CHANGELOG.md")


def read_version() -> dict[str, object]:
    if not VERSION_FILE.exists():
        return {"error": "missing_VERSION.json"}
    return json.loads(VERSION_FILE.read_text(encoding="utf-8"))


def git_value(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=8).strip()
    except Exception:
        return ""


def recent_changelog_entries(limit: int = 3) -> list[str]:
    if not CHANGELOG.exists():
        return []
    entries: list[str] = []
    current: list[str] = []
    for line in CHANGELOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("## "):
            if current:
                entries.append("\n".join(current).strip())
            current = [line]
        elif current:
            current.append(line)
    if current:
        entries.append("\n".join(current).strip())
    return entries[:limit]


def main() -> int:
    version = read_version()
    local_head = git_value(["git", "rev-parse", "HEAD"])
    remote_head = git_value(["git", "rev-parse", "origin/main"])
    branch = git_value(["git", "branch", "--show-current"])
    payload = {
        "version": version,
        "git": {
            "branch": branch or "unknown",
            "local_head": local_head or "unknown",
            "origin_main": remote_head or "unknown",
            "up_to_date_with_origin_main": bool(local_head and remote_head and local_head == remote_head),
            "remote_check_note": "This compares the local git refs. Run git fetch before this check when live remote freshness matters.",
        },
        "recent_changes": recent_changelog_entries(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if "error" not in version else 1


if __name__ == "__main__":
    raise SystemExit(main())

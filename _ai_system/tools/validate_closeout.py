"""validate_closeout.py
=====================
Closeout validator — checks delivery-readiness conditions that other
validators cannot catch:

  1. Every declared project deliverable exists *inside* the workspace
     workspace root.  Files that live under the AI-service app-data directory
     (e.g. paths under AppData or .gemini/antigravity/brain/...) are
     classified as outside-workspace and cause a hard error.

  2. snapshot_manifests.bad must equal 0.  Any hash mismatch in the snapshot
     manifest means the AI made undocumented edits after the last snapshot was
     recorded, which violates the change-detection protocol.

  3. (informational) Warn when declared deliverable paths do not exist at all.

Usage
-----
  python _ai_system/tools/validate_closeout.py --project <folder_name>
  python _ai_system/tools/validate_closeout.py --project <folder_name> \\
      --deliverables path/to/file1 path/to/file2

Exit codes
----------
  0  all checks pass
  1  one or more hard errors
  2  project not found or argument error
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
WORKSPACE_ROOT = Path(".")  # script is run from workspace root
EXCLUDED_SCAN_PARTS = {
    "_ai_system/backups",
    "_ai_system/project_state/latest_ai_snapshot",
    "_ai_system/runtime",
}
EXCLUDED_SCAN_MARKERS = {
    "/archive/",
}

# Patterns that identify AI-service app-data directories that are NOT
# part of the active report workspace.
OUTSIDE_WORKSPACE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"[/\\]\.gemini[/\\]", re.IGNORECASE),
    re.compile(r"[/\\]antigravity[/\\]", re.IGNORECASE),
    re.compile(r"[/\\]brain[/\\][0-9a-f\-]{30,}", re.IGNORECASE),
    re.compile(r"[/\\]AppData[/\\]", re.IGNORECASE),
    re.compile(r"[/\\]tmp[/\\]", re.IGNORECASE),
    re.compile(r"[/\\]Temp[/\\]", re.IGNORECASE),
]

COMMON_EXTERNAL_ARTIFACT_NAMES = {
    "implementation_plan.md",
    "workspace_validation_report.md",
    "walkthrough.md",
    "task.md",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_outside_workspace(path_str: str, workspace_root: Path) -> bool:
    """Return True if the path is outside the workspace root."""
    resolved = Path(path_str).resolve()
    ws_resolved = workspace_root.resolve()
    try:
        resolved.relative_to(ws_resolved)
        return False  # inside workspace
    except ValueError:
        pass
    # Also check pattern-based heuristics for AI app-data paths.
    normalised = path_str.replace("\\", "/")
    return any(p.search(normalised) for p in OUTSIDE_WORKSPACE_PATTERNS)


def should_skip_scan_path(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(rel == part or rel.startswith(part + "/") for part in EXCLUDED_SCAN_PARTS) or any(
        marker in rel for marker in EXCLUDED_SCAN_MARKERS
    )


def check_snapshot_manifests(root: Path) -> dict[str, int]:
    """Re-implement the same hash-triple check used in validate_workspace_setup."""
    checked = 0
    bad = 0
    bad_files: list[str] = []
    for manifest in root.rglob("latest_ai_snapshot_manifest.csv"):
        if should_skip_scan_path(manifest, root):
            continue
        with manifest.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                checked += 1
                rel_path = row.get("path") or row.get("relative_path") or ""
                active = root / rel_path
                snapshot = root / row.get("snapshot_path", "")
                if not active.exists() or not snapshot.exists():
                    bad += 1
                    bad_files.append(f"MISSING: {rel_path}")
                    continue
                active_hash = sha256_file(active)
                snapshot_hash = sha256_file(snapshot)
                expected = row.get("snapshot_sha256") or row.get("sha256") or ""
                if (
                    active_hash.lower() != expected.lower()
                    or snapshot_hash.lower() != expected.lower()
                    or active_hash.lower() != snapshot_hash.lower()
                ):
                    bad += 1
                    bad_files.append(f"HASH_MISMATCH: {rel_path}")
    return {"checked": checked, "bad": bad, "bad_files": bad_files}


def default_deliverables(project: Path) -> list[str]:
    """Return a list of paths that are always expected as workspace deliverables
    for a project that has reached the internal-review stage."""
    candidates = [
        project / "프로젝트_대시보드_실행.vbs",
        project / "report_prd",
        project / "drafts",
        project / "reports",
    ]
    # Add any HTML reports found.
    for p in sorted((project / "reports").glob("*.html")):
        candidates.append(p)
    return [str(c) for c in candidates if c.exists()]


def missing_common_workspace_artifacts(root: Path) -> list[str]:
    """Find common AI-declared artifact names that are absent from the workspace.

    This cannot read an AI service's chat transcript.  It deliberately catches the
    recurring closeout risk where an assistant mentions standard artifact names
    but never mirrors them into the workspace.
    """
    found = {p.name for p in root.rglob("*") if p.is_file() and not should_skip_scan_path(p, root)}
    return sorted(COMMON_EXTERNAL_ARTIFACT_NAMES - found)


def validate_closeout(
    project: Path,
    workspace_root: Path,
    extra_deliverables: list[str] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    if not project.exists():
        return {
            "project": project.name,
            "errors": [f"project directory not found: {project}"],
            "warnings": [],
            "info": [],
        }

    # ------------------------------------------------------------------ #
    # 1. Snapshot manifest integrity: bad must be 0                       #
    # ------------------------------------------------------------------ #
    snap = check_snapshot_manifests(workspace_root)
    info.append(f"snapshot_manifests checked={snap['checked']}, bad={snap['bad']}")
    if snap["bad"] > 0:
        errors.append(
            f"CLOSEOUT FAIL — snapshot_manifests.bad={snap['bad']} (not 0). "
            "The AI made file changes that were not reflected in the snapshot manifest. "
            "Run update_ai_snapshots.py for all modified files before claiming closeout."
        )
        for bf in snap.get("bad_files", [])[:10]:
            errors.append(f"  snapshot mismatch: {bf}")

    # ------------------------------------------------------------------ #
    # 2. Deliverable location: must be inside workspace                   #
    # ------------------------------------------------------------------ #
    deliverables = list(extra_deliverables or []) + default_deliverables(project)
    outside: list[str] = []
    missing: list[str] = []
    inside_ok: list[str] = []

    for path_str in deliverables:
        if is_outside_workspace(path_str, workspace_root):
            outside.append(path_str)
        elif not Path(path_str).exists():
            missing.append(path_str)
        else:
            inside_ok.append(path_str)

    if outside:
        for p in outside:
            errors.append(
                f"CLOSEOUT FAIL — deliverable is outside-workspace and is NOT a workspace artifact: {p}"
            )
    if missing:
        for p in missing:
            warnings.append(f"declared deliverable does not exist: {p}")

    info.append(f"deliverables_inside_workspace={len(inside_ok)}")
    info.append(f"deliverables_outside_workspace={len(outside)}")
    info.append(f"deliverables_missing={len(missing)}")

    missing_common = missing_common_workspace_artifacts(workspace_root)
    if missing_common:
        warnings.append(
            "common AI artifact names are not present inside the workspace; "
            "if any were claimed in the response, classify them as outside-workspace: "
            + ", ".join(missing_common)
        )

    # ------------------------------------------------------------------ #
    # 3. Warn about known AI-service artifact folder names in any path    #
    #    referenced inside workspace files (simple heuristic scan)        #
    # ------------------------------------------------------------------ #
    report_dir = project / "reports"
    for html_file in sorted(report_dir.glob("*.html")):
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in OUTSIDE_WORKSPACE_PATTERNS:
            if pattern.search(text):
                warnings.append(
                    f"{html_file.name}: report HTML references a path pattern "
                    f"that looks like an AI-service app-data directory ({pattern.pattern})"
                )
                break

    for backup_file in sorted(report_dir.glob("*.bak")):
        errors.append(
            f"CLOSEOUT FAIL — active reports folder contains leftover backup file: {backup_file}"
        )

    return {
        "project": project.name,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "snapshot_manifests": snap,
        "deliverables_inside": inside_ok,
        "deliverables_outside": outside,
        "deliverables_missing": missing,
        "common_artifact_names_missing_from_workspace": missing_common,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=(
            "Closeout validator: checks that deliverables are inside the workspace "
            "and that snapshot manifests have zero mismatches."
        )
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Project folder name under 00_사용자_작업공간",
    )
    parser.add_argument(
        "--deliverables",
        nargs="*",
        default=[],
        help="Additional paths (absolute or workspace-relative) to classify as declared deliverables.",
    )
    args = parser.parse_args()

    workspace_root = Path(".").resolve()
    project = PROJECT_ROOT / args.project
    result = validate_closeout(project, workspace_root, args.deliverables or [])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

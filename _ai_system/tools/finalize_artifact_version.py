from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
REPORT_REGISTRY_FIELDS = [
    "report_id",
    "report_title",
    "document_classification",
    "confidentiality_status",
    "version",
    "stage",
    "owner",
    "practitioners",
    "reviewers",
    "latest_file",
    "prd_path",
    "updated_at_kst",
    "next_action",
    "notes",
]
CHANGE_LOG_FIELDS = [
    "changed_at_kst",
    "scope",
    "target_file",
    "summary",
    "pc_name",
    "anonymous_device_id",
    "before_hash",
    "after_hash",
    "app_version",
]


def now_kst() -> datetime:
    return datetime.now(timezone(timedelta(hours=9)))


def timestamp_ymdhm() -> str:
    return now_kst().strftime("%y%m%d%H%M")


def now_label() -> str:
    return now_kst().strftime("%Y-%m-%d %H:%M KST")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def safe_segment(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._-") or "artifact"


def rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def app_version(root: Path) -> str:
    data = read_json(root / "VERSION.json")
    return str(data.get("version", "unknown") or "unknown")


def read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{field: str(row.get(field, "") or "") for field in fields} for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "") or "") for field in fields})


def copy_if_exists(source: Path, dest_dir: Path, suffix: str) -> str:
    if not source.exists() or not source.is_file():
        return ""
    dest = dest_dir / f"{source.stem}_{suffix}{source.suffix}"
    shutil.copy2(source, dest)
    return dest.name


def append_dashboard_log(root: Path, project: Path, target_file: str, summary: str, before_hash: str, after_hash: str) -> dict[str, str]:
    event = {
        "changed_at_kst": now_label(),
        "scope": "report_version",
        "target_file": target_file,
        "summary": summary,
        "pc_name": platform.node() or "unknown",
        "anonymous_device_id": "AI_VERSION_TOOL",
        "before_hash": before_hash[:12],
        "after_hash": after_hash[:12],
        "app_version": app_version(root),
    }
    jsonl_path = project / "project_state" / "dashboard_change_log.jsonl"
    csv_path = project / "worklogs" / "dashboard_change_log.csv"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    rows = read_csv(csv_path, CHANGE_LOG_FIELDS)
    rows.append(event)
    write_csv(csv_path, rows, CHANGE_LOG_FIELDS)
    return event


def upsert_registry(
    project: Path,
    report_id: str,
    title: str,
    version_label: str,
    status: str,
    latest_file: str,
    prd_path: str,
    note: str,
) -> tuple[str, str]:
    path = project / "reports" / "report_registry.csv"
    before = read_text(path)
    rows = read_csv(path, REPORT_REGISTRY_FIELDS)
    now = now_label()
    matched = False
    for row in rows:
        if row.get("report_id") == report_id:
            row.update(
                {
                    "report_title": title or row.get("report_title", ""),
                    "version": version_label,
                    "stage": status,
                    "latest_file": latest_file,
                    "prd_path": prd_path or row.get("prd_path", ""),
                    "updated_at_kst": now,
                    "next_action": "review or next approved improvement",
                    "notes": note,
                }
            )
            matched = True
            break
    if not matched:
        rows.append(
            {
                "report_id": report_id,
                "report_title": title or report_id,
                "document_classification": "",
                "confidentiality_status": "",
                "version": version_label,
                "stage": status,
                "owner": "",
                "practitioners": "",
                "reviewers": "",
                "latest_file": latest_file,
                "prd_path": prd_path,
                "updated_at_kst": now,
                "next_action": "review or next approved improvement",
                "notes": note,
            }
        )
    write_csv(path, rows, REPORT_REGISTRY_FIELDS)
    after = read_text(path)
    return before, after


def append_version_history(
    project: Path,
    version_key: str,
    status: str,
    artifact_rel: str,
    current_rel: str,
    note: str,
) -> None:
    path = project / "reports" / "version_history.md"
    if not path.exists():
        path.write_text(
            "# Artifact Version History\n\n"
            "| created_at_kst | version | status | versioned_artifact | current_pointer | note |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    safe_note = note.replace("|", "/").replace("\n", " ").strip()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"| {now_label()} | {version_key} | {status} | {artifact_rel} | {current_rel} | {safe_note} |\n")


def finalize(args: argparse.Namespace) -> dict[str, object]:
    root = Path.cwd()
    project = (PROJECT_ROOT / args.project).resolve()
    if not project.exists():
        return {"passed": False, "errors": [f"project not found: {args.project}"]}
    artifact = (project / args.artifact).resolve()
    try:
        artifact.relative_to(project)
    except ValueError:
        return {"passed": False, "errors": ["artifact path is outside project"]}
    if not artifact.exists() or not artifact.is_file():
        return {"passed": False, "errors": [f"artifact not found: {args.artifact}"]}

    ts = args.timestamp or timestamp_ymdhm()
    version = safe_segment(args.version)
    version_key = f"{version}_{ts}"
    version_dir = project / "reports" / "versions" / version_key
    if version_dir.exists() and not args.force:
        return {"passed": False, "errors": [f"version folder already exists: {rel(version_dir, project)}"]}
    version_dir.mkdir(parents=True, exist_ok=True)

    suffix = version_key
    versioned_artifact = version_dir / f"{artifact.stem}_{suffix}{artifact.suffix}"
    shutil.copy2(artifact, versioned_artifact)

    copied_related = []
    for related in [
        project / "reports" / "report_assembly_manifest.json",
        project / "reports" / "assembly_manifest.json",
        project / "reports" / "quality_status" / "quality_status.json",
        project / "reports" / "workflow_status" / "workflow_status.json",
    ]:
        copied = copy_if_exists(related, version_dir, suffix)
        if copied:
            copied_related.append(copied)

    current_dir = project / "reports" / "current"
    current_dir.mkdir(parents=True, exist_ok=True)
    current_artifact = current_dir / artifact.name
    shutil.copy2(artifact, current_artifact)
    pointer = {
        "schema_version": "1.0",
        "project": args.project,
        "report_id": args.report_id or artifact.stem,
        "version": args.version,
        "version_key": version_key,
        "status": args.status,
        "artifact": rel(versioned_artifact, project),
        "current_artifact": rel(current_artifact, project),
        "source_artifact": rel(artifact, project),
        "sha256": sha256_file(versioned_artifact),
        "updated_at_kst": now_label(),
        "note": args.note,
    }
    pointer_path = current_dir / "version_pointer.json"
    pointer_path.write_text(json.dumps(pointer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    latest_rel = rel(versioned_artifact, project)
    before_registry, after_registry = upsert_registry(
        project=project,
        report_id=args.report_id or artifact.stem,
        title=args.title or artifact.stem,
        version_label=version_key,
        status=args.status,
        latest_file=latest_rel,
        prd_path=args.prd_path,
        note=args.note,
    )
    append_version_history(project, version_key, args.status, latest_rel, rel(pointer_path, project), args.note)
    event = append_dashboard_log(
        root,
        project,
        latest_rel,
        f"{version_key} created: {args.note}".strip(),
        sha256_text(before_registry),
        sha256_text(after_registry),
    )

    return {
        "passed": True,
        "project": args.project,
        "version_key": version_key,
        "artifact": latest_rel,
        "current_pointer": rel(pointer_path, project),
        "registry": "reports/report_registry.csv",
        "dashboard_event": event,
        "copied_related": copied_related,
        "warnings": [] if args.status != "draft" or args.version.startswith("v0.") else ["draft status normally uses v0.x"],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Preserve a versioned artifact and update project registries.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--artifact", required=True, help="Project-relative artifact path, e.g. reports/internal_review_report.html")
    parser.add_argument("--version", required=True, help="AI-chosen version label, e.g. v0.1")
    parser.add_argument("--status", required=True, choices=["draft", "review_candidate", "approved", "archived"])
    parser.add_argument("--note", required=True)
    parser.add_argument("--title", default="")
    parser.add_argument("--report-id", default="")
    parser.add_argument("--prd-path", default="")
    parser.add_argument("--timestamp", default="", help="YYMMDDHHMM; defaults to current KST")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    payload = finalize(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())

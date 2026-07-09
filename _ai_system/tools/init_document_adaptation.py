from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
TIER_1 = {".md", ".docx", ".html", ".htm", ".txt"}
TIER_2 = {".pdf", ".pptx", ".xlsx", ".xls", ".csv"}
MODES = {"light_polish", "format_adaptation", "substantive_rewrite", "derived_artifact", "undecided"}


def now_kst() -> datetime:
    return datetime.now(timezone(timedelta(hours=9)))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^\w가-힣.-]+", "_", value, flags=re.UNICODE).strip("._")
    return cleaned[:80] or "document"


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def source_reference(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return f"external_source/{path.name}"


def resolve_project(raw: str, workspace_root: Path) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        project = candidate
    elif len(candidate.parts) == 1:
        project = workspace_root / PROJECT_ROOT / raw
    else:
        project = workspace_root / candidate
    project = project.resolve()
    project_root = (workspace_root / PROJECT_ROOT).resolve()
    try:
        project.relative_to(project_root)
    except ValueError as exc:
        raise ValueError(f"project must be under {PROJECT_ROOT.as_posix()}: {project}") from exc
    if not project.exists() or not project.is_dir():
        raise FileNotFoundError(f"project not found: {project}")
    return project


def resolve_source(raw: str, project: Path, workspace_root: Path) -> Path:
    candidate = Path(raw)
    candidates = []
    if candidate.is_absolute():
        candidates.append(candidate)
    else:
        candidates.append(project / candidate)
        candidates.append(workspace_root / candidate)
    for item in candidates:
        resolved = item.resolve()
        if resolved.exists() and resolved.is_file():
            return resolved
    raise FileNotFoundError(f"source file not found: {raw}")


def support_tier(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TIER_1:
        return "tier_1"
    if suffix in TIER_2:
        return "tier_2_with_limitations"
    return "unsupported_requires_plan"


def plan_markdown(payload: dict[str, object]) -> str:
    source = payload["source"] if isinstance(payload["source"], dict) else {}
    request = payload["request"] if isinstance(payload["request"], dict) else {}
    verification = payload["verification"] if isinstance(payload["verification"], dict) else {}
    return f"""# Document Adaptation Plan

## Source

- adaptation_id: {payload.get("adaptation_id", "")}
- source_file: {source.get("original_path", "")}
- preserved_copy: {source.get("preserved_copy_path", "")}
- source_sha256: {source.get("sha256", "")}
- support_tier: {source.get("support_tier", "")}
- detected_file_type: {source.get("file_type", "")}

## User Request

- requested_goal: {request.get("goal", "")}
- adaptation_mode: {request.get("adaptation_mode", "")}
- target_file_type: {request.get("target_file_type", "")}
- target_format_or_template: {request.get("target_format_or_template", "")}
- target_reader: {request.get("target_reader", "")}
- output_language: {request.get("output_language", "")}
- content_depth: {request.get("content_depth", "")}
- execution_control_mode: {request.get("execution_control_mode", "")}

## Clarifications

Ask only for fields that are unclear and material to the work.

| question | why_needed | answer | status |
|---|---|---|---|
| Confirm any `undecided` mode, target, reader, or verification level before rewriting. | Prevent accidental over-rewrite or wrong output type. |  | pending |

## Protected Spans

| span_or_rule | reason | handling |
|---|---|---|
| Direct quotes, numbers, dates, units, laws, names, citations, approval/legal wording | Must not drift during adaptation | preserve unless explicitly authorized |

## Adaptation Steps

1. Inspect source structure and extraction quality.
2. Confirm or infer target mode and output.
3. Choose document preset/style profile/register guidance when relevant.
4. Create the adapted output as a new file.
5. Review protected spans and meaning changes.
6. Run file-type or render/import checks when relevant.

## Verification Plan

- original_preserved: {verification.get("original_preserved", False)}
- output_opens: {verification.get("output_opens", "not_run")}
- target_format_followed: {verification.get("target_format_followed", "not_run")}
- protected_spans_checked: {verification.get("protected_spans_checked", "not_run")}
- meaning_changes_reviewed: {verification.get("meaning_changes_reviewed", "not_run")}
- render_or_import_checked: {verification.get("render_or_import_checked", "not_run")}
- known_limits: {", ".join(str(item) for item in verification.get("known_limits", []))}

## Change Log

| changed_at_kst | output_path | change_type | notes |
|---|---|---|---|
"""


def create_payload(
    *,
    adaptation_id: str,
    created_at: str,
    workspace_root: Path,
    source: Path,
    preserved: Path,
    mode: str,
    goal: str,
    target_file_type: str,
    target_format: str,
    target_reader: str,
    output_language: str,
    content_depth: str,
    execution_control_mode: str,
) -> dict[str, object]:
    tier = support_tier(source)
    known_limits: list[str] = []
    if tier == "tier_2_with_limitations":
        known_limits.append("Tier 2 input: extraction, layout, tables, speaker notes, formulas, or render fidelity may need manual review.")
    if tier == "unsupported_requires_plan":
        known_limits.append("Unsupported input type: inspect and agree on a safe handling plan before rewriting.")
    return {
        "schema_version": "1.0",
        "adaptation_id": adaptation_id,
        "created_at_kst": created_at,
        "source": {
            "original_path": source_reference(source, workspace_root),
            "preserved_copy_path": rel(preserved, workspace_root),
            "sha256": sha256(source),
            "file_size_bytes": source.stat().st_size,
            "file_type": source.suffix.lower().lstrip(".") or "none",
            "support_tier": tier,
        },
        "request": {
            "goal": goal,
            "adaptation_mode": mode,
            "target_file_type": target_file_type,
            "target_format_or_template": target_format,
            "target_reader": target_reader,
            "output_language": output_language,
            "content_depth": content_depth,
            "execution_control_mode": execution_control_mode,
        },
        "outputs": [],
        "verification": {
            "original_preserved": True,
            "output_opens": "not_run",
            "target_format_followed": "not_run",
            "protected_spans_checked": "not_run",
            "meaning_changes_reviewed": "not_run",
            "render_or_import_checked": "not_run",
            "known_limits": known_limits,
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Preserve a source file and create a document adaptation plan/manifest.")
    parser.add_argument("--project", required=True, help="Project folder name or path under 00_사용자_작업공간.")
    parser.add_argument("--source", required=True, help="Source file path, absolute or relative to the project/workspace root.")
    parser.add_argument("--goal", required=True, help="User-facing adaptation goal.")
    parser.add_argument("--mode", default="undecided", choices=sorted(MODES), help="Adaptation mode.")
    parser.add_argument("--target-file-type", default="undecided", help="Requested output file type, such as docx/html/md/pdf.")
    parser.add_argument("--target-format", default="undecided", help="Target template, preset, or document shape.")
    parser.add_argument("--target-reader", default="undecided", help="Reader or use case.")
    parser.add_argument("--output-language", default="undecided", help="ko, en, mixed, or undecided.")
    parser.add_argument("--content-depth", default="standard", choices=["concise", "standard", "expanded", "undecided"])
    parser.add_argument("--execution-control-mode", default="checkpointed", choices=["checkpointed", "delegated", "undecided"])
    parser.add_argument("--dry-run", action="store_true", help="Show planned paths without writing files.")
    args = parser.parse_args()

    workspace_root = Path.cwd().resolve()
    project = resolve_project(args.project, workspace_root)
    source = resolve_source(args.source, project, workspace_root)
    stamp = now_kst().strftime("%Y%m%d%H%M%S")
    adaptation_id = f"adapt_{stamp}_{safe_stem(source.stem)}"

    documents = project / "documents"
    intake_dir = documents / "intake"
    plan_dir = documents / "adaptation_plans"
    adapted_dir = documents / "adapted"
    versions_dir = documents / "versions"
    preserved = intake_dir / f"{adaptation_id}{source.suffix.lower()}"
    manifest_path = plan_dir / f"{adaptation_id}.manifest.json"
    plan_path = plan_dir / f"{adaptation_id}.plan.md"

    payload = create_payload(
        adaptation_id=adaptation_id,
        created_at=now_kst().strftime("%Y-%m-%dT%H:%M:%S%z"),
        workspace_root=workspace_root,
        source=source,
        preserved=preserved,
        mode=args.mode,
        goal=args.goal,
        target_file_type=args.target_file_type,
        target_format=args.target_format,
        target_reader=args.target_reader,
        output_language=args.output_language,
        content_depth=args.content_depth,
        execution_control_mode=args.execution_control_mode,
    )

    result = {
        "status": "dry_run" if args.dry_run else "created",
        "adaptation_id": adaptation_id,
        "project": rel(project, workspace_root),
        "source": source_reference(source, workspace_root),
        "support_tier": payload["source"]["support_tier"] if isinstance(payload["source"], dict) else "",
        "paths": {
            "preserved_copy": rel(preserved, workspace_root),
            "manifest": rel(manifest_path, workspace_root),
            "plan": rel(plan_path, workspace_root),
            "adapted_dir": rel(adapted_dir, workspace_root),
            "versions_dir": rel(versions_dir, workspace_root),
        },
    }

    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    for path in [intake_dir, plan_dir, adapted_dir, versions_dir]:
        path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, preserved)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    plan_path.write_text(plan_markdown(payload), encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from validate_report_factory import validate_project as validate_report_factory_project
from validate_reference_register_consistency import validate_project as validate_reference_registers


PROJECT_ROOT = Path("00_사용자_작업공간")
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".tsv"}
PLAN_DATA_FILENAMES = {"visual_plan.csv"}


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S KST")


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


def visual_pass_current(project: Path, body_chapters: list[Path]) -> tuple[bool, str]:
    manifest = project / "reports" / "visual_pass_manifest.json"
    review_note = project / "reports" / "visual_review.md"
    latest_body_mtime = max((path.stat().st_mtime_ns for path in body_chapters), default=0)
    if not manifest.exists():
        if review_note.exists() and review_note.stat().st_mtime_ns >= latest_body_mtime:
            return True, ""
        return False, "reports/visual_review.md or reports/visual_pass_manifest.json"
    data = read_json(manifest)
    recorded = data.get("body_chapter_integrity")
    if not isinstance(recorded, list) or not recorded:
        return False, "visual_pass_manifest.json has no body_chapter_integrity"
    recorded_paths = {
        str(item.get("path", "")): str(item.get("sha256", ""))
        for item in recorded
        if isinstance(item, dict)
    }
    import hashlib

    for chapter in body_chapters:
        rel_path = rel(chapter, project)
        digest = hashlib.sha256(chapter.read_bytes()).hexdigest()
        if recorded_paths.get(rel_path) != digest:
            return False, f"visual pass is stale for {rel_path}"
    return True, ""


def chapter_quality_current(project: Path, chapters: list[Path], workpacks: list[Path]) -> tuple[bool, str, dict[str, object]]:
    status_path = project / "reports" / "chapter_quality" / "chapter_quality.json"
    if not chapters:
        return False, "reports/chapters/ch*.html", {}
    if not status_path.exists():
        return False, "reports/chapter_quality/chapter_quality.json", {}
    latest_input_mtime = max((path.stat().st_mtime_ns for path in [*chapters, *workpacks] if path.exists()), default=0)
    if status_path.stat().st_mtime_ns < latest_input_mtime:
        return False, "reports/chapter_quality/chapter_quality.json is stale", read_json(status_path)
    data = read_json(status_path)
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    if data.get("skill_action_required"):
        return False, "chapter quality hook requires report_reviewer/chapter_writer action", data
    if int(summary.get("needs_attention", 0) or 0) > 0:
        return False, "chapter quality review has needs_attention chapters", data
    if int(summary.get("missing_workpacks", 0) or 0) > 0:
        return False, "chapter quality review has missing workpacks", data
    if int(summary.get("chapters_checked", 0) or 0) < len(chapters):
        return False, "chapter quality review did not check all chapter fragments", data
    return True, "", data


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def rel(path: Path, base: Path) -> str:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def first_files(path: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(sorted(path.glob(pattern)))
    unique: list[Path] = []
    seen: set[Path] = set()
    for file in files:
        resolved = file.resolve()
        if resolved not in seen and file.is_file():
            seen.add(resolved)
            unique.append(file)
    return unique


def count_markdown_rows(path: Path) -> int:
    if not path.exists():
        return 0
    rows = 0
    for raw in read_text(path).splitlines():
        line = raw.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows += 1
    return max(0, rows - 1)


def source_record_count(project: Path) -> int:
    source_dir = project / "references" / "source_records"
    return len(list(source_dir.glob("*.md"))) if source_dir.exists() else 0


def active_report(project: Path) -> tuple[Path | None, str]:
    manifests = [
        project / "reports" / "report_assembly_manifest.json",
        project / "project_state" / "report_stage_manifest.json",
    ]
    for manifest in manifests:
        data = read_json(manifest)
        for key in ("active_report", "report_path", "current_report", "output"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                candidate = project / value.strip()
                if candidate.exists() and candidate.is_file():
                    return candidate, f"{rel(manifest, project)}:{key}"
    reports = [
        path
        for path in sorted((project / "reports").glob("*.html"))
        if "quality_status" not in path.as_posix().lower()
        and "source_status" not in path.as_posix().lower()
        and "workflow_status" not in path.as_posix().lower()
        and "outbox" not in path.as_posix().lower()
    ]
    return (reports[-1], "latest_html_fallback") if reports else (None, "")


def has_chapter0(project: Path, report: Path | None) -> bool:
    candidates = list((project / "reports" / "chapters").glob("ch00*.html"))
    if report and report.exists():
        candidates.append(report)
    pattern = re.compile(
        r"(?:제\s*0\s*장|chapter\s*0)[^\n<]{0,80}(?:요약|executive\s*summary)"
        r"|(?:요약|executive\s*summary)[^\n<]{0,40}(?:제\s*0\s*장|chapter\s*0)",
        flags=re.I,
    )
    return any(pattern.search(read_text(path)) for path in candidates)


def run_probe(command: list[str]) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, *command],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": "python " + " ".join(command),
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-1000:],
    }


def drafting_preflight(project_name: str) -> tuple[bool, dict[str, object]]:
    probe = run_probe(["_ai_system/tools/report_preflight.py", "--project", project_name, "--for-drafting"])
    payload: dict[str, object] = {}
    try:
        loaded = json.loads(str(probe.get("stdout_tail", "") or "{}"))
        if isinstance(loaded, dict):
            payload = loaded
    except json.JSONDecodeError:
        payload = {}
    payload["_probe"] = probe
    exit_code = probe.get("exit_code", 1)
    return isinstance(exit_code, int) and exit_code == 0, payload


def recommended_for(action: str, project_name: str, next_chapter: str) -> list[str]:
    commands_by_action = {
        "create_report_prd": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage interview --write-packet",
        ],
        "create_detailed_toc": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage architect --write-packet",
        ],
        "create_source_collection_plan": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage source --write-packet",
        ],
        "review_detailed_toc": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage architect --write-packet",
        ],
        "create_major_skeleton": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage architect --write-packet",
            f"python _ai_system/tools/report_skeleton_score.py --project {project_name}",
        ],
        "map_sources_and_claims": [
            f"python _ai_system/tools/build_project_context_db.py --project {project_name}",
            f"python _ai_system/tools/report_preflight.py --project {project_name} --for-drafting",
            f"python _ai_system/tools/validate_reference_register_consistency.py --project {project_name}",
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage source --write-packet",
        ],
        "create_chapter_workpacks": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage architect --write-packet",
            f"python _ai_system/tools/validate_report_factory.py --project {project_name}",
        ],
        "draft_chapter_fragments": [
            f"python _ai_system/tools/build_project_context_db.py --project {project_name}",
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage chapter --chapter {next_chapter} --write-packet",
        ],
        "run_chapter_quality_review": [
            f"python _ai_system/tools/report_chapter_quality_coach.py --project {project_name} --write-status",
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage review --write-packet",
        ],
        "create_visual_plan_and_data": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage chart --chapter {next_chapter} --write-packet",
        ],
        "prepare_cover_data": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage assemble --write-packet",
        ],
        "assemble_report": [
            f"python _ai_system/tools/assemble_report.py --project {project_name}",
        ],
        "repair_factory_gaps": [
            f"python _ai_system/tools/validate_report_factory.py --project {project_name} --strict",
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage review --write-packet",
        ],
        "write_chapter0_then_reassemble": [
            f"python _ai_system/tools/compose_report_context.py --project {project_name} --stage chapter --chapter ch00_summary --write-packet",
            f"python _ai_system/tools/assemble_report.py --project {project_name}",
        ],
        "run_review_candidate_gates": [
            f"python _ai_system/tools/run_guarded_step.py --project {project_name} --step review-candidate",
            f"python _ai_system/tools/build_delivery_outbox.py --project {project_name} --dry-run --require-active-report",
        ],
    }
    return commands_by_action.get(action, [])


def prompt_for(action: str, project_name: str, next_chapter: str) -> str:
    task_prefix = (
        "tasks/current_task.md의 active 단계를 먼저 확인하고, "
        "해당 단계의 Read Before Work와 Required Rules 범위 안에서 "
    )
    prompts = {
        "create_report_prd": f"{task_prefix}compose_report_context.py --stage interview --write-packet 결과를 읽은 뒤 {project_name}의 보고서 PRD를 먼저 제안해 주세요. 아직 본문 작성이나 자료 인테이크는 하지 말고, 목적·독자·핵심 질문·범위·증거 기준·산출물만 정리한 뒤 승인 여부를 물어봐 주세요.",
        "create_detailed_toc": f"{task_prefix}compose_report_context.py --stage architect --write-packet 결과를 읽은 뒤 {project_name}의 상세 목차를 작성해 주세요. PRD 범위를 벗어난 결론은 쓰지 말고, 각 장의 질문·필요 원문·예상 claim·필요 시각자료를 함께 매핑해 주세요.",
        "review_detailed_toc": f"{task_prefix}{project_name}의 상세 목차를 PRD 기준으로 셀프 검수해 주세요. 대목차·중목차·소목차가 주제 범위, 정책/법안, 주요 플레이어, 사업기회, 반론, 리스크, 시각자료 후보를 충분히 덮는지 확인하고, 보강안과 함께 사용자 목차 승인을 요청해 주세요. 승인 전에는 근거 수집이나 본문 작성으로 넘어가지 마세요.",
        "create_source_collection_plan": f"{task_prefix}compose_report_context.py --stage source --write-packet 결과를 읽은 뒤 {project_name}의 source collection plan을 작성해 주세요. 공식 링크, 인용 위치 확인, 파일이 필요하지만 사용자가 제공해야 할 자료, source_link_register와 user_requested_materials.md 처리 방식을 구분해 주세요.",
        "create_major_skeleton": f"{task_prefix}compose_report_context.py --stage architect --write-packet 결과를 읽은 뒤 {project_name}의 major skeleton을 작성한 뒤 report_skeleton_score.py로 점검해 주세요. 독자 의사결정, 논지, 증거, 반론, 리스크, 데이터와 시각자료 계획까지만 정리하고 최종 본문은 아직 쓰지 마세요.",
        "map_sources_and_claims": f"{task_prefix}새 참고자료가 있으면 intake_reference_batch.py로 원본 보존과 Docling 정규화를 먼저 처리한 뒤 build_project_context_db.py --project {project_name}로 로컬 색인을 갱신해 주세요. 그 다음 compose_report_context.py --stage source --write-packet 결과를 읽고 출처와 claim register를 보강해 주세요. confirmed_fact나 report_citable로 올리기 전 원문 위치와 보존 상태를 분리해서 기록하고, 본문 작성은 preflight 통과 후 진행해 주세요.",
        "create_chapter_workpacks": f"{task_prefix}compose_report_context.py --stage architect --write-packet 결과를 읽은 뒤 {project_name}의 reports/chapter_workpacks/에 장별 workpack을 만들어 주세요. 각 workpack에는 장 질문, 독자 의사결정, 문단 계획, 증거, claim, 반론, required visuals, 금지할 과장 표현을 넣어 주세요.",
        "draft_chapter_fragments": f"{task_prefix}build_project_context_db.py --project {project_name}로 로컬 색인이 최신인지 확인한 뒤 compose_report_context.py --stage chapter --chapter {next_chapter} --write-packet 결과만 읽고 {project_name}의 {next_chapter}만 작성해 주세요. 필요한 경우 query_project_context.py로 해당 장의 키워드만 조회하고, 원문·claim·visual은 필요한 단위만 읽어 reports/chapters/{next_chapter}.html 조각으로 작성하세요. 큰 HTML 전체를 다시 쓰지 마세요. 초안 작성 후에는 최종 완료나 closeout 통과가 아니라 검수/교차검증이 필요한 내부 초안으로 보고하세요.",
        "run_chapter_quality_review": f"{project_name}의 reports/chapter_quality/chapter_quality.json을 확인하고 report_reviewer 관점으로 needs_attention 장을 검수하세요. 먼저 파일 수정 없이 문제점, 근거 보강, 반론, 리스크, 표·그래프, 참고자료 표시, 표지/독자용 구성의 보완 목록을 작성하세요. 사용자가 고도화를 승인하면 해당 보완 목록을 기준으로 chapter_writer 방식으로 reports/chapters/chNN.html과 데이터/시각자료를 수정하고 다시 chapter quality hook을 실행하세요. 이 단계에서는 전체 AGENTS 재독해 대신 compose_report_context.py --stage review --write-packet 또는 해당 장의 --stage chapter --write-packet 결과만 읽으세요.",
        "create_visual_plan_and_data": f"{task_prefix}compose_report_context.py --stage chart --chapter {next_chapter} --write-packet 결과를 읽은 뒤 {project_name}의 본문 챕터에 맞는 표·차트·다이어그램을 chart builder 방식으로 만드세요. visual_plan.csv의 decision_use에 맞춰 별도 CSV/XLSX 또는 source-record-backed artifact를 만들고, 본문에는 자료: 와 근거 데이터:를 넣어 주세요. 완료 후 reports/visual_review.md 체크리스트에 본문 이후 시각자료 검토 결과를 남기고, 필요할 때만 finalize_visual_pass.py 훅으로 해시 기록을 보조하세요.",
        "prepare_cover_data": f"{task_prefix}compose_report_context.py --stage assemble --write-packet 결과를 읽은 뒤 {project_name}의 reports/cover.data.json을 reusable cover component에 맞춰 작성해 주세요. 표지 코드를 새로 만들지 말고 public_release, team_review, executive_decision, partner_proposal 중 문서 목적에 맞는 cover_preset을 고른 뒤 템플릿 값을 채우고 validate_cover_render.py --write-preview로 확인하세요.",
        "assemble_report": f"{task_prefix}compose_report_context.py --stage assemble --write-packet 결과를 읽은 뒤 {project_name}의 assemble_report.py를 실행해 표지와 챕터 조각을 합쳐 주세요. 조립 단계에서는 본문을 새로 쓰거나 요약하지 말고, 조립 결과와 active_report 선언 여부만 보고해 주세요.",
        "repair_factory_gaps": f"{project_name}의 strict Report Factory 검증 실패를 먼저 고쳐 주세요. 특히 상세 목차의 대목차/중목차/소목차가 reports/chapters/chNN.html 원본 장 파일에 그대로 반영되어 있는지 확인하고, 합본 HTML을 직접 고치지 말고 해당 장 파일을 보강한 뒤 assemble_report.py로 다시 조립해 주세요.",
        "write_chapter0_then_reassemble": f"{task_prefix}compose_report_context.py --stage chapter --chapter ch00_summary --write-packet 결과를 읽은 뒤 {project_name}의 본문·시각자료·리스크가 안정되었는지 확인하고, 마지막으로 ch00_summary / 제0장 요약 조각을 작성한 뒤 assemble_report.py로 다시 조립해 주세요.",
        "run_review_candidate_gates": f"{task_prefix}{project_name}의 review-candidate 검증을 실행하기 전에 파일 수정 없는 보고서 검수/교차검증 결과가 작업로그에 반영되어 있는지 확인해 주세요. workspace validation과 report content validation을 분리해서 보고하고, 실패하면 다음 생산 작업으로 번역해 주세요. 일반 프로젝트 작업 중 _ai_system/ 또는 루트 문서 등 시스템 코어 변경이 감지되면 closeout 대신 core 변경 여부를 별도로 보고하세요.",
    }
    return prompts.get(action, f"{task_prefix}compose_report_context.py 결과만 읽고 {project_name}의 다음 보고서 생산 단계를 점검해 주세요.")


def analyze_project(project_name: str, include_probes: bool = False) -> dict[str, object]:
    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"error": f"project not found: {project_name}"}

    prd_files = first_files(project / "report_prd", ["*.md"])
    toc_files = first_files(project / "drafts", ["*toc*.md", "*목차*.md"])
    toc_review_files = first_files(project / "drafts", ["*toc_review*.md", "*목차*검수*.md", "*목차*승인*.md"])
    source_plan_files = first_files(project / "drafts", ["*source*plan*.md", "*collection*plan*.md"]) + first_files(
        project / "notes", ["*source*plan*.md", "*collection*plan*.md"]
    )
    skeleton_files = first_files(project / "drafts", ["*skeleton*.md", "*골조*.md"]) + first_files(
        project / "reports", ["major_skeleton.md", "*skeleton*.md", "*골조*.md"]
    )
    workpacks = first_files(project / "reports" / "chapter_workpacks", ["ch*_workpack.md"])
    chapters = [path for path in first_files(project / "reports" / "chapters", ["ch*.html"]) if not path.name.startswith("ch00")]
    summary_chapters = first_files(project / "reports" / "chapters", ["ch00*.html"])
    visual_plan = project / "data_sources" / "visual_plan.csv"
    visual_rows = read_csv(visual_plan)
    data_files = [
        path
        for path in sorted((project / "data_sources").glob("*"))
        if path.suffix.lower() in DATA_SUFFIXES and path.name not in PLAN_DATA_FILENAMES
    ]
    cover_data = project / "reports" / "cover.data.json"
    assembly_manifest = project / "reports" / "report_assembly_manifest.json"
    report, report_source = active_report(project)
    visual_pass_ok, visual_pass_issue = visual_pass_current(project, chapters)
    chapter_quality_ok, chapter_quality_issue, chapter_quality_payload = chapter_quality_current(project, [*chapters, *summary_chapters], workpacks)
    factory_status = validate_report_factory_project(project, strict=True, enforce_modern=False)
    factory_errors = factory_status.get("errors", [])
    if not isinstance(factory_errors, list):
        factory_errors = []
    chapter0 = has_chapter0(project, report)
    claims = count_markdown_rows(project / "reports" / "report_claim_register.md")
    sources = source_record_count(project)
    reference_consistency = validate_reference_registers(project)
    reference_consistency_ok = bool(reference_consistency.get("passed"))
    reference_consistency_errors = reference_consistency.get("errors", [])
    if not isinstance(reference_consistency_errors, list):
        reference_consistency_errors = []
    drafting_preflight_ok, drafting_preflight_payload = drafting_preflight(project.name)
    drafting_preflight_errors = drafting_preflight_payload.get("errors", [])
    if not isinstance(drafting_preflight_errors, list):
        drafting_preflight_errors = []
    next_chapter = "ch01"
    if workpacks:
        for workpack in workpacks:
            candidate = workpack.name.replace("_workpack.md", "")
            if candidate.startswith("ch00") and summary_chapters:
                continue
            if candidate.startswith("ch") and not (project / "reports" / "chapters" / f"{candidate}.html").exists():
                next_chapter = candidate
                break

    missing: list[str] = []
    blocked: list[str] = []
    warnings: list[str] = []
    action = "run_review_candidate_gates"
    current_step = "ready_for_review_gates"

    if not prd_files:
        action = "create_report_prd"
        current_step = "scope_not_defined"
        missing.append("report_prd/*.md")
        blocked.append("Do not draft report prose before the report PRD exists.")
    elif not toc_files:
        action = "create_detailed_toc"
        current_step = "prd_exists_toc_missing"
        missing.append("drafts/*toc*.md")
        blocked.append("Do not collect broad sources or draft chapters before the detailed TOC exists.")
    elif not toc_review_files:
        action = "review_detailed_toc"
        current_step = "toc_exists_user_approval_needed"
        missing.append("drafts/*toc_review*.md or recorded TOC approval")
        blocked.append("Do not collect broad sources or draft chapters before substantial-report TOC self-review and user approval.")
    elif not source_plan_files:
        action = "create_source_collection_plan"
        current_step = "toc_exists_source_plan_missing"
        missing.append("drafts/source_collection_plan.md or notes/source_collection_plan.md")
        blocked.append("Do not treat external leads as collected originals before the source collection plan exists.")
    elif not skeleton_files:
        action = "create_major_skeleton"
        current_step = "planning_ready_skeleton_missing"
        missing.append("reports/major_skeleton.md or drafts/*skeleton*.md")
        blocked.append("Do not write full chapter prose before the major skeleton is scored.")
    elif sources == 0 or claims == 0 or not reference_consistency_ok:
        action = "map_sources_and_claims"
        current_step = "evidence_mapping_needed"
        if sources == 0:
            missing.append("references/source_records/*.md")
        if claims == 0:
            missing.append("reports/report_claim_register.md claim rows")
        if not reference_consistency_ok:
            missing.append("reference/source register consistency")
        blocked.append("Do not present material conclusions as confirmed facts until source records and claim rows exist.")
        blocked.append("Do not call the reference library complete while source records, source index, and reference inventory are out of sync.")
    elif not workpacks:
        action = "create_chapter_workpacks"
        current_step = "skeleton_exists_workpacks_missing"
        missing.append("reports/chapter_workpacks/ch*_workpack.md")
        blocked.append("Do not ask the AI to draft from the assembled HTML; create bounded chapter workpacks first.")
    elif not drafting_preflight_ok:
        action = "map_sources_and_claims"
        current_step = "drafting_preflight_needed"
        missing.append("drafting preflight")
        for error in drafting_preflight_errors[:5]:
            missing.append(str(error))
        blocked.append("Do not draft chapter fragments until report_preflight.py --for-drafting passes.")
        blocked.append("Do not manually promote a report stage or cite weak sources just to unlock drafting.")
    elif not chapters:
        action = "draft_chapter_fragments"
        current_step = "workpacks_exist_chapter_fragments_missing"
        missing.append("reports/chapters/ch*.html")
        blocked.append("Do not assemble a substantial report before chapter fragments exist.")
    elif not chapter_quality_ok:
        action = "run_chapter_quality_review"
        current_step = "chapter_fragments_exist_quality_review_required"
        missing.append(chapter_quality_issue)
        blocked.append("Do not move to visual pass, assembly, review-candidate, or closeout until the chapter-quality hook has no required AI review/revision action.")
        blocked.append("Do not treat file count, visible length, or a numeric quality score as a substitute for report_reviewer review.")
    elif not visual_plan.exists() or not visual_rows or not data_files or not visual_pass_ok:
        action = "create_visual_plan_and_data"
        current_step = "chapter_fragments_exist_visuals_incomplete"
        if not visual_plan.exists():
            missing.append("data_sources/visual_plan.csv")
        elif not visual_rows:
            missing.append("visual_plan.csv rows")
        if not data_files:
            missing.append("data_sources/*.csv or *.xlsx backing files")
        if not visual_pass_ok:
            missing.append(visual_pass_issue)
        blocked.append("Do not rely on hard-coded report numbers without backing data/source artifacts.")
        blocked.append("Do not treat the final report as review-ready before table/chart/diagram work is reviewed after body chapters.")
    elif not cover_data.exists():
        action = "prepare_cover_data"
        current_step = "content_exists_cover_data_missing"
        missing.append("reports/cover.data.json")
        blocked.append("Do not recreate cover markup from scratch; choose a cover_preset and populate the reusable cover data file.")
    elif not (report and report.exists()) or not assembly_manifest.exists():
        action = "assemble_report"
        current_step = "components_ready_assembly_missing"
        missing.append("reports/report_assembly_manifest.json and active assembled report")
        blocked.append("Do not call the report review-ready before assemble_report.py declares the active report.")
    elif factory_errors:
        action = "repair_factory_gaps"
        current_step = "strict_factory_gaps_block_review"
        missing.extend(str(item) for item in factory_errors[:8])
        blocked.append("Do not move to review-candidate or closeout while strict Report Factory validation has errors.")
        blocked.append("Do not repair this by editing the assembled HTML directly; fix the relevant chapter source fragment and reassemble.")
    elif not chapter0 or not summary_chapters:
        action = "write_chapter0_then_reassemble"
        current_step = "assembled_report_exists_chapter0_missing"
        missing.append("reports/chapters/ch00_summary.html or visible 제0장 요약")
        blocked.append("Do not write the final executive summary until body chapters, visuals, and risks are stable.")

    if report_source == "latest_html_fallback":
        warnings.append("active report is not declared; latest HTML fallback is unverified for handoff.")
    if visual_plan.exists() and visual_rows and not data_files:
        warnings.append("visual_plan.csv exists, but no local backing data file was found.")
    if sources and sources < 8:
        warnings.append("source record count is below the normal substantial-report signal of 8.")

    probes = []
    if include_probes:
        probes = [
            run_probe(["_ai_system/tools/report_gate_status.py", "--project", project_name]),
            run_probe(["_ai_system/tools/validate_report_factory.py", "--project", project_name]),
        ]

    payload = {
        "project": project_name,
        "generated_at_kst": now_kst(),
        "purpose": "production navigator for report writing; this is not content validation",
        "current_step": current_step,
        "next_action": action,
        "next_chapter": next_chapter,
        "missing_artifacts": missing,
        "allowed_actions": [action, "update worklog/question log when decisions change"],
        "blocked_actions": blocked,
        "recommended_commands": recommended_for(action, project_name, next_chapter),
        "human_prompt": prompt_for(action, project_name, next_chapter),
        "warnings": warnings,
        "metrics": {
            "prd_files": [rel(path, project) for path in prd_files],
            "toc_files": [rel(path, project) for path in toc_files],
            "source_plan_files": [rel(path, project) for path in source_plan_files],
            "skeleton_files": [rel(path, project) for path in skeleton_files],
            "source_records": sources,
            "claim_rows": claims,
            "reference_consistency_ok": reference_consistency_ok,
            "reference_consistency_errors": reference_consistency_errors,
            "drafting_preflight_ok": drafting_preflight_ok,
            "drafting_preflight_errors": drafting_preflight_errors,
            "drafting_preflight_stage": drafting_preflight_payload.get("stage", ""),
            "drafting_preflight_stage_ok": drafting_preflight_ok,
            "chapter_workpacks": len(workpacks),
            "chapter_fragments": len(chapters),
            "summary_chapters": len(summary_chapters),
            "chapter_quality_current": chapter_quality_ok,
            "chapter_quality_issue": chapter_quality_issue,
            "chapter_quality_summary": chapter_quality_payload.get("summary", {}) if isinstance(chapter_quality_payload, dict) else {},
            "visual_plan_rows": len(visual_rows),
            "data_files": len(data_files),
            "visual_pass_current": visual_pass_ok,
            "visual_pass_issue": visual_pass_issue,
            "cover_data": cover_data.exists(),
            "assembly_manifest": assembly_manifest.exists(),
            "strict_factory_errors": len(factory_errors),
            "active_report": rel(report, project) if report else "",
            "active_report_source": report_source,
            "chapter0_present": chapter0,
        },
        "probes": probes,
    }
    return payload


def render_status_html(payload: dict[str, object]) -> str:
    project = html.escape(str(payload.get("project", "")))
    next_action = html.escape(str(payload.get("next_action", "")))
    current_step = html.escape(str(payload.get("current_step", "")))
    prompt = html.escape(str(payload.get("human_prompt", "")))
    missing = payload.get("missing_artifacts", [])
    warnings = payload.get("warnings", [])
    commands = payload.get("recommended_commands", [])
    metrics = payload.get("metrics", {})
    if not isinstance(missing, list):
        missing = []
    if not isinstance(warnings, list):
        warnings = []
    if not isinstance(commands, list):
        commands = []
    if not isinstance(metrics, dict):
        metrics = {}

    def li(items: list[object]) -> str:
        return "\n".join(f"<li>{html.escape(str(item))}</li>" for item in items) or "<li>없음</li>"

    metric_rows = "\n".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value))}</td></tr>"
        for key, value in metrics.items()
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>Report Workflow Status - {project}</title>
  <style>
    :root {{ color-scheme: light; --ink:#1f2933; --muted:#65707d; --line:#d8dee6; --soft:#f5f7fa; --accent:#1f6feb; --warn:#9a5b00; }}
    body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:#fff; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 40px 28px 56px; }}
    header {{ border-bottom: 2px solid var(--ink); padding-bottom: 18px; margin-bottom: 24px; }}
    h1 {{ margin:0 0 8px; font-size: 30px; letter-spacing:0; }}
    h2 {{ margin:28px 0 10px; font-size: 18px; }}
    .meta {{ color:var(--muted); }}
    .badge {{ display:inline-block; padding:6px 10px; border:1px solid var(--accent); color:var(--accent); font-weight:700; }}
    .grid {{ display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:16px; }}
    .panel {{ border:1px solid var(--line); background:var(--soft); padding:16px; }}
    pre {{ white-space:pre-wrap; border:1px solid var(--line); padding:14px; background:#fff; overflow:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th, td {{ border:1px solid var(--line); padding:8px 10px; text-align:left; vertical-align:top; }}
    th {{ width:220px; background:var(--soft); }}
    .note {{ color:var(--muted); font-size:14px; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} main {{ padding:28px 18px; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="badge">Workflow Navigator</div>
    <h1>{project}</h1>
    <p class="meta">생성 시각: {html.escape(str(payload.get("generated_at_kst", "")))} · 이 패널은 다음 생산 작업 안내이며, 보고서 내용 검증이 아닙니다.</p>
  </header>
  <section class="grid">
    <div class="panel">
      <h2>현재 단계</h2>
      <p>{current_step}</p>
    </div>
    <div class="panel">
      <h2>다음 작업</h2>
      <p>{next_action}</p>
    </div>
  </section>
  <section>
    <h2>누락 산출물</h2>
    <ul>{li(missing)}</ul>
  </section>
  <section>
    <h2>주의/잔존 리스크</h2>
    <ul>{li(warnings)}</ul>
  </section>
  <section>
    <h2>추천 명령</h2>
    <ul>{li(commands)}</ul>
  </section>
  <section>
    <h2>AI에게 줄 프롬프트</h2>
    <pre>{prompt}</pre>
  </section>
  <section>
    <h2>상태 지표</h2>
    <table>{metric_rows}</table>
  </section>
  <p class="note">workspace validation, research integrity, artifact validation, closeout validation은 별도 검증입니다. 이 패널만으로 review-ready를 주장하지 마세요.</p>
</main>
</body>
</html>
"""


def write_status(project_name: str, payload: dict[str, object]) -> dict[str, str]:
    project = PROJECT_ROOT / project_name
    status_dir = project / "reports" / "workflow_status"
    status_dir.mkdir(parents=True, exist_ok=True)
    json_path = status_dir / "workflow_status.json"
    html_path = status_dir / "workflow_status.html"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    html_path.write_text(render_status_html(payload), encoding="utf-8", newline="\n")
    return {"json": rel(json_path, project), "html": rel(html_path, project)}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Suggest the next report-factory production action for one project.")
    parser.add_argument("--project", required=True, help="Project folder name under 00_사용자_작업공간")
    parser.add_argument("--write-status", action="store_true", help="Write reports/workflow_status/workflow_status.json and .html")
    parser.add_argument("--include-probes", action="store_true", help="Also run lightweight gate/factory probes")
    args = parser.parse_args()

    payload = analyze_project(args.project, include_probes=args.include_probes)
    if args.write_status and "error" not in payload:
        payload["status_files"] = write_status(args.project, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if "error" in payload else 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_report_workflow_next"


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


def base_project(project: Path) -> None:
    remove_smoke_project(project)
    for folder in [
        "report_prd",
        "drafts",
        "notes",
        "reports",
        "references/source_records",
        "source_index",
        "data_sources",
        "project_state",
    ]:
        (project / folder).mkdir(parents=True, exist_ok=True)
    (project / "reports" / "report_claim_register.md").write_text(
        "| claim_id | claim_type | status | source_ids | citation_type | exact_location |\n|---|---|---|---|---|---|\n",
        encoding="utf-8",
        newline="\n",
    )


def write_prd_toc_source_plan(project: Path) -> None:
    (project / "report_prd" / "smoke_prd.md").write_text(
        "# Smoke PRD\n\nSubstantial internal review report for smoke testing.\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "drafts" / "smoke_toc.md").write_text(
        "# Smoke Detailed TOC\n\n## 제1장 테스트\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "drafts" / "smoke_toc_review.md").write_text(
        "# TOC Review\n\nCoverage checked and approval recorded for smoke testing.\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "drafts" / "source_collection_plan.md").write_text(
        "# Source Collection Plan\n\nRecord official links, source locators, and user-needed files before drafting.\n",
        encoding="utf-8",
        newline="\n",
    )


def write_sources_claims(project: Path) -> None:
    (project / "references" / "source_records" / "src_001.md").write_text(
        "# Source Record\n\n- source_id: src_001\n- status: working_note\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "references" / "reference_inventory.csv").write_text(
        "source_id,title,status,url_or_path\n"
        "src_001,Smoke Source,working_note,evidence/web_captures/src_001.txt\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "source_index" / "source_master_index.md").write_text(
        "| source_id | title | status | original_verified | url_or_path |\n"
        "|---|---|---|---|---|\n"
        "| src_001 | Smoke Source | working_note | no | evidence/web_captures/src_001.txt |\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "reports" / "report_claim_register.md").write_text(
        "| claim_id | claim_type | status | source_ids | citation_type | exact_location |\n"
        "|---|---|---|---|---|---|\n"
        "| claim_001 | working | draft | src_001 | paraphrase | p.1 |\n",
        encoding="utf-8",
        newline="\n",
    )


def write_skeleton(project: Path) -> None:
    (project / "reports" / "major_skeleton.md").write_text(
        "# Major Skeleton\n\n## Chapter plan\n\n- ch01: decision question, evidence, claims, counterarguments, visuals.\n",
        encoding="utf-8",
        newline="\n",
    )


def write_workpack(project: Path) -> None:
    (project / "reports" / "chapter_workpacks").mkdir(parents=True, exist_ok=True)
    (project / "reports" / "chapter_workpacks" / "ch01_workpack.md").write_text(
        "# ch01 Workpack\n\n"
        "## 1. Reader Decision\nDecide the smoke path.\n\n"
        "## 2. Reader Takeaway\nUnderstand the next action.\n\n"
        "## 3. Core Question\nWhat should happen next?\n\n"
        "## 4. Required Answer Boundary\nNo final conclusions.\n\n"
        "## 5. Paragraph Plan\n- Explain evidence.\n\n"
        "## 6. Evidence Inputs\n| source_id | source title | exact location needed | use in chapter |\n|---|---|---|---|\n| src_001 | Smoke | p.1 | proof |\n\n"
        "## 7. Claim Register Links\n| claim_id | use |\n|---|---|\n| claim_001 | support |\n\n"
        "## 8. Assumptions and Estimates\n| assumption_id | note |\n|---|---|\n| asm_001 | smoke |\n\n"
        "## 9. Counterarguments\n- Include residual risk.\n\n"
        "## 10. Required Visuals\n| visual_id | use |\n|---|---|\n| vis_001 | decision |\n\n"
        "## 11. Forbidden Claims\n- No overclaim.\n\n"
        "## 12. Completion Checklist\n- Captions checked.\n\n"
        + ("This smoke workpack deliberately includes enough detail to satisfy the strict factory check. " * 18),
        encoding="utf-8",
        newline="\n",
    )


def allow_drafting(project: Path) -> None:
    (project / "project_state" / "report_stage_manifest.json").write_text(
        json.dumps({"project": project.name, "stage": "draft_allowed"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    (project / "source_index" / "source_master_index.md").write_text(
        "| source_id | title | status | original_verified | url_or_path |\n"
        "|---|---|---|---|---|\n"
        "| src_001 | Smoke Source | report_citable | yes | evidence/web_captures/src_001.txt |\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "references" / "reference_inventory.csv").write_text(
        "source_id,title,status,url_or_path\n"
        "src_001,Smoke Source,report_citable,evidence/web_captures/src_001.txt\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "references" / "source_records" / "src_001.md").write_text(
        "# Source Record\n\n"
        "- source_id: src_001\n"
        "- title: Smoke Source\n"
        "- status: report_citable\n"
        "- source_readiness_status: report_citable\n"
        "- original_verified: yes\n"
        "- url_or_path: evidence/web_captures/src_001.txt\n\n"
        "## 2. Exact Quotes\n\n"
        "> Smoke source quote.\n\n"
        "## 3. Notes\n\n"
        + ("Audit detail for workflow smoke. " * 60),
        encoding="utf-8",
        newline="\n",
    )
    (project / "reports" / "report_claim_register.md").write_text(
        "| claim_id | claim_type | status | source_ids | citation_type | exact_quote_location |\n"
        "|---|---|---|---|---|---|\n"
        "| claim_001 | confirmed_fact | report_citable | src_001 | direct_quote | evidence/web_captures/src_001.txt |\n",
        encoding="utf-8",
        newline="\n",
    )


def write_chapter(project: Path) -> None:
    (project / "reports" / "chapters").mkdir(parents=True, exist_ok=True)
    (project / "reports" / "chapters" / "ch01.html").write_text(
        "<section id=\"ch01\"><h2>제1장 테스트</h2><p>본문 조각입니다.</p></section>\n",
        encoding="utf-8",
        newline="\n",
    )


def write_chapter_quality(project: Path) -> None:
    chapters = sorted((project / "reports" / "chapters").glob("ch*.html"))
    quality_dir = project / "reports" / "chapter_quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    (quality_dir / "chapter_quality.json").write_text(
        json.dumps(
            {
                "summary": {
                    "chapters_checked": len(chapters),
                    "needs_attention": 0,
                    "missing_workpacks": 0,
                },
                "skill_action_required": False,
                "chapters": [{"path": path.as_posix(), "status": "strong_signal"} for path in chapters],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )


def write_enhancement_log(project: Path) -> None:
    quality_dir = project / "reports" / "chapter_quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    (quality_dir / "enhancement_log.md").write_text(
        "# Chapter Enhancement Log\n\n"
        "- review_status: cross-check complete\n"
        "- user_approved_changes: none for smoke fixture\n"
        "- no_change_rationale: chapter fixture is intentionally minimal but structurally complete for workflow smoke.\n",
        encoding="utf-8",
        newline="\n",
    )


def write_visuals_cover_assembly(project: Path, include_summary: bool) -> None:
    (project / "data_sources" / "visual_plan.csv").write_text(
        "visual_id,chapter,visual_type,title,purpose,decision_use,expected_reader_takeaway,required,data_file,source_record,status\n"
        "vis_001,ch01,chart,Smoke Chart,Show decision,Choose next action,Understand flow,yes,data_sources/vis_001.csv,,planned\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "data_sources" / "vis_001.csv").write_text("label,value\nA,1\n", encoding="utf-8", newline="\n")
    (project / "reports" / "visual_review.md").write_text(
        "# Visual Review\n\n- Body chapters reviewed after drafting.\n- Visual data file exists.\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "reports" / "cover.data.json").write_text(
        json.dumps({"report_title": "Smoke Report", "report_no": "SMOKE-001", "date": "2026-05-24"}, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    if include_summary:
        (project / "reports" / "chapter_workpacks" / "ch00_summary_workpack.md").write_text(
            "# ch00 Summary Workpack\n\n"
            "## 1. Reader Decision\nConfirm the final executive synthesis.\n\n"
            "## 2. Reader Takeaway\nUnderstand the final action sequence.\n\n"
            "## 3. Core Question\nWhat should the reader do after the body evidence is stable?\n\n"
            "## 4. Required Answer Boundary\nSummarize only body-supported findings.\n\n"
            "## 5. Paragraph Plan\n- Synthesize the body.\n- Name residual risk.\n\n"
            "## 6. Evidence Inputs\n| source_id | source title | exact location needed | use in chapter |\n|---|---|---|---|\n| src_001 | Smoke | p.1 | final synthesis |\n\n"
            "## 7. Claim Register Links\n| claim_id | use |\n|---|---|\n| claim_001 | synthesis |\n\n"
            "## 8. Assumptions and Estimates\n| assumption_id | note |\n|---|---|\n| asm_001 | smoke |\n\n"
            "## 9. Counterarguments\n- Do not hide unresolved risk.\n\n"
            "## 10. Required Visuals\n| visual_id | use |\n|---|---|\n| vis_001 | summary reference |\n\n"
            "## 11. Forbidden Claims\n- No unsupported final recommendation.\n\n"
            "## 12. Completion Checklist\n- Body evidence checked.\n\n"
            + ("This smoke summary workpack is intentionally detailed enough for strict factory validation. " * 18),
            encoding="utf-8",
            newline="\n",
        )
        (project / "reports" / "chapters" / "ch00_summary.html").write_text(
            "<section id=\"ch00\"><h1>제0장 요약</h1><p>마지막 요약입니다.</p></section>\n",
            encoding="utf-8",
            newline="\n",
        )
    write_assembly(project)


def write_assembly(project: Path) -> None:
    report_text = "<!doctype html><html lang=\"ko\"><body data-assembled-report=\"true\"><main>"
    chapters = sorted((project / "reports" / "chapters").glob("ch*.html"))
    for chapter in chapters:
        report_text += chapter.read_text(encoding="utf-8", errors="ignore")
    report_text += "</main></body></html>\n"
    style_dir = project / "reports" / "style_pass"
    style_pass_artifacts = [
        {
            "path": (style_dir / filename).relative_to(project).as_posix(),
            "sha256": hashlib.sha256((style_dir / filename).read_bytes()).hexdigest(),
        }
        for filename in [
            "style_risk_findings.json",
            "protected_spans.json",
            "style_rewrite_diff.md",
            "style_fidelity_review.md",
            "style_naturalness_review.md",
        ]
        if (style_dir / filename).exists()
    ]
    (project / "reports" / "internal_review_report.html").write_text(report_text, encoding="utf-8", newline="\n")
    (project / "reports" / "report_assembly_manifest.json").write_text(
        json.dumps(
            {
                "active_report": "reports/internal_review_report.html",
                "assembly_mode": "concatenate_only_no_rewrite",
                "chapter_integrity": [
                    {
                        "path": path.relative_to(project).as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in chapters
                ],
                "style_pass_artifacts": style_pass_artifacts,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )


def write_style_pass(project: Path) -> None:
    style_dir = project / "reports" / "style_pass"
    style_dir.mkdir(parents=True, exist_ok=True)
    (style_dir / "style_risk_findings.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "scope": "pre_assembly_after_chapter0",
                "findings": [],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (style_dir / "protected_spans.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "protected_spans": [
                    {"span_type": "number", "text": "SMOKE-001", "action": "preserve"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (style_dir / "style_rewrite_diff.md").write_text(
        "# Style Rewrite Diff\n\nNo wording change needed for this smoke fixture.\n",
        encoding="utf-8",
        newline="\n",
    )
    (style_dir / "style_fidelity_review.md").write_text(
        "# Style Fidelity Review\n\nResult: pass. No meaning, evidence, or protected span changed.\n",
        encoding="utf-8",
        newline="\n",
    )
    (style_dir / "style_naturalness_review.md").write_text(
        "# Style Naturalness Review\n\nResult: pass. Reader-fit tone is acceptable without additional polish.\n",
        encoding="utf-8",
        newline="\n",
    )


def workflow_action(project: Path, write_status: bool = False) -> tuple[int, dict[str, object]]:
    command = ["_ai_system/tools/report_workflow_next.py", "--project", SMOKE_PROJECT]
    if write_status:
        command.append("--write-status")
    proc = run(command)
    return proc.returncode, parse_payload(proc)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        base_project(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "empty_project_requests_prd",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "create_report_prd",
                "payload": payload,
            }
        )

        write_prd_toc_source_plan(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "prd_toc_source_plan_requests_source_claim_mapping",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "map_sources_and_claims",
                "payload": payload,
            }
        )

        write_sources_claims(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "source_claim_mapping_requests_skeleton",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "create_major_skeleton",
                "payload": payload,
            }
        )

        write_skeleton(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "skeleton_requests_workpacks",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "create_chapter_workpacks",
                "payload": payload,
            }
        )

        write_workpack(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "workpack_without_drafting_gate_requests_source_claim_repair",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "map_sources_and_claims",
                "payload": payload,
            }
        )

        allow_drafting(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "workpack_with_drafting_gate_requests_chapter_fragment",
                "exit_code": code,
                "passed": code == 0
                and payload.get("next_action") == "draft_chapter_fragments"
                and payload.get("metrics", {}).get("drafting_preflight_stage_ok") is True,
                "payload": payload,
            }
        )

        write_chapter(project)
        write_chapter_quality(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "chapter_quality_requests_enhancement",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "enhance_chapter_fragments",
                "payload": payload,
            }
        )

        write_enhancement_log(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "enhanced_chapter_requests_visuals",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "create_visual_plan_and_data",
                "payload": payload,
            }
        )

        write_visuals_cover_assembly(project, include_summary=False)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "assembled_without_summary_requests_chapter0",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "write_chapter0_summary",
                "payload": payload,
            }
        )

        write_visuals_cover_assembly(project, include_summary=True)
        write_chapter_quality(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "chapter0_without_style_pass_requests_pre_assembly_style",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "run_pre_assembly_style_pass",
                "payload": payload,
            }
        )

        write_style_pass(project)
        code, payload = workflow_action(project)
        results.append(
            {
                "case": "style_pass_without_reassembly_requests_assembly",
                "exit_code": code,
                "passed": code == 0 and payload.get("next_action") == "assemble_report",
                "payload": payload,
            }
        )

        write_assembly(project)
        code, payload = workflow_action(project, write_status=True)
        status_files = payload.get("status_files") if isinstance(payload.get("status_files"), dict) else {}
        results.append(
            {
                "case": "complete_flow_requests_review_gates_and_writes_status",
                "exit_code": code,
                "passed": code == 0
                and payload.get("next_action") == "run_review_candidate_gates"
                and (project / str(status_files.get("html", ""))).exists()
                and (project / str(status_files.get("json", ""))).exists(),
                "payload": payload,
            }
        )
    finally:
        remove_smoke_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

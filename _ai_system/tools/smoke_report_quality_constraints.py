from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_report_quality_constraints"


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


def parse_json(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON:\n{proc.stdout}\n{proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise AssertionError("payload was not a JSON object")
    return payload


def remove_project(project: Path) -> None:
    if not project.exists():
        return
    root = PROJECT_ROOT.resolve()
    target = project.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {target}") from exc
    shutil.rmtree(target)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def long_korean_text() -> str:
    sentence = (
        "이 장은 독자의 의사결정에 필요한 사실, 해석, 반론, 잔존 리스크, 실행 함의를 구분하여 "
        "충분히 설명하는 테스트 문장입니다. "
    )
    return sentence * 520


def write_common_quality_fixture(project: Path) -> None:
    write_text(project / "report_prd" / "smoke_report_prd.md", "# 내부 검토 보고서 PRD\n\nsubstantial internal review report\n")
    write_text(project / "drafts" / "smoke_toc.md", "# 상세 목차\n\n## 제0장 요약\n## 제1장 본문\n")

    inventory_rows = ["source_id,title,original_path,sha256,file_size_bytes"]
    for idx in range(1, 11):
        inventory_rows.append(f"src_{idx:03d},Official Source {idx},references/received_originals/src_{idx:03d}.pdf,{'a'*64},{4096+idx}")
    write_text(project / "references" / "reference_inventory.csv", "\n".join(inventory_rows) + "\n")

    source_index_rows = ["| source_id | status |", "|---|---|"]
    for idx in range(1, 7):
        source_id = f"src_{idx:03d}"
        source_index_rows.append(f"| {source_id} | report_citable |")
        record = (
            f"# Source Record {idx}\n\n"
            f"- source_id: {source_id}\n"
            f"- title: Official Source {idx}\n"
            "- exact_quote_location: p. 1\n\n"
            "## 2. Exact Quotes\n\n"
            "> 이 공식 문서는 보고서 테스트를 위한 원문 인용 위치를 제공합니다.\n\n"
            + ("원문 보존 설명입니다. " * 90)
        )
        write_text(project / "references" / "source_records" / f"{source_id}.md", record)
    write_text(project / "source_index" / "source_master_index.md", "\n".join(source_index_rows) + "\n")

    claim_rows = ["| claim_id | source_ids | exact_quote_location | status |", "|---|---|---|---|"]
    for idx in range(1, 6):
        claim_rows.append(f"| claim_{idx:03d} | src_{idx:03d} | p. 1 | confirmed_fact |")
    write_text(project / "reports" / "report_claim_register.md", "\n".join(claim_rows) + "\n")

    visual_plan_rows = [
        "visual_id,chapter,visual_type,title,purpose,decision_use,expected_reader_takeaway,required,data_file,source_data,source_record,status,notes",
        "vis_001,ch01,chart,Scenario chart,Compare strategic options,Choose the lower-risk option,Option B is operationally safer,yes,data_sources/vis_001.csv,data_sources/vis_001.csv,references/source_records/src_001.md,planned,",
        "vis_002,ch01,diagram,Process map,Show control flow,Identify handoff risk,More handoffs create more controls,yes,data_sources/vis_002.csv,data_sources/vis_002.csv,references/source_records/src_002.md,planned,",
        "vis_003,ch01,table,Risk matrix,Prioritize risks,Select mitigation priority,Regulatory risk dominates,yes,data_sources/vis_003.csv,data_sources/vis_003.csv,references/source_records/src_003.md,planned,",
        "vis_004,ch01,chart,Timeline,Sequence delivery steps,Decide next milestone,Evidence collection should precede drafting,yes,data_sources/vis_004.csv,data_sources/vis_004.csv,references/source_records/src_004.md,planned,",
    ]
    write_text(project / "data_sources" / "visual_plan.csv", "\n".join(visual_plan_rows) + "\n")
    for idx in range(1, 5):
        write_text(project / "data_sources" / f"vis_{idx:03d}.csv", "label,value\nA,1\nB,2\n")

    html = f"""<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><title>Smoke Report</title><!-- report.css --></head>
<body>
<main>
<section data-cover-component="report-cover-v1"><h1>Smoke Report</h1></section>
<section><h2>제0장 요약</h2><p>최종 요약입니다.</p></section>
<section><h2>제1장 본문</h2><p>{long_korean_text()}</p></section>
<figure class="chart"><svg><text>chart</text></svg><figcaption>자료: src_001. 근거 데이터: 시나리오 차트 데이터</figcaption><!-- data_file: data_sources/vis_001.csv --></figure>
<figure class="diagram"><svg><text>diagram</text></svg><figcaption>자료: src_002. 근거 데이터: 프로세스맵 데이터</figcaption><!-- data_file: data_sources/vis_002.csv --></figure>
<table><caption>자료: src_003. 근거 데이터: 리스크 매트릭스 데이터</caption><!-- data_file: data_sources/vis_003.csv --><tr><td>A</td></tr></table>
<table><caption>자료: src_004. 근거 데이터: 타임라인 데이터</caption><!-- data_file: data_sources/vis_004.csv --><tr><td>B</td></tr></table>
<section><h2>부록</h2><p>Appendix source list.</p></section>
</main>
</body>
</html>
"""
    write_text(project / "reports" / "internal_review_report.html", html)


def add_chapter_factory(project: Path) -> None:
    def workpack_text(chapter_id: str, title: str) -> str:
        return f"""# {title} Workpack

## 1. Chapter Identity

- chapter_id: {chapter_id}
- chapter_title: {title}
- matching_fragment: `reports/chapters/{chapter_id}.html`
- status: drafted

## 2. Reader Decision Supported

- Decide whether the report argument is supported enough for the smoke scenario.

## 2A. Reader Takeaway

- The reader should see that chapter workpacks are substantive writing briefs, not placeholders.

## 3. Core Question

- Does this chapter answer a bounded decision question with evidence, caveats, and visuals?

## 4. Required Answer Boundary

- Allowed conclusion range: The smoke fixture can show the factory signal works.
- Must-not-overstate: Do not claim real report truth from a smoke fixture.
- Counsel/business review markers: Not applicable; fixture only.

## 4A. Paragraph Plan

| paragraph/block | job in the argument | evidence or visual to use | reader-facing output |
|---|---|---|---|
| 1 | State the chapter answer | src_001 | bounded prose |
| 2 | Explain uncertainty | claim_001 | residual risk |

## 5. Evidence Inputs

| source_id | source title | exact location needed | use in chapter |
|---|---|---|---|
| src_001 | Official Source 1 | p. 1 | anchor the smoke claim |

## 6. Claim Register Links

| claim_id | claim_type | intended paragraph/section | status |
|---|---|---|---|
| claim_001 | Fact | paragraph 1 | confirmed_fact |

## 7. Assumptions and Estimates

| assumption_id | estimate/data need | sensitivity or caveat |
|---|---|---|
| asm_001 | fixture assumption | not a real report claim |

## 8. Counterarguments and Residual Risks

- Counterargument 1: A fixture can pass without proving real business truth.
- Counterargument 2: Human review remains necessary.
- Residual risk to keep visible: Validators can miss domain-specific quality problems.
- Evidence limit: synthetic smoke data only.
- What would change the conclusion: real project evidence contradicting the fixture.

## 9. Required Visuals

These should also appear in `data_sources/visual_plan.csv`.

| visual_id | visual_type | purpose | data/source artifact | status |
|---|---|---|---|---|
| vis_001 | chart | compare options | data_sources/vis_001.csv | planned |

## 9A. Figure/Table Integration Notes

- Where the visual appears: body section.
- Caption `자료:`: src_001.
- Caption `근거 데이터:`: data_sources/vis_001.csv.
- How the prose interprets the visual: bounded fixture interpretation.

## 10. Appendix and Glossary Needs

- Appendix item: fixture source list.
- Glossary terms: smoke, factory.

## 11. Forbidden Claims or Tone

- Do not claim: this fixture proves real report quality.
- Avoid over-certainty terms: perfect, guaranteed.
- Required uncertainty language: smoke-test only.

## 12. Completion Checklist

- [x] The core question is answered.
- [x] The reader takeaway is explicit.
- [x] The paragraph plan was followed or deliberately updated.
- [x] Evidence and interpretation are separated.
- [x] Material claims are in the claim register.
- [x] Required visuals have data/source artifacts.
- [x] Counterarguments and residual risks are visible.
- [x] Internal ids are comments only, not reader-facing prose.
- [x] Chapter fragment has no `<html>`, `<head>`, or `<body>` wrapper.
"""

    write_text(project / "reports" / "cover.data.json", "{}\n")
    write_text(project / "reports" / "chapter_workpacks" / "ch00_summary_workpack.md", workpack_text("ch00_summary", "Summary"))
    write_text(project / "reports" / "chapter_workpacks" / "ch01_workpack.md", workpack_text("ch01", "Chapter 1"))
    write_text(project / "reports" / "chapters" / "ch00_summary.html", "<section><h2>제0장 요약</h2><p>최종 요약입니다.</p></section>\n")
    write_text(project / "reports" / "chapters" / "ch01.html", "<section><h2>제1장 본문</h2><p>본문 조각입니다.</p></section>\n")
    report = project / "reports" / "internal_review_report.html"
    text = report.read_text(encoding="utf-8")
    text = text.replace("<main>", "<!-- mode: concatenate_only_no_rewrite -->\n<main class=\"assembled-report\" data-assembled-report=\"true\">")
    report.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        remove_project(project)
        write_common_quality_fixture(project)
        no_factory_proc = run(["_ai_system/tools/report_quality_score.py", "--project", SMOKE_PROJECT])
        no_factory_payload = parse_json(no_factory_proc)
        no_factory_constraints = no_factory_payload.get("level_constraints")
        results.append(
            {
                "case": "high_scoring_report_without_chapter_factory_stays_below_level4",
                "exit_code": no_factory_proc.returncode,
                "passed": no_factory_proc.returncode == 0
                and no_factory_payload.get("current_level") != "Level 4"
                and isinstance(no_factory_constraints, dict)
                and no_factory_constraints.get("chapter_factory_ok") is False,
                "payload": no_factory_payload,
            }
        )

        weak_visual_plan = project / "data_sources" / "visual_plan.csv"
        weak_visual_plan.write_text(
            "visual_id,chapter,visual_type,title,purpose,decision_use,status\nvis_bad,ch01,chart,Bad visual,,,planned\n",
            encoding="utf-8",
            newline="\n",
        )
        weak_factory_proc = run(["_ai_system/tools/validate_report_factory.py", "--project", SMOKE_PROJECT, "--strict"])
        weak_factory_payload = parse_json(weak_factory_proc)
        results.append(
            {
                "case": "strict_factory_rejects_weak_visual_plan_roles",
                "exit_code": weak_factory_proc.returncode,
                "passed": weak_factory_proc.returncode != 0
                and any("visual_plan rows lack purpose or decision_use" in str(error) for error in weak_factory_payload.get("errors", [])),
                "payload": weak_factory_payload,
            }
        )

        remove_project(project)
        write_common_quality_fixture(project)
        add_chapter_factory(project)
        with_factory_proc = run(["_ai_system/tools/report_quality_score.py", "--project", SMOKE_PROJECT])
        with_factory_payload = parse_json(with_factory_proc)
        with_factory_constraints = with_factory_payload.get("level_constraints")
        results.append(
            {
                "case": "chapter_factory_satisfies_level4_constraint",
                "exit_code": with_factory_proc.returncode,
                "passed": with_factory_proc.returncode == 0
                and isinstance(with_factory_constraints, dict)
                and with_factory_constraints.get("chapter_factory_ok") is True,
                "payload": with_factory_payload,
            }
        )
    finally:
        remove_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

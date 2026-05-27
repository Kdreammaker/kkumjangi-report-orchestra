from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_context_composer"


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


def write_fixture(project: Path) -> None:
    remove_project(project)
    write_text(project / "report_prd" / "smoke_prd.md", "# PRD\n\nSmoke report.\n")
    write_text(project / "drafts" / "smoke_toc.md", "# Detailed TOC\n")
    write_text(project / "reports" / "major_skeleton.md", "# Major Skeleton\n")
    write_text(
        project / "references" / "source_records" / "src_alpha.md",
        "# Source Record\n\n- source_id: src_alpha\n- exact_quote_location: p. 1\n",
    )
    write_text(
        project / "reports" / "report_claim_register.md",
        "| claim_id | source_ids | exact_quote_location | citation_type | status |\n|---|---|---|---|---|\n| claim_alpha | src_alpha | p. 1 | direct_quote | confirmed_fact |\n",
    )
    write_text(project / "source_index" / "source_master_index.md", "| source_id | status |\n|---|---|\n| src_alpha | report_citable |\n")
    write_text(
        project / "data_sources" / "visual_plan.csv",
        "visual_id,chapter,visual_type,title,purpose,decision_use,expected_reader_takeaway,required,data_file,source_data,source_record,status,notes\n"
        "vis_alpha,ch01,chart,Alpha chart,Show alpha scenario,Choose alpha option,Alpha is better,yes,data_sources/vis_alpha.csv,data_sources/vis_alpha.csv,references/source_records/src_alpha.md,planned,\n"
        "vis_beta,ch02,chart,Beta chart,Show beta scenario,Choose beta option,Beta is separate,yes,data_sources/vis_beta.csv,data_sources/vis_beta.csv,references/source_records/src_alpha.md,planned,\n",
    )
    write_text(project / "data_sources" / "vis_alpha.csv", "label,value\nA,1\n")
    write_text(project / "data_sources" / "vis_beta.csv", "label,value\nB,2\n")
    write_text(
        project / "reports" / "chapter_workpacks" / "ch01_workpack.md",
        """# ch01 Workpack

## 5. Evidence Inputs

| source_id | source title | exact location needed | use in chapter |
|---|---|---|---|
| src_alpha | Alpha source | p. 1 | support alpha |

## 6. Claim Register Links

| claim_id | claim_type | intended paragraph/section | status |
|---|---|---|---|
| claim_alpha | Fact | opening | confirmed_fact |

## 7. Assumptions and Estimates

| assumption_id | estimate/data need | sensitivity or caveat |
|---|---|---|
| asm_alpha | alpha estimate | fixture only |

## 9. Required Visuals

| visual_id | visual_type | purpose | data/source artifact | status |
|---|---|---|---|---|
| vis_alpha | chart | show alpha | data_sources/vis_alpha.csv | planned |
""",
    )


def paths(payload: dict[str, object]) -> set[str]:
    files = payload.get("context_files")
    if not isinstance(files, list):
        return set()
    result: set[str] = set()
    for item in files:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            result.add(item["path"])
    return result


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    project = PROJECT_ROOT / SMOKE_PROJECT
    results: list[dict[str, object]] = []
    try:
        write_fixture(project)
        chapter_proc = run(
            [
                "_ai_system/tools/compose_report_context.py",
                "--project",
                SMOKE_PROJECT,
                "--stage",
                "chapter",
                "--chapter",
                "ch01",
                "--write-packet",
            ]
        )
        chapter_payload = parse_json(chapter_proc)
        chapter_paths = paths(chapter_payload)
        packet = chapter_payload.get("context_packet", {})
        packet_md = packet.get("markdown", "") if isinstance(packet, dict) else ""
        packet_tsv = packet.get("files_tsv", "") if isinstance(packet, dict) else ""
        results.append(
            {
                "case": "chapter_context_follows_workpack_refs",
                "exit_code": chapter_proc.returncode,
                "passed": chapter_proc.returncode == 0
                and f"{PROJECT_ROOT.as_posix()}/{SMOKE_PROJECT}/references/source_records/src_alpha.md" in chapter_paths
                and f"{PROJECT_ROOT.as_posix()}/{SMOKE_PROJECT}/data_sources/vis_alpha.csv" in chapter_paths
                and f"{PROJECT_ROOT.as_posix()}/{SMOKE_PROJECT}/data_sources/vis_beta.csv" not in chapter_paths
                and not any(path.endswith("internal_review_report.html") for path in chapter_paths),
                "packet_written": bool(packet_md and packet_tsv and Path(packet_md).exists() and Path(packet_tsv).exists()),
                "payload": chapter_payload,
            }
        )
        results[-1]["passed"] = bool(results[-1]["passed"] and results[-1]["packet_written"])

        chart_proc = run(
            [
                "_ai_system/tools/compose_report_context.py",
                "--project",
                SMOKE_PROJECT,
                "--stage",
                "chart",
                "--chapter",
                "ch01",
            ]
        )
        chart_payload = parse_json(chart_proc)
        chart_paths = paths(chart_payload)
        results.append(
            {
                "case": "chart_context_prefers_chapter_visual_artifacts",
                "exit_code": chart_proc.returncode,
                "passed": chart_proc.returncode == 0
                and f"{PROJECT_ROOT.as_posix()}/{SMOKE_PROJECT}/data_sources/vis_alpha.csv" in chart_paths
                and f"{PROJECT_ROOT.as_posix()}/{SMOKE_PROJECT}/data_sources/vis_beta.csv" not in chart_paths,
                "payload": chart_payload,
            }
        )
    finally:
        remove_project(project)

    passed = all(bool(result["passed"]) for result in results)
    print(json.dumps({"passed": passed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

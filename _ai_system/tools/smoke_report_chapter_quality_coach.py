from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")
SMOKE_PROJECT = "zz_smoke_report_chapter_quality"


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


def parse_payload(proc: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout was not JSON:\n{proc.stdout}\n{proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise AssertionError("payload was not a JSON object")
    return payload


def write_project(project: Path) -> None:
    remove_project(project)
    (project / "reports" / "chapters").mkdir(parents=True, exist_ok=True)
    (project / "reports" / "chapter_workpacks").mkdir(parents=True, exist_ok=True)
    (project / "reports" / "chapters" / "ch01.html").write_text(
        "<section><h2>제1장 얇은 장</h2><p>좋은 이야기입니다. 완벽하고 100% 보장됩니다.</p></section>\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "reports" / "chapters" / "ch02.html").write_text(
        "<section><!-- CLAIM C-201 --><!-- VIS-201 --><h2>제2장 의사결정 분석</h2>"
        "<p>이 장은 독자의 의사결정과 실행 판단을 돕기 위해 대안 A와 대안 B를 비교한다. "
        "핵심 근거와 출처, 자료: 공식 원문, 근거 데이터: 장별 비교 데이터가 함께 제시된다.</p>"
        "<p>반론과 잔존 리스크도 분리한다. 제도 불확실성, 실행 한계, 비용 위험을 함께 제시해 "
        "선택의 조건을 좁힌다.</p>"
        "<p>첫째, 대안 A는 속도와 단순성이 장점이지만 운영 책임이 커진다. 둘째, 대안 B는 "
        "승인 가능성과 통제력이 높지만 비용과 이해관계자 조율 부담이 남는다. 셋째, 실행 단계에서는 "
        "법무 검토, 데이터 검증, 사용자 커뮤니케이션, 사후 모니터링을 분리해야 한다. 이 비교는 "
        "독자가 어느 조건에서 어느 대안을 선택할지 판단하도록 돕는다.</p>"
        "<p>또한 반론을 별도로 적는다. 시장 수요가 충분하지 않을 수 있고, 규제기관은 혁신성보다 "
        "사고 방지와 투자자 보호를 우선할 수 있다. 따라서 본 장은 권고를 단정하지 않고, 남은 "
        "리스크와 확인 질문을 함께 둔다. 출처와 근거 데이터는 본문 주장과 분리해 확인할 수 있어야 한다.</p>"
        "<p>이 장의 결론은 실행팀이 다음 회의에서 필요한 판단 항목을 줄이는 것이다. 비용, 일정, "
        "승인 가능성, 평판 위험, 기술 난도를 같은 표에서 비교하고, 각 항목의 근거가 불충분하면 "
        "추가 자료 수집을 먼저 하도록 안내한다. 의사결정은 단일 점수가 아니라 조건부 선택으로 남긴다.</p>"
        "<p>실무자는 이 장을 읽고 세 가지 행동을 결정한다. 첫째, 현재 근거만으로 진행 가능한 항목을 "
        "분리한다. 둘째, 규제나 데이터가 부족해 보류해야 할 항목을 표시한다. 셋째, 다음 검토 회의 전에 "
        "수집해야 할 원문과 수치 데이터를 지정한다. 이렇게 하면 보고서가 배경 설명에 그치지 않고 실제 "
        "실행 순서를 줄이는 도구가 된다.</p>"
        "<p>품질 판단도 같은 기준을 따른다. 장이 길어도 반론, 리스크, 출처, 근거 데이터가 없으면 "
        "강한 장이 아니다. 반대로 핵심 질문과 대안별 판단 조건이 선명하고, 주장마다 확인 가능한 근거가 "
        "있으며, 표나 그림의 근거 데이터가 분리되어 있으면 독자는 다음 결정을 더 안전하게 내릴 수 있다.</p>"
        "<p>마지막으로 잔존 리스크를 다시 적는다. 외부 환경 변화, 이해관계자 반대, 원문 해석 차이, "
        "데이터 품질 문제는 결론을 바꿀 수 있다. 따라서 본 장은 권고를 확정 문장으로 닫지 않고, "
        "조건부 판단과 추가 확인 항목으로 마무리한다. 이는 과장된 완결감을 줄이고 후속 작업의 품질을 높인다.</p>"
        "<p>후속 회의에서는 이 장의 판단 기준을 그대로 안건화할 수 있다. 먼저 법무 확인이 끝난 항목과 "
        "추가 원문이 필요한 항목을 나누고, 비용이 낮지만 규제 리스크가 큰 선택지는 즉시 실행이 아니라 "
        "실험 조건을 좁힌다. 반대로 비용이 높더라도 통제 가능성이 높은 선택지는 장기 과제로 분류한다.</p>"
        "<figure class=\"report-figure\"><svg><text>decision visual</text></svg><figcaption>자료: 공식 원문 / 근거 데이터: 장별 비교 데이터</figcaption><!-- data_file: data_sources/ch02.csv --></figure>"
        "</section>\n",
        encoding="utf-8",
        newline="\n",
    )
    (project / "reports" / "chapter_workpacks" / "ch02_workpack.md").write_text(
        "# ch02 Workpack\n\n"
        "## Reader Decision\n"
        "대안 A와 대안 B 중 어느 실행 경로를 선택할지 판단한다.\n\n"
        "## Reader Takeaway\n"
        "조건부 선택, 실행 순서, 잔존 리스크를 분리한다.\n\n"
        "## Core Question\n"
        "어떤 조건에서 어느 대안을 선택해야 하는가.\n\n"
        "## Required Answer Boundary\n"
        "비용, 일정, 승인 가능성, 평판 위험, 기술 난도, 추가 자료 수집을 함께 다룬다.\n\n"
        "## Claim Register Links\n"
        "C-201\n\n"
        "## Counterarguments\n"
        "시장 수요 부족, 규제기관의 사고 방지 우선순위, 원문 해석 차이를 다룬다.\n\n"
        "## Required Visuals\n"
        "VIS-201\n\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    project = PROJECT_ROOT / SMOKE_PROJECT
    try:
        write_project(project)
        proc = run(["_ai_system/tools/report_chapter_quality_coach.py", "--project", SMOKE_PROJECT, "--write-status"])
        payload = parse_payload(proc)
        chapters = payload.get("chapters", [])
        statuses = {row.get("chapter"): row.get("status") for row in chapters if isinstance(row, dict)}
        status_files = payload.get("status_files") if isinstance(payload.get("status_files"), dict) else {}
        passed = (
            proc.returncode == 0
            and statuses.get("reports/chapters/ch01.html") == "needs_attention"
            and statuses.get("reports/chapters/ch02.html") == "strong_signal"
            and (project / str(status_files.get("html", ""))).exists()
            and (project / str(status_files.get("json", ""))).exists()
        )
        print(
            json.dumps(
                {
                    "passed": passed,
                    "exit_code": proc.returncode,
                    "statuses": statuses,
                    "payload": payload,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if passed else 1
    finally:
        remove_project(project)


if __name__ == "__main__":
    raise SystemExit(main())

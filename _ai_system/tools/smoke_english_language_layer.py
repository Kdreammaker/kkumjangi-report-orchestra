from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path("00_사용자_작업공간")
FIXTURE_ROOT = Path("_ai_system") / "validation_fixtures" / "preset_samples"
SMOKE_PREFIX = "_smoke_english_language_layer_"
EXPECTED_ENGLISH_LABEL_ERROR = "English caption labels require html"
PRESET_STYLE_CASES = {
    "business_proposal": "partner_business",
    "press_release": "press_public",
    "investor_brief": "internal_executive_summary",
    "equity_research": "internal_executive_summary",
}


def safe_remove(path: Path) -> None:
    resolved_root = PROJECT_ROOT.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"refusing to remove path outside project root: {resolved_path}") from exc
    if not path.name.startswith(SMOKE_PREFIX):
        raise RuntimeError(f"refusing to remove non-smoke project path: {path}")
    if path.exists():
        shutil.rmtree(path)


def run_command(args: list[str], expect_success: bool = True) -> dict[str, Any]:
    proc = subprocess.run(
        args,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = {
        "command": " ".join(args),
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    if expect_success and proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")
    if not expect_success and proc.returncode == 0:
        raise RuntimeError(f"command unexpectedly passed: {' '.join(args)}\n{proc.stdout}")
    return result


def parse_json(result: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(str(result["stdout"]))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"command did not return JSON: {result['command']}") from exc
    return payload if isinstance(payload, dict) else {}


def asset_paths(items: list[Any]) -> list[str]:
    paths = []
    for item in items:
        if isinstance(item, dict):
            paths.append(str(item.get("path", "")))
    return paths


def assert_contains(paths: list[str], expected: str, label: str) -> None:
    if expected not in paths:
        raise RuntimeError(f"{label} missing expected asset: {expected}")


def assert_not_contains_language_guidance(paths: list[str], label: str) -> None:
    hits = [path for path in paths if path.endswith("language_guidance.md")]
    if hits:
        raise RuntimeError(f"{label} unexpectedly included language guidance: {' | '.join(hits)}")


def assert_guidance_assets(
    paths: list[str],
    preset_id: str,
    style_profile: str,
    should_include: bool,
    label: str,
) -> None:
    expected_preset = f"_ai_system/document_presets/{preset_id}/language_guidance.md"
    expected_style = f"_ai_system/style_profiles/{style_profile}/language_guidance.md"
    if should_include:
        assert_contains(paths, expected_preset, label)
        assert_contains(paths, expected_style, label)
    else:
        if expected_preset in paths:
            raise RuntimeError(f"{label} unexpectedly included preset language guidance: {expected_preset}")
        if expected_style in paths:
            raise RuntimeError(f"{label} unexpectedly included style language guidance: {expected_style}")


def copy_fixture_project(preset_id: str, project_name: str) -> Path:
    source = FIXTURE_ROOT / preset_id
    target = PROJECT_ROOT / project_name
    safe_remove(target)
    shutil.copytree(source, target)
    return target


def write_bad_language_variant(project: Path, source_report: str, target_report: str, mode: str) -> None:
    source = project / "reports" / source_report
    target = project / "reports" / target_report
    text = source.read_text(encoding="utf-8")
    text = re.sub(
        r"<meta\s+name=[\"']output_language[\"']\s+content=[\"']en[\"']>\s*",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\sdata-output-language=[\"']en[\"']", "", text, flags=re.I)
    if mode == "ko":
        text = re.sub(r"<html\s+lang=[\"']en[\"']>", '<html lang="ko">', text, count=1, flags=re.I)
    elif mode == "missing":
        text = re.sub(r"<html\s+lang=[\"']en[\"']>", "<html>", text, count=1, flags=re.I)
    else:
        raise ValueError(f"unknown bad language variant mode: {mode}")
    target.write_text(text, encoding="utf-8", newline="\n")


def validate_project_report(project_name: str, report: str, expect_success: bool = True) -> dict[str, Any]:
    result = run_command(
        [
            sys.executable,
            "_ai_system/tools/validate_report_artifact.py",
            "--project",
            project_name,
            "--report",
            report,
        ],
        expect_success=expect_success,
    )
    payload = parse_json(result)
    if expect_success and payload.get("errors"):
        raise RuntimeError(f"validator payload has errors for {project_name}/{report}: {payload.get('results')}")
    if not expect_success:
        text = result["stdout"] + result["stderr"]
        if EXPECTED_ENGLISH_LABEL_ERROR not in text:
            raise RuntimeError(f"expected English-label boundary error was not reported for {project_name}/{report}")
    return {
        "project": project_name,
        "report": report,
        "returncode": result["returncode"],
        "errors": payload.get("errors"),
        "warnings": payload.get("warnings"),
    }


def workflow_smoke() -> dict[str, Any]:
    created_projects: list[Path] = []
    context_results: list[dict[str, Any]] = []
    automation_checks: list[dict[str, Any]] = []
    language_cases = [
        ("en", True),
        ("mixed", True),
        ("ko", False),
        ("", False),
    ]

    try:
        for preset_id, style_profile in PRESET_STYLE_CASES.items():
            for output_language, should_include in language_cases:
                preset_args = [
                    sys.executable,
                    "_ai_system/tools/query_document_preset.py",
                    "--query",
                    preset_id,
                    "--stage",
                    "prd",
                ]
                style_args = [
                    sys.executable,
                    "_ai_system/tools/query_style_profile.py",
                    "--query",
                    style_profile,
                ]
                if output_language:
                    preset_args.extend(["--output-language", output_language])
                    style_args.extend(["--output-language", output_language])
                preset_payload = parse_json(run_command(preset_args))
                style_payload = parse_json(run_command(style_args))
                preset_asset_paths = asset_paths(preset_payload.get("stage_assets", []))
                expected_preset = f"_ai_system/document_presets/{preset_id}/language_guidance.md"
                if should_include:
                    assert_contains(
                        preset_asset_paths,
                        expected_preset,
                        f"document preset query {preset_id} {output_language}",
                    )
                elif expected_preset in preset_asset_paths:
                    raise RuntimeError(f"document preset query unexpectedly included language guidance for {preset_id} {output_language or 'unmarked'}")
                style_asset_paths = asset_paths(style_payload.get("style_assets", []))
                expected_style = f"_ai_system/style_profiles/{style_profile}/language_guidance.md"
                if should_include:
                    assert_contains(
                        style_asset_paths,
                        expected_style,
                        f"style profile query {style_profile} {output_language}",
                    )
                elif expected_style in style_asset_paths:
                    raise RuntimeError(f"style profile query unexpectedly included language guidance for {style_profile} {output_language or 'unmarked'}")

                preset_automation = preset_payload.get("automation", {})
                style_automation = style_payload.get("automation", {})
                if not isinstance(preset_automation, dict) or preset_automation.get("workflow_automation") not in {"not_enabled", "available_for_existing_base_flow"}:
                    raise RuntimeError(f"unexpected preset automation status for {preset_id}: {preset_automation}")
                if not isinstance(style_automation, dict) or style_automation.get("rewrite_automation") != "not_enabled":
                    raise RuntimeError(f"style profile enabled rewrite automation for {style_profile}")
                automation_checks.append(
                    {
                        "preset_id": preset_id,
                        "style_profile": style_profile,
                        "output_language": output_language or "unmarked",
                        "translation_automation": "not_enabled",
                        "rewrite_automation": style_automation.get("rewrite_automation"),
                        "jurisdiction_disclaimer_generation": "not_enabled",
                    }
                )

                project_name = f"{SMOKE_PREFIX}context_{preset_id}_{output_language or 'unmarked'}"
                project_path = PROJECT_ROOT / project_name
                safe_remove(project_path)
                (project_path / "reports").mkdir(parents=True, exist_ok=True)
                created_projects.append(project_path)

                context_args = [
                    sys.executable,
                    "_ai_system/tools/compose_report_context.py",
                    "--project",
                    project_name,
                    "--stage",
                    "design",
                    "--preset-query",
                    preset_id,
                    "--style-query",
                    style_profile,
                    "--write-packet",
                ]
                if output_language:
                    context_args.extend(["--output-language", output_language])
                context_payload = parse_json(run_command(context_args))
                context_paths = asset_paths(context_payload.get("context_files", []))
                assert_guidance_assets(
                    context_paths,
                    preset_id,
                    style_profile,
                    should_include,
                    f"context packet {preset_id} {output_language or 'unmarked'}",
                )
                packet_path = Path(context_payload["context_packet"]["markdown"])
                packet_text = packet_path.read_text(encoding="utf-8")
                preset_marker = f"{preset_id}/language_guidance.md"
                style_marker = f"{style_profile}/language_guidance.md"
                if should_include:
                    if preset_marker not in packet_text:
                        raise RuntimeError(f"context markdown omits preset guidance for {preset_id} {output_language}")
                    if style_marker not in packet_text:
                        raise RuntimeError(f"context markdown omits style guidance for {style_profile} {output_language}")
                else:
                    if preset_marker in packet_text:
                        raise RuntimeError(f"context markdown unexpectedly includes preset guidance for {preset_id} {output_language or 'unmarked'}")
                    if style_marker in packet_text:
                        raise RuntimeError(f"context markdown unexpectedly includes style guidance for {style_profile} {output_language or 'unmarked'}")
                context_results.append(
                    {
                        "preset_id": preset_id,
                        "style_profile": style_profile,
                        "output_language": output_language or "unmarked",
                        "language_guidance_included": should_include,
                    }
                )
    finally:
        for path in created_projects:
            safe_remove(path)

    return {
        "context_cases_checked": len(context_results),
        "en_mixed_language_guidance_only": True,
        "automation_checks": automation_checks,
        "context_results": context_results,
    }


def validator_smoke() -> dict[str, Any]:
    created: list[Path] = []
    results: list[dict[str, Any]] = []
    korean_reports = {
        "business_proposal": "reports/business_proposal_fixture.html",
        "press_release": "reports/press_release_fixture.html",
        "investor_brief": "reports/investor_brief_fixture.html",
        "equity_research": "reports/equity_research_fixture.html",
        "product_manual": "reports/product_manual_fixture.html",
    }
    english_reports = {
        "business_proposal": "reports/business_proposal_fixture_en.html",
        "press_release": "reports/press_release_fixture_en.html",
        "investor_brief": "reports/investor_brief_fixture_en.html",
        "equity_research": "reports/equity_research_fixture_en.html",
    }

    try:
        for preset_id, report in english_reports.items():
            project_name = f"{SMOKE_PREFIX}en_{preset_id}"
            project = copy_fixture_project(preset_id, project_name)
            created.append(project)
            results.append(validate_project_report(project_name, report, expect_success=True))

        boundary_block_count = 0
        for preset_id, report in english_reports.items():
            boundary_project_name = f"{SMOKE_PREFIX}boundary_{preset_id}"
            boundary_project = copy_fixture_project(preset_id, boundary_project_name)
            created.append(boundary_project)
            source_name = Path(report).name
            lang_ko_name = source_name.replace(".html", "_lang_ko.html")
            no_marker_name = source_name.replace(".html", "_no_marker.html")
            write_bad_language_variant(boundary_project, source_name, lang_ko_name, "ko")
            write_bad_language_variant(boundary_project, source_name, no_marker_name, "missing")
            results.append(
                validate_project_report(
                    boundary_project_name,
                    f"reports/{lang_ko_name}",
                    expect_success=False,
                )
            )
            results.append(
                validate_project_report(
                    boundary_project_name,
                    f"reports/{no_marker_name}",
                    expect_success=False,
                )
            )
            boundary_block_count += 2

        for preset_id, report in korean_reports.items():
            project_name = f"{SMOKE_PREFIX}ko_{preset_id}"
            project = copy_fixture_project(preset_id, project_name)
            created.append(project)
            results.append(validate_project_report(project_name, report, expect_success=True))
    finally:
        for path in created:
            safe_remove(path)

    return {
        "english_fixture_pass_count": len(english_reports),
        "english_label_boundary_block_count": boundary_block_count,
        "korean_fixture_pass_count": len(korean_reports),
        "results": results,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Smoke-test English language guidance as a layer over existing presets/profiles."
    )
    parser.parse_args()
    payload = {
        "status": "pass",
        "workflow_smoke": workflow_smoke(),
        "validator_smoke": validator_smoke(),
        "notes": [
            "No *_en preset is created.",
            "No automatic translation, automatic rewrite, or jurisdiction-specific disclaimer generation is enabled.",
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

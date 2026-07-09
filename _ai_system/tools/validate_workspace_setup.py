from __future__ import annotations

import argparse
import csv
import os
import hashlib
import html.parser
import importlib.util
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from workspace_config import load_config, resolved_domain_profile, validate_config_schema


ROOT_REQUIRED = {
    "README.md",
    "INSTALL.md",
    "START_HERE.html",
    "AGENTS.md",
    "VERSION.json",
    "CHANGELOG.md",
    "LICENSE",
    "docs",
    "00_사용자_작업공간",
    "_ai_system",
}
ROOT_REQUIRED_PATHS = {
    "docs/NOTICE",
    "docs/THIRD_PARTY_NOTICES.md",
    "docs/SECURITY.md",
    "docs/CONTRIBUTING.md",
}
ROOT_OPTIONAL = {".git", ".gitignore", ".github", ".agents", ".codex", ".local_state", "_internal"}
ROOT_ALLOWED = ROOT_REQUIRED | ROOT_OPTIONAL
PROJECT_ROOT = Path("00_사용자_작업공간")
RUNTIME_ROOT = Path("_ai_system") / "runtime"
PROJECT_REQUIRED = [
    "01_자료_넣는_곳",
    "프로젝트_대시보드_실행.vbs",
    "project_dashboard/open_project_dashboard.bat",
    "project_dashboard",
    "project_profile.json",
    "brand_assets",
    "tasks/current_task.md",
    "tasks/task_status.html",
    "context_packets",
    "worklogs",
    "references/reference_inventory.csv",
    "questions/question_log.md",
    "reports/report_claim_register.md",
    "reports/report_registry.csv",
    "source_index/source_master_index.md",
    "assumptions/assumption_register.md",
]
PROJECT_LIKE_ROOT_MARKERS = [
    "01_자료_넣는_곳",
    "프로젝트_대시보드_실행.vbs",
    "references/reference_inventory.csv",
    "reports/report_claim_register.md",
    "project_state/report_stage_manifest.json",
]
SMOKE_PROJECT_PREFIXES = ("zz_smoke_",)

EXCLUDED_SCAN_PARTS = {
    "_ai_system/backups",
    "_ai_system/project_state/latest_ai_snapshot",
    "_ai_system/runtime",
    ".local_state",
}
EXCLUDED_SCAN_MARKERS = {
    "/archive/",
}
PRIVATE_REPO_SLUG = "Kdreammaker/kkumjangi-report-orchestra"
PRIVATE_REPO_URL = "https://github.com/Kdreammaker/kkumjangi-report-orchestra"
PUBLIC_REPO_SLUG_RE = re.compile(r"Kdreammaker/kkumjangi-report-orchestra(?!-private)")
PUBLIC_REPO_URL_RE = re.compile(r"https://github\.com/Kdreammaker/kkumjangi-report-orchestra(?!-private)(?:\.git)?")
PUBLIC_INSTALL_DIR_RE = re.compile(r"\bcd\s+kkumjangi-report-orchestra(?!-private)\b")


def should_skip_scan_path(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return any(rel == part or rel.startswith(part + "/") for part in EXCLUDED_SCAN_PARTS) or any(
        marker in rel for marker in EXCLUDED_SCAN_MARKERS
    )


def is_smoke_project(path: Path) -> bool:
    return any(path.name.startswith(prefix) for prefix in SMOKE_PROJECT_PREFIXES)


class MinimalHTMLParser(html.parser.HTMLParser):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_html(path: Path) -> None:
    parser = MinimalHTMLParser()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    parser.close()


def remove_pycache(root: Path) -> int:
    removed = 0
    for path in root.rglob("__pycache__"):
        if should_skip_scan_path(path, root):
            continue
        if path.is_dir():
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink(missing_ok=True)
                elif child.is_dir():
                    child.rmdir()
            path.rmdir()
            removed += 1
    return removed


def runtime_package_status(import_name: str) -> dict[str, object]:
    return {"available": importlib.util.find_spec(import_name) is not None}


def check_local_runtime() -> dict[str, object]:
    packages = {
        "pypdf": runtime_package_status("pypdf"),
        "docling": runtime_package_status("docling"),
        "duckdb": runtime_package_status("duckdb"),
        "python_docx": runtime_package_status("docx"),
    }
    duckdb_smoke: dict[str, object] = {"ok": False, "error": "duckdb not installed"}
    if packages["duckdb"]["available"]:
        try:
            import duckdb  # type: ignore[import-not-found]

            duckdb_smoke = {"ok": duckdb.sql("select 1 + 1").fetchone()[0] == 2}
        except Exception as exc:  # noqa: BLE001
            duckdb_smoke = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    docling_smoke: dict[str, object] = {"ok": False, "error": "docling not installed"}
    if packages["docling"]["available"]:
        try:
            from docling.document_converter import DocumentConverter  # type: ignore[import-not-found]

            docling_smoke = {"ok": DocumentConverter is not None, "mode": "import_only"}
        except Exception as exc:  # noqa: BLE001
            docling_smoke = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    runtime_assets: dict[str, object] = {
        "assets": {
            "echarts": {"available": (RUNTIME_ROOT / "vendor" / "echarts" / "echarts.min.js").exists()},
            "pretendard_css": {"available": (RUNTIME_ROOT / "fonts" / "pretendard" / "pretendard.css").exists()},
        }
    }
    runtime_assets["ok"] = all(
        bool(asset.get("available"))
        for asset in runtime_assets["assets"].values()  # type: ignore[union-attr]
        if isinstance(asset, dict)
    )

    return {
        "python_version": sys.version.split()[0],
        "python_ok": sys.version_info >= (3, 11),
        "packages": packages,
        "duckdb_smoke": duckdb_smoke,
        "docling_smoke": docling_smoke,
        "runtime_assets": runtime_assets,
    }


def git_origin_url(root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def load_version_payload(root: Path) -> dict[str, object]:
    path = root / "VERSION.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"error": "invalid_VERSION_json"}
    return payload if isinstance(payload, dict) else {"error": "VERSION_json_must_be_object"}


def check_install_source(root: Path, expected_channel: str) -> dict[str, object]:
    version_payload = load_version_payload(root)
    channel = str(version_payload.get("channel", "")).strip()
    origin_url = git_origin_url(root)
    install_text = (root / "INSTALL.md").read_text(encoding="utf-8", errors="replace") if (root / "INSTALL.md").exists() else ""
    readme_text = (root / "README.md").read_text(encoding="utf-8", errors="replace") if (root / "README.md").exists() else ""
    errors: list[str] = []
    public_hits: list[str] = []

    if expected_channel and expected_channel != "any" and channel != expected_channel:
        errors.append(f"expected VERSION.json channel={expected_channel}, found {channel or 'missing'}")

    private_expected = expected_channel == "main" or channel == "main"
    if private_expected:
        if PRIVATE_REPO_SLUG not in install_text and PRIVATE_REPO_URL not in install_text:
            errors.append("private install source requires INSTALL.md to point to the private repository")
        if origin_url and PRIVATE_REPO_SLUG not in origin_url and PRIVATE_REPO_URL not in origin_url:
            errors.append(f"private install source requires origin to be private, found {origin_url}")
        for label, text in [("INSTALL.md", install_text), ("README.md", readme_text)]:
            if PUBLIC_REPO_URL_RE.search(text):
                public_hits.append(f"{label}: public GitHub URL")
            if PUBLIC_REPO_SLUG_RE.search(text):
                public_hits.append(f"{label}: public repository slug")
            if label == "INSTALL.md" and PUBLIC_INSTALL_DIR_RE.search(text):
                public_hits.append(f"{label}: public install directory")
        if public_hits:
            errors.append("private install source docs point to public repository: " + " | ".join(public_hits[:8]))

    return {
        "expected_channel": expected_channel or "not_specified",
        "version": version_payload.get("version", ""),
        "release_date": version_payload.get("release_date", ""),
        "channel": channel,
        "origin_url": origin_url,
        "private_expected": private_expected,
        "public_repo_hits": public_hits,
        "errors": errors,
    }


def check_snapshot_manifests(root: Path) -> dict[str, int]:
    checked = 0
    bad = 0
    missing = 0
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
                    missing += 1
                    bad += 1
                    continue
                active_hash = sha256(active)
                snapshot_hash = sha256(snapshot)
                expected_snapshot_hash = row.get("snapshot_sha256") or row.get("sha256")
                if (
                    active_hash.lower() != (row.get("sha256") or "").lower()
                    or snapshot_hash.lower() != (expected_snapshot_hash or "").lower()
                    or active_hash.lower() != snapshot_hash.lower()
                ):
                    bad += 1
    return {"checked": checked, "bad": bad, "missing": missing}


def detect_absolute_paths(root: Path) -> list[str]:
    pattern = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
    hits: list[str] = []
    include_ext = {".md", ".txt", ".html", ".csv", ".py", ".bat", ".vbs"}
    for path in [root / "AGENTS.md", root / "START_HERE.html", root / "_ai_system", root / "00_사용자_작업공간"]:
        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = [p for p in path.rglob("*") if p.is_file()]
        else:
            continue
        for file in files:
            rel = file.relative_to(root).as_posix()
            if should_skip_scan_path(file, root):
                continue
            if file.suffix.lower() not in include_ext:
                continue
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except FileNotFoundError:
                # Smoke tests may create and remove temporary projects while this
                # scan is running. A vanished file is not an absolute-path hit.
                continue
            for line_no, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append(f"{rel}:{line_no}")
    return hits


def detect_root_project_like_items(root: Path) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for item in sorted(root.iterdir(), key=lambda path: path.name.lower()):
        if not item.is_dir() or item.name in ROOT_ALLOWED:
            continue
        markers = [marker for marker in PROJECT_LIKE_ROOT_MARKERS if (item / marker).exists()]
        if markers:
            hits.append(
                {
                    "name": item.name,
                    "markers": markers,
                    "expected_parent": PROJECT_ROOT.as_posix(),
                }
            )
    return hits


def check_reference_api(root: Path, project_dir: Path, port: int) -> dict[str, object]:
    app = root / "_ai_system" / "tools" / "project_dashboard_app" / "app.py"
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.Popen(
        [sys.executable, str(app), "--project", str(project_dir), "--port", str(port), "--no-browser"],
        cwd=root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        url = f"http://127.0.0.1:{port}/api/references"
        last_error = ""
        for _ in range(40):
            try:
                with urllib.request.urlopen(url, timeout=1.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return {"ok": True, "count": int(data.get("count", 0))}
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                time.sleep(0.1)
        return {"ok": False, "count": None, "error": last_error}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def check_project_profile(project_dir: Path) -> dict[str, object]:
    path = project_dir / "project_profile.json"
    result: dict[str, object] = {"ok": False, "errors": []}
    if not path.exists():
        result["errors"].append("missing_project_profile_json")
        return result
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        result["errors"].append(f"invalid_json: {exc}")
        return result
    if not isinstance(payload, dict):
        result["errors"].append("project_profile_must_be_object")
        return result
    for key in ["document_classification", "classification", "confidentiality", "confidentiality_status", "is_confidential"]:
        if key in payload:
            result["errors"].append(f"forbidden_report_default_field: {key}")
    responsible = payload.get("responsible_people", [])
    practitioners = payload.get("practitioners", [])
    external = payload.get("external_contacts", [])
    if not isinstance(responsible, list) or len(responsible) < 1:
        result["errors"].append("responsible_people_requires_at_least_one_row")
    if not isinstance(practitioners, list) or len(practitioners) < 1:
        result["errors"].append("practitioners_requires_at_least_one_row")
    if not isinstance(external, list):
        result["errors"].append("external_contacts_must_be_list")
    brand_assets = payload.get("brand_assets", {})
    if not isinstance(brand_assets, dict):
        result["errors"].append("brand_assets_must_be_object")
    result["ok"] = not result["errors"]
    return result


def check_dashboard_batch_path(root: Path, project_dir: Path) -> dict[str, object]:
    path = project_dir / "project_dashboard" / "open_project_dashboard.bat"
    result: dict[str, object] = {
        "ok": False,
        "exists": path.exists(),
        "uses_current_workspace_path": False,
        "uses_legacy_four_up_path": False,
        "resolved_app_exists": False,
        "errors": [],
    }
    if not path.exists():
        result["errors"].append("missing_open_project_dashboard_bat")
        return result
    text = path.read_text(encoding="utf-8", errors="ignore")
    current = r"..\..\..\_ai_system\tools\project_dashboard_app\app.py"
    legacy = r"..\..\..\..\_ai_system\tools\project_dashboard_app\app.py"
    result["uses_current_workspace_path"] = current in text
    result["uses_legacy_four_up_path"] = legacy in text
    resolved = (path.parent / ".." / ".." / ".." / "_ai_system" / "tools" / "project_dashboard_app" / "app.py").resolve()
    result["resolved_app_path"] = resolved.as_posix()
    result["resolved_app_exists"] = resolved.exists()
    if not result["uses_current_workspace_path"]:
        result["errors"].append("dashboard_batch_does_not_use_current_workspace_relative_path")
    if result["uses_legacy_four_up_path"]:
        result["errors"].append("dashboard_batch_uses_legacy_four_up_path")
    if not result["resolved_app_exists"]:
        result["errors"].append("dashboard_batch_resolved_app_missing")
    result["ok"] = not result["errors"]
    return result


def python_process_ids() -> set[int]:
    pids: set[int] = set()
    try:
        output = subprocess.check_output(
            ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        output = b""
    for line in output.decode("utf-8", errors="ignore").splitlines():
        match = re.search(r"(\d+)\s*$", line.strip())
        if match:
            pids.add(int(match.group(1)))
    try:
        output = subprocess.check_output(
            ["wmic", "process", "where", "name='pythonw.exe'", "get", "ProcessId,CommandLine"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        output = b""
    for line in output.decode("utf-8", errors="ignore").splitlines():
        match = re.search(r"(\d+)\s*$", line.strip())
        if match:
            pids.add(int(match.group(1)))
    return pids


def stop_process_ids(pids: set[int]) -> None:
    for pid in pids:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )


def check_reference_user_flow(root: Path, project_dir: Path, base_port: int) -> dict[str, object]:
    project_name = project_dir.name
    vbs = project_dir / "프로젝트_대시보드_실행.vbs"
    result: dict[str, object] = {
        "launcher_ok": False,
        "api_ok": False,
        "ui_html_ok": False,
        "port": None,
        "count": None,
    }
    if not vbs.exists():
        result["error"] = "missing_project_dashboard_vbs_launcher"
        return result
    if os.name != "nt":
        result["error"] = "vbs_launcher_requires_windows"
        return result

    before_pids = python_process_ids()
    try:
        env = os.environ.copy()
        env["PROJECT_DASHBOARD_NO_BROWSER"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        launcher = subprocess.run(
            ["cscript.exe", "//nologo", str(vbs)],
            cwd=root,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
        result["launcher_returncode"] = launcher.returncode
        result["launcher_ok"] = launcher.returncode == 0
        result["browser_suppressed"] = True
        deadline = time.monotonic() + 12.0
        probes = 0
        while time.monotonic() < deadline:
            for port in range(8895, 8916):
                if time.monotonic() >= deadline:
                    break
                probes += 1
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/references", timeout=0.1) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    if int(data.get("count", -1)) >= 0:
                        result["api_ok"] = True
                        result["port"] = port
                        result["count"] = int(data.get("count", 0))
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/references", timeout=0.5) as resp:
                            html = resp.read().decode("utf-8", errors="ignore")
                        result["ui_html_ok"] = (
                            "문서 대장" in html
                            and "referenceTable" in html
                            and ("list-card" in html or "<table" in html)
                        )
                        result["probe_count"] = probes
                        return result
                except Exception:
                    pass
            time.sleep(0.1)
        result["error"] = "launched_but_api_not_found"
        result["probe_count"] = probes
        result["probe_timeout_seconds"] = 12
        return result
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result
    finally:
        stop_process_ids(python_process_ids() - before_pids)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate report-factory workspace setup.")
    parser.add_argument("--skip-api", action="store_true", help="Skip local reference-library API checks.")
    parser.add_argument(
        "--include-user-flow",
        action="store_true",
        help="Also run VBS/BAT launcher checks and verify the served reference-library UI HTML.",
    )
    parser.add_argument(
        "--expect-channel",
        choices=["main", "public", "any"],
        default="any",
        help="Require VERSION.json channel to match. Private install tests should use --expect-channel main.",
    )
    args = parser.parse_args()

    root = Path.cwd().resolve()
    results: dict[str, object] = {}

    root_items = {p.name for p in root.iterdir()}
    results["root_extra_items"] = sorted(root_items - ROOT_ALLOWED)
    results["root_missing_items"] = sorted(ROOT_REQUIRED - root_items)
    results["root_missing_paths"] = sorted(path for path in ROOT_REQUIRED_PATHS if not (root / path).exists())
    results["root_project_like_items"] = detect_root_project_like_items(root)
    results["install_source"] = check_install_source(root, args.expect_channel)

    projects_root = root / PROJECT_ROOT
    project_dirs = sorted([p for p in projects_root.iterdir() if p.is_dir() and not is_smoke_project(p)]) if projects_root.exists() else []
    project_checks = []
    project_profiles = {}
    project_dashboard_batches = {}
    for project in project_dirs:
        missing = [rel for rel in PROJECT_REQUIRED if not (project / rel).exists()]
        project_checks.append({"project": project.name, "missing": missing})
        project_profiles[project.name] = check_project_profile(project)
        project_dashboard_batches[project.name] = check_dashboard_batch_path(root, project)
    results["projects_checked"] = len(project_dirs)
    results["project_required_missing"] = project_checks
    results["project_profiles"] = project_profiles
    results["project_dashboard_batch_paths"] = project_dashboard_batches

    user_facing_html = [
        root / "START_HERE.html",
    ]
    user_facing_html.extend(project / "tasks" / "task_status.html" for project in project_dirs)
    report_html = sorted(
        path for path in (root / PROJECT_ROOT).glob("*/reports/*.html")
        if not is_smoke_project(path.parents[1])
    )
    evidence_html = sorted(
        path for path in (root / PROJECT_ROOT).glob("*/evidence/**/*.html")
        if not is_smoke_project(path.parents[2])
    )
    html_errors = []
    for path in [*user_facing_html, *report_html, *evidence_html]:
        if path.exists():
            try:
                parse_html(path)
            except Exception as exc:  # noqa: BLE001
                html_errors.append({"path": path.relative_to(root).as_posix(), "error": str(exc)})
    results["html_checked"] = {
        "user_facing": sum(1 for p in user_facing_html if p.exists()),
        "reports": len(report_html),
        "evidence_captures": len(evidence_html),
        "errors": html_errors,
    }

    results["python_version"] = sys.version.split()[0]
    results["local_runtime"] = check_local_runtime()
    results["pypdf_available"] = bool(results["local_runtime"]["packages"]["pypdf"]["available"])
    results["docling_available"] = bool(results["local_runtime"]["packages"]["docling"]["available"])
    results["duckdb_available"] = bool(results["local_runtime"]["packages"]["duckdb"]["available"])
    results["python_docx_available"] = bool(results["local_runtime"]["packages"]["python_docx"]["available"])
    results["echarts_available"] = bool(results["local_runtime"].get("runtime_assets", {}).get("assets", {}).get("echarts", {}).get("available"))
    results["pretendard_available"] = bool(results["local_runtime"].get("runtime_assets", {}).get("assets", {}).get("pretendard_css", {}).get("available"))
    config = load_config(root)
    results["workspace_config"] = {
        "active_domain": resolved_domain_profile(config).get("preset_domain"),
        "errors": validate_config_schema(config),
    }

    if args.skip_api:
        results["reference_api"] = "skipped"
    else:
        api = {}
        base_port = 8890
        for idx, project in enumerate(project_dirs):
            api[project.name] = check_reference_api(root, project, base_port + idx)
        results["reference_api"] = api

    if args.include_user_flow:
        user_flow = {}
        for idx, project in enumerate(project_dirs):
            user_flow[project.name] = check_reference_user_flow(root, project, 8890 + idx)
        results["reference_user_flow"] = user_flow
    else:
        results["reference_user_flow"] = "skipped_use_--include-user-flow_for_vbs_and_ui_check"

    results["snapshot_manifests"] = check_snapshot_manifests(root)
    results["absolute_path_hits"] = detect_absolute_paths(root)
    results["root_runtime_leftovers"] = [name for name in [".playwright-mcp"] if (root / name).exists()]
    results["pycache_removed_during_check"] = remove_pycache(root)
    results["pycache_count"] = len([p for p in root.rglob("__pycache__") if not should_skip_scan_path(p, root)])

    has_failure = bool(
        results["root_extra_items"]
        or results["root_missing_items"]
        or results["root_missing_paths"]
        or results["root_project_like_items"]
        or results["install_source"]["errors"]
        or results["absolute_path_hits"]
        or results["root_runtime_leftovers"]
        or results["pycache_count"]
    )
    has_failure = has_failure or any(item["missing"] for item in project_checks)
    has_failure = has_failure or any(not item.get("ok") for item in project_profiles.values())
    has_failure = has_failure or any(not item.get("ok") for item in project_dashboard_batches.values())
    has_failure = has_failure or bool(results["html_checked"]["errors"])
    has_failure = has_failure or not results["pypdf_available"]
    has_failure = has_failure or not results["docling_available"]
    has_failure = has_failure or not results["duckdb_available"]
    has_failure = has_failure or not results["python_docx_available"]
    has_failure = has_failure or not results["echarts_available"]
    has_failure = has_failure or not results["pretendard_available"]
    has_failure = has_failure or not bool(results["local_runtime"]["python_ok"])
    has_failure = has_failure or not bool(results["local_runtime"]["duckdb_smoke"]["ok"])
    has_failure = has_failure or not bool(results["local_runtime"]["docling_smoke"]["ok"])
    has_failure = has_failure or bool(results["workspace_config"]["errors"])
    if isinstance(results["reference_api"], dict):
        has_failure = has_failure or any(not item.get("ok") for item in results["reference_api"].values())
    if isinstance(results["reference_user_flow"], dict):
        has_failure = has_failure or any(
            not (item.get("launcher_ok") and item.get("api_ok") and item.get("ui_html_ok"))
            for item in results["reference_user_flow"].values()
        )
    has_failure = has_failure or bool(results["snapshot_manifests"]["bad"])

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if has_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())

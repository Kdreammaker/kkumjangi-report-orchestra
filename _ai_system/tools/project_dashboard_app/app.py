from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import platform
import re
import socket
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


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

INVENTORY_FIELDS = [
    "reference_id",
    "listed_at_kst",
    "title",
    "file_type",
    "material_origin",
    "material_origin_ko",
    "visibility",
    "visibility_ko",
    "source_tier",
    "ai_tags",
    "tag_version",
    "tagged_at_kst",
    "tag_notes",
    "original_path",
    "open_path",
    "sha256",
    "file_size_bytes",
    "last_modified_kst",
    "intake_status",
    "parse_status",
    "ocr_status",
    "page_count",
    "derived_text_path",
    "normalized_status",
    "normalized_manifest_path",
    "normalized_text_path",
    "normalized_unit_index_path",
    "context_index_status",
    "context_unit_count",
    "source_id",
    "source_record_path",
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

ALLOWED_FOLDER_KEYS = {
    "materials": ("01_자료_넣는_곳", "자료 폴더"),
    "brand_assets": ("brand_assets", "로고 폴더"),
    "reports": ("reports", "보고서 폴더"),
    "share": ("04_공유_패키지", "공유 패키지 폴더"),
}
ALLOWED_REPORT_FILE_PREFIXES = ("reports/", "04_공유_패키지/")
ALLOWED_REPORT_FILE_SUFFIXES = {".html", ".htm", ".pdf", ".docx", ".xlsx", ".csv"}

ICON_SPRITE = """
<svg aria-hidden="true" class="svg-sprite" height="0" width="0" style="position:absolute">
  <symbol id="icon-dashboard" viewBox="0 0 24 24"><path d="M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z"/></symbol>
  <symbol id="icon-user" viewBox="0 0 24 24"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-8 8a8 8 0 0 1 16 0H4Z"/></symbol>
  <symbol id="icon-report" viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6V3Zm8 1.8V7h2.2L14 4.8ZM8 10h8v2H8v-2Zm0 4h8v2H8v-2Z"/></symbol>
  <symbol id="icon-folder" viewBox="0 0 24 24"><path d="M3 6h7l2 2h9v10a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V6Z"/></symbol>
  <symbol id="icon-copy" viewBox="0 0 24 24"><path d="M8 7h11v14H8V7Zm-3 10H3V3h11v2H5v12Z"/></symbol>
  <symbol id="icon-save" viewBox="0 0 24 24"><path d="M5 3h12l2 2v16H5V3Zm3 2v5h8V5H8Zm0 10v4h8v-4H8Z"/></symbol>
  <symbol id="icon-plus" viewBox="0 0 24 24"><path d="M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6V5Z"/></symbol>
  <symbol id="icon-trash" viewBox="0 0 24 24"><path d="M8 4h8l1 2h4v2H3V6h4l1-2Zm1 6h2v8H9v-8Zm4 0h2v8h-2v-8Z"/></symbol>
  <symbol id="icon-refresh" viewBox="0 0 24 24"><path d="M12 5a7 7 0 0 1 6.3 4H16l3.5 4L23 9h-2.6A9 9 0 1 0 21 15h-2.1A7 7 0 1 1 12 5Z"/></symbol>
  <symbol id="icon-search" viewBox="0 0 24 24"><path d="M10 4a6 6 0 1 1 0 12 6 6 0 0 1 0-12Zm0 2a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm5.5 9 4.5 4.5-1.5 1.5-4.5-4.5 1.5-1.5Z"/></symbol>
  <symbol id="icon-stop" viewBox="0 0 24 24"><path d="M7 7h10v10H7V7Z"/></symbol>
  <symbol id="icon-list" viewBox="0 0 24 24"><path d="M8 6h13v2H8V6Zm0 5h13v2H8v-2Zm0 5h13v2H8v-2ZM3 6h2v2H3V6Zm0 5h2v2H3v-2Zm0 5h2v2H3v-2Z"/></symbol>
</svg>
"""


def icon(name: str) -> str:
    return f'<svg class="icon" aria-hidden="true"><use href="#icon-{html.escape(name)}"></use></svg>'


def now_kst() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M KST")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_csv(path: Path, fieldnames: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows: list[dict[str, str]] = []
        for row in csv.DictReader(f):
            rows.append({field: str(row.get(field, "") or "") for field in fieldnames})
        return rows


def read_csv_with_fields(path: Path, default_fields: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return list(default_fields), []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or default_fields)
        for field in default_fields:
            if field not in fields:
                fields.append(field)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({field: str(row.get(field, "") or "") for field in fields})
        return fields, rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: str(row.get(field, "") or "") for field in fieldnames})


def row_map(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows if row.get(key, "")}


def changed_fields(before: dict[str, str], after: dict[str, str], fields: list[str]) -> list[str]:
    return [field for field in fields if str(before.get(field, "") or "") != str(after.get(field, "") or "")]


def count_changed(before: object, after: object) -> bool:
    return before != after


def redactable_fields(fields: list[str]) -> list[str]:
    sensitive_tokens = ("phone", "email", "contact", "note", "notes", "비고", "연락처", "이메일")
    return [field for field in fields if not any(token.lower() in field.lower() for token in sensitive_tokens)]


def contact_template(name: str = "") -> dict[str, str]:
    return {
        "company": "",
        "department": "",
        "name": name,
        "title": "",
        "organization": "",
        "phone": "",
        "email": "",
        "notes": "",
    }


def default_project_profile(project_dir: Path) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "project_name": project_dir.name,
        "organization_name": "미지정",
        "responsible_people": [contact_template("미지정")],
        "approval_line": [],
        "practitioners": [contact_template("미지정")],
        "external_contacts": [],
        "brand_assets": {
            "project_logo_path": "",
            "common_logo_path": "",
            "usage_priority": [
                "report_specific_cover_or_prd",
                "project_brand_assets",
                "common_ci",
                "blank",
            ],
            "project_logo_filename": "project_logo.png",
            "notes": "산출물별 지정 로고가 없으면 brand_assets/project_logo.png만 프로젝트 로고로 자동 사용합니다.",
        },
        "notes": "문서 분류와 대외비 여부는 보고서 PRD에서 매번 확인합니다.",
    }


def person_display(row: object) -> str:
    if not isinstance(row, dict):
        return ""
    name = str(row.get("name", "")).strip()
    if not name or name == "미지정":
        return ""
    title = str(row.get("title", "")).strip()
    organization = str(row.get("organization", "")).strip()
    parts = [name]
    if title:
        parts.append(title)
    if organization:
        parts.append(organization)
    return " / ".join(parts)


def split_task_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_task_rows(text: str) -> list[dict[str, str]]:
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
    in_table = False
    for line in text.splitlines():
        if not line.startswith("|"):
            if in_table and rows:
                break
            continue
        cells = split_task_row(line)
        if "stage_id" in cells and "status" in cells:
            header = cells
            in_table = True
            continue
        if in_table and re.fullmatch(r"[\s|:-]+", line):
            continue
        if in_table and header:
            if len(cells) < len(header):
                cells.extend([""] * (len(header) - len(cells)))
            rows.append(dict(zip(header, cells, strict=False)))
    return rows


class DashboardStore:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.workspace_dir = self._find_workspace_root(self.project_dir)
        self.profile_path = self.project_dir / "project_profile.json"
        self.registry_path = self.project_dir / "reports" / "report_registry.csv"
        self.inventory_path = self.project_dir / "references" / "reference_inventory.csv"
        self.change_jsonl_path = self.project_dir / "project_state" / "dashboard_change_log.jsonl"
        self.change_csv_path = self.project_dir / "worklogs" / "dashboard_change_log.csv"
        self.device_path = self.workspace_dir / ".local_state" / "device_identity.json"
        self.reference_job_lock = threading.Lock()
        self.reference_job: dict[str, object] = {
            "running": False,
            "status": "idle",
            "message": "대기 중",
            "started_at_kst": "",
            "finished_at_kst": "",
            "log_path": "",
            "returncode": "",
        }

    @staticmethod
    def _find_workspace_root(project_dir: Path) -> Path:
        for parent in [project_dir.resolve(), *project_dir.resolve().parents]:
            if (parent / "AGENTS.md").exists():
                return parent
        raise RuntimeError("Cannot find workspace root with AGENTS.md")

    def _safe_project_path(self, rel_path: str) -> Path:
        target = (self.project_dir / rel_path).resolve()
        try:
            target.relative_to(self.project_dir)
        except ValueError as exc:
            raise ValueError("path outside project") from exc
        return target

    def _allowed_folder(self, key: str) -> tuple[Path, str]:
        if key not in ALLOWED_FOLDER_KEYS:
            raise ValueError("허용되지 않은 폴더입니다.")
        rel_path, label = ALLOWED_FOLDER_KEYS[key]
        target = self._safe_project_path(rel_path)
        if not target.exists() or not target.is_dir():
            raise ValueError(f"{label}가 아직 없습니다.")
        return target, label

    def _app_version(self) -> str:
        version_path = self.workspace_dir / "VERSION.json"
        if not version_path.exists():
            return "unknown"
        try:
            data = json.loads(version_path.read_text(encoding="utf-8"))
            return str(data.get("version", "unknown") or "unknown")
        except json.JSONDecodeError:
            return "unknown"

    def _device_identity(self) -> dict[str, str]:
        self.device_path.parent.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            subprocess.run(["attrib", "+H", str(self.device_path.parent)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if self.device_path.exists():
            try:
                data = json.loads(self.device_path.read_text(encoding="utf-8"))
                device_id = str(data.get("anonymous_device_id", "") or "")
                if device_id:
                    return data
            except json.JSONDecodeError:
                pass
        data = {
            "schema_version": "1.0",
            "anonymous_device_id": str(uuid.uuid4()),
            "created_at_kst": now_kst(),
            "note": "Local random device identifier. Do not sync or share this folder.",
        }
        self.device_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return data

    def _device_hash(self) -> str:
        device = self._device_identity()
        raw_id = str(device.get("anonymous_device_id", "") or "")
        return sha256_text(raw_id)[:12] if raw_id else "UNKNOWN"

    def _append_change_log(self, scope: str, target_file: str, summary: str, before_hash: str, after_hash: str) -> dict[str, str]:
        event = {
            "changed_at_kst": now_kst(),
            "scope": scope,
            "target_file": target_file,
            "summary": summary,
            "pc_name": platform.node() or "unknown",
            "anonymous_device_id": self._device_hash(),
            "before_hash": before_hash[:12],
            "after_hash": after_hash[:12],
            "app_version": self._app_version(),
        }
        self.change_jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.change_jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        existing = read_csv(self.change_csv_path, CHANGE_LOG_FIELDS)
        existing.append(event)
        write_csv(self.change_csv_path, existing, CHANGE_LOG_FIELDS)
        return event

    def changes(self, scope: str | None = None, limit: int = 200) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        if self.change_jsonl_path.exists():
            for line in self.change_jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    row = {field: str(item.get(field, "") or "") for field in CHANGE_LOG_FIELDS}
                    rows.append(row)
        if scope:
            rows = [row for row in rows if row.get("scope") == scope]
        return list(reversed(rows))[:limit]

    def profile(self) -> dict[str, object]:
        if not self.profile_path.exists():
            return default_project_profile(self.project_dir)
        try:
            data = json.loads(self.profile_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return default_project_profile(self.project_dir)

    def project_owner(self) -> str:
        profile = self.profile()
        responsible = profile.get("responsible_people", [])
        if isinstance(responsible, list) and responsible:
            owner = person_display(responsible[0])
            if owner:
                return owner
        return "프로젝트 책임자 미입력: 프로젝트 정보에서 첫 번째 책임자를 입력해 주세요."

    def save_profile(self, data: dict[str, object]) -> dict[str, str]:
        if not isinstance(data, dict):
            raise ValueError("profile must be an object")
        before_profile = self.profile()
        before_hash = file_sha256(self.profile_path)
        responsible = data.get("responsible_people", [])
        practitioners = data.get("practitioners", [])
        if not isinstance(responsible, list) or not responsible:
            raise ValueError("책임자는 1명 이상 필요합니다.")
        if not isinstance(practitioners, list) or not practitioners:
            raise ValueError("담당 실무자는 1명 이상 필요합니다.")
        data.setdefault("schema_version", "1.0")
        data.setdefault("brand_assets", {})
        if isinstance(data["brand_assets"], dict):
            data["brand_assets"]["project_logo_filename"] = "project_logo.png"
        self.profile_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        after_hash = file_sha256(self.profile_path)
        summary = self._profile_change_summary(before_profile, data)
        event = self._append_change_log("project_profile", "project_profile.json", summary, before_hash, after_hash)
        return {"saved_at_kst": now_kst(), "path": "project_profile.json", "change_summary": summary, "change_id": event["changed_at_kst"]}

    @staticmethod
    def _profile_count(data: object, key: str) -> int:
        if isinstance(data, dict) and isinstance(data.get(key), list):
            return len(data[key])
        return 0

    def _profile_change_summary(self, before: dict[str, object], after: dict[str, object]) -> str:
        parts: list[str] = []
        for key, label in [("project_name", "프로젝트명"), ("organization_name", "조직명")]:
            if before.get(key) != after.get(key):
                parts.append(f"{label} 변경")
        for key, label in [
            ("responsible_people", "책임자"),
            ("approval_line", "결재라인"),
            ("practitioners", "담당 실무자"),
            ("external_contacts", "외부 담당자"),
        ]:
            before_count = self._profile_count(before, key)
            after_count = self._profile_count(after, key)
            if before_count != after_count:
                parts.append(f"{label} {before_count}->{after_count}")
            elif count_changed(before.get(key), after.get(key)):
                parts.append(f"{label} 필드 변경")
        if before.get("brand_assets") != after.get("brand_assets"):
            parts.append("로고 설정 변경")
        return "; ".join(parts) if parts else "프로젝트 정보 저장"

    def report_registry(self) -> list[dict[str, str]]:
        return read_csv(self.registry_path, REPORT_REGISTRY_FIELDS)

    def save_report_registry(self, rows: object) -> dict[str, str]:
        if not isinstance(rows, list):
            raise ValueError("rows must be a list")
        before_rows = self.report_registry()
        before_hash = file_sha256(self.registry_path)
        cleaned: list[dict[str, str]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            cleaned.append({field: str(row.get(field, "") or "").strip() for field in REPORT_REGISTRY_FIELDS})
        write_csv(self.registry_path, cleaned, REPORT_REGISTRY_FIELDS)
        after_hash = file_sha256(self.registry_path)
        summary = self._registry_change_summary(before_rows, cleaned)
        event = self._append_change_log("report_registry", "reports/report_registry.csv", summary, before_hash, after_hash)
        return {"saved_at_kst": now_kst(), "path": "reports/report_registry.csv", "count": str(len(cleaned)), "change_summary": summary, "change_id": event["changed_at_kst"]}

    def _registry_change_summary(self, before_rows: list[dict[str, str]], after_rows: list[dict[str, str]]) -> str:
        before = row_map(before_rows, "report_id")
        after = row_map(after_rows, "report_id")
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed: list[str] = []
        fields = redactable_fields(REPORT_REGISTRY_FIELDS)
        for report_id in sorted(set(before) & set(after)):
            fields_changed = changed_fields(before[report_id], after[report_id], fields)
            if fields_changed:
                changed.append(f"{report_id}({', '.join(fields_changed)})")
        parts: list[str] = []
        if len(before_rows) != len(after_rows):
            parts.append(f"보고서 행 {len(before_rows)}->{len(after_rows)}")
        if added:
            parts.append("추가 " + ", ".join(added[:5]))
        if removed:
            parts.append("삭제 " + ", ".join(removed[:5]))
        if changed:
            parts.append("변경 " + "; ".join(changed[:5]))
        return "; ".join(parts) if parts else "산출물 관리 저장"

    def reference_inventory(self) -> dict[str, object]:
        fields, rows = read_csv_with_fields(self.inventory_path, INVENTORY_FIELDS)
        return {"rows": rows, "fields": fields, "count": len(rows)}

    def save_reference_inventory(self, rows: object) -> dict[str, str]:
        if not isinstance(rows, list):
            raise ValueError("rows must be a list")
        fields, before_rows = read_csv_with_fields(self.inventory_path, INVENTORY_FIELDS)
        before_hash = file_sha256(self.inventory_path)
        for row in rows:
            if isinstance(row, dict):
                for field in row:
                    if field not in fields:
                        fields.append(field)
        cleaned: list[dict[str, str]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            cleaned.append({field: str(row.get(field, "") or "").strip() for field in fields})
        write_csv(self.inventory_path, cleaned, fields)
        after_hash = file_sha256(self.inventory_path)
        summary = self._reference_change_summary(before_rows, cleaned, fields)
        event = self._append_change_log("reference_inventory", "references/reference_inventory.csv", summary, before_hash, after_hash)
        return {"saved_at_kst": now_kst(), "path": "references/reference_inventory.csv", "count": str(len(cleaned)), "change_summary": summary, "change_id": event["changed_at_kst"]}

    def open_folder(self, key: str) -> dict[str, str]:
        target, label = self._allowed_folder(key)
        self._open_local_path(target)
        return {"ok": "true", "label": label}

    def _safe_report_file(self, rel_path: str) -> tuple[Path, str]:
        normalized = rel_path.strip().replace("\\", "/")
        if not normalized:
            raise ValueError("연결된 산출물 파일이 없습니다.")
        if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized) or ".." in Path(normalized).parts:
            raise ValueError("프로젝트 내부 상대경로만 열 수 있습니다.")
        if not normalized.startswith(ALLOWED_REPORT_FILE_PREFIXES):
            raise ValueError("reports/ 또는 04_공유_패키지/ 안의 파일만 열 수 있습니다.")
        target = self._safe_project_path(normalized)
        if target.suffix.lower() not in ALLOWED_REPORT_FILE_SUFFIXES:
            raise ValueError("허용되지 않은 파일 형식입니다.")
        if not target.exists() or not target.is_file():
            raise ValueError("산출물 파일을 찾을 수 없습니다.")
        return target, normalized

    def _open_local_path(self, target: Path) -> None:
        if os.environ.get("PROJECT_DASHBOARD_DISABLE_OPEN") == "1":
            return
        if os.name == "nt":
            os.startfile(str(target))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])

    def open_report_file(self, rel_path: str) -> dict[str, str]:
        target, normalized = self._safe_report_file(rel_path)
        self._open_local_path(target)
        return {"ok": "true", "path": normalized}

    def scan_materials(self) -> dict[str, object]:
        materials_dir, _ = self._allowed_folder("materials")
        fields, before_rows = read_csv_with_fields(self.inventory_path, INVENTORY_FIELDS)
        before_hash = file_sha256(self.inventory_path)
        existing_hashes = {row.get("sha256", "") for row in before_rows if row.get("sha256")}
        existing_paths = {row.get("original_path", "") for row in before_rows if row.get("original_path")}
        rows = list(before_rows)
        added: list[dict[str, str]] = []
        for file_path in sorted(materials_dir.rglob("*")):
            if not file_path.is_file() or file_path.name.startswith("~$") or file_path.name == "README.txt":
                continue
            rel_path = file_path.relative_to(self.project_dir).as_posix()
            digest = file_sha256(file_path)
            if digest in existing_hashes or rel_path in existing_paths:
                continue
            row = {field: "" for field in fields}
            row["reference_id"] = f"REF-FILE-{digest[:12]}"
            row["listed_at_kst"] = now_kst()
            row["title"] = file_path.stem
            row["file_type"] = file_path.suffix.lower().lstrip(".") or "file"
            row["material_origin"] = "user_provided"
            row["material_origin_ko"] = "사용자 제공"
            row["visibility"] = "internal"
            row["visibility_ko"] = "내부"
            row["original_path"] = rel_path
            row["open_path"] = rel_path
            row["sha256"] = digest
            row["file_size_bytes"] = str(file_path.stat().st_size)
            row["last_modified_kst"] = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M KST")
            row["intake_status"] = "received"
            row["parse_status"] = "not_started"
            row["normalized_status"] = "not_started"
            rows.append(row)
            added.append(row)
            existing_hashes.add(digest)
            existing_paths.add(rel_path)
        if added:
            write_csv(self.inventory_path, rows, fields)
            after_hash = file_sha256(self.inventory_path)
            summary = f"자료 폴더 스캔 추가 {len(added)}건"
            self._append_change_log("reference_inventory", "references/reference_inventory.csv", summary, before_hash, after_hash)
        return {"added": len(added), "rows": rows, "fields": fields, "saved_at_kst": now_kst()}

    def start_reference_normalization(self) -> dict[str, object]:
        materials_dir, _ = self._allowed_folder("materials")
        with self.reference_job_lock:
            if bool(self.reference_job.get("running")):
                return dict(self.reference_job)
            batch_id = "dashboard_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            log_rel = Path("project_state") / f"{batch_id}_reference_normalization.log"
            self.reference_job = {
                "running": True,
                "status": "running",
                "message": "자료 파싱/정규화/색인을 실행 중입니다.",
                "started_at_kst": now_kst(),
                "finished_at_kst": "",
                "log_path": log_rel.as_posix(),
                "returncode": "",
            }
        threading.Thread(target=self._run_reference_normalization, args=(materials_dir, batch_id, log_rel), daemon=True).start()
        return self.reference_normalization_status()

    def _run_reference_normalization(self, materials_dir: Path, batch_id: str, log_rel: Path) -> None:
        log_path = self.project_dir / log_rel
        log_path.parent.mkdir(parents=True, exist_ok=True)
        before_hash = file_sha256(self.inventory_path)
        tool_path = self.workspace_dir / "_ai_system" / "tools" / "intake_reference_batch.py"
        index_tool_path = self.workspace_dir / "_ai_system" / "tools" / "build_project_context_db.py"
        cmd = [sys.executable, str(tool_path), str(materials_dir), str(self.project_dir), batch_id]
        index_cmd = [sys.executable, str(index_tool_path), "--project", self.project_dir.name]
        try:
            proc = subprocess.run(cmd, cwd=self.workspace_dir, text=True, capture_output=True, timeout=600, check=False)
            index_proc: subprocess.CompletedProcess[str] | None = None
            if proc.returncode == 0:
                index_proc = subprocess.run(
                    index_cmd,
                    cwd=self.workspace_dir,
                    text=True,
                    capture_output=True,
                    timeout=600,
                    check=False,
                )
            index_returncode = index_proc.returncode if index_proc is not None else ""
            index_stdout = index_proc.stdout if index_proc is not None else ""
            index_stderr = index_proc.stderr if index_proc is not None else ""
            log_body = [
                f"started_at_kst: {self.reference_job.get('started_at_kst', '')}",
                f"finished_at_kst: {now_kst()}",
                "command: intake_reference_batch.py <materials_dir> <project_dir> <batch_id>",
                f"returncode: {proc.returncode}",
                "",
                "[stdout]",
                proc.stdout,
                "",
                "[stderr]",
                proc.stderr,
                "",
                "[context_index]",
                "command: build_project_context_db.py --project <project_name>",
                f"returncode: {index_returncode}",
                "",
                "[context_index stdout]",
                index_stdout,
                "",
                "[context_index stderr]",
                index_stderr,
            ]
            log_path.write_text("\n".join(log_body), encoding="utf-8")
            after_hash = file_sha256(self.inventory_path)
            if before_hash != after_hash:
                self._append_change_log(
                    "reference_inventory",
                    "references/reference_inventory.csv",
                    "문서 파싱/정규화/색인 상태 갱신",
                    before_hash,
                    after_hash,
                )
            if proc.returncode == 0 and index_proc is not None and index_proc.returncode == 0:
                status = "done"
                message = "자료 파싱/정규화/색인이 완료되었습니다."
                returncode = "parse=0,index=0"
            elif proc.returncode == 0 and index_proc is not None:
                status = "partial"
                message = "자료 파싱/정규화는 완료되었지만 색인 갱신에 실패했습니다."
                returncode = f"parse=0,index={index_proc.returncode}"
            else:
                status = "failed"
                message = "자료 파싱/정규화 중 오류가 발생했습니다."
                returncode = f"parse={proc.returncode},index=not_run"
            with self.reference_job_lock:
                self.reference_job.update(
                    {
                        "running": False,
                        "status": status,
                        "message": message,
                        "finished_at_kst": now_kst(),
                        "returncode": returncode,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            log_path.write_text(f"error: {type(exc).__name__}: {exc}\n", encoding="utf-8")
            with self.reference_job_lock:
                self.reference_job.update(
                    {
                        "running": False,
                        "status": "failed",
                        "message": f"자료 파싱/정규화/색인 실패: {type(exc).__name__}",
                        "finished_at_kst": now_kst(),
                        "returncode": "error",
                    }
                )

    def reference_normalization_status(self) -> dict[str, object]:
        with self.reference_job_lock:
            return dict(self.reference_job)

    def current_task_status(self) -> dict[str, str]:
        path = self.project_dir / "tasks" / "current_task.md"
        if not path.exists():
            return {
                "exists": "false",
                "status": "missing",
                "user_label": "작업 현황 파일 없음",
                "ai_task": "AI가 다음 작업 전에 tasks/current_task.md를 생성해야 합니다.",
                "read_before_work": "",
                "next_stage": "",
                "updated_at_kst": "",
            }
        rows = parse_task_rows(path.read_text(encoding="utf-8", errors="ignore"))
        active = next((row for row in rows if row.get("status") == "active"), None)
        if not active:
            return {
                "exists": "true",
                "status": "no_active_stage",
                "user_label": "활성 단계 없음",
                "ai_task": "AI가 현재 단계를 갱신해야 합니다.",
                "read_before_work": "",
                "next_stage": "",
                "updated_at_kst": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M KST"),
            }
        return {
            "exists": "true",
            "status": active.get("status", ""),
            "stage_id": active.get("stage_id", ""),
            "user_label": active.get("user_label", ""),
            "ai_task": active.get("ai_task", ""),
            "read_before_work": active.get("read_before_work", ""),
            "next_stage": active.get("next_stage", ""),
            "updated_at_kst": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M KST"),
        }

    def _reference_change_summary(self, before_rows: list[dict[str, str]], after_rows: list[dict[str, str]], fields: list[str]) -> str:
        before = row_map(before_rows, "reference_id")
        after = row_map(after_rows, "reference_id")
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        safe_fields = redactable_fields(fields)
        changed: list[str] = []
        for reference_id in sorted(set(before) & set(after)):
            fields_changed = changed_fields(before[reference_id], after[reference_id], safe_fields)
            if fields_changed:
                changed.append(f"{reference_id}({', '.join(fields_changed[:8])})")
        parts: list[str] = []
        if len(before_rows) != len(after_rows):
            parts.append(f"문서 행 {len(before_rows)}->{len(after_rows)}")
        if added:
            parts.append("추가 " + ", ".join(added[:5]))
        if removed:
            parts.append("삭제 " + ", ".join(removed[:5]))
        if changed:
            parts.append("변경 " + "; ".join(changed[:5]))
        return "; ".join(parts) if parts else "문서 대장 저장"

    def summary(self) -> dict[str, object]:
        return {
            "project_name": self.project_dir.name,
            "project_title": self.profile().get("project_name") or self.project_dir.name,
            "project_owner": self.project_owner(),
            "report_count": len(self.report_registry()),
            "reference_count": int(self.reference_inventory()["count"]),
            "current_task": self.current_task_status(),
            "recent_changes": self.changes(limit=3),
            "updated_at_kst": now_kst(),
        }


class SessionState:
    def __init__(self, idle_timeout_seconds: int, shutdown_grace_seconds: int):
        self.idle_timeout_seconds = idle_timeout_seconds
        self.shutdown_grace_seconds = shutdown_grace_seconds
        self.last_activity = time.monotonic()
        self.shutting_down = False
        self.shutdown_reason = ""
        self.server: ThreadingHTTPServer | None = None
        self.lock = threading.Lock()

    def touch(self) -> None:
        with self.lock:
            if not self.shutting_down:
                self.last_activity = time.monotonic()

    def heartbeat(self) -> dict[str, object]:
        with self.lock:
            remaining = max(0, int(self.idle_timeout_seconds - (time.monotonic() - self.last_activity)))
            return {
                "ok": True,
                "shutting_down": self.shutting_down,
                "reason": self.shutdown_reason,
                "idle_timeout_seconds": self.idle_timeout_seconds,
                "remaining_seconds": remaining,
            }

    def begin_shutdown(self, reason: str) -> None:
        should_schedule = False
        with self.lock:
            if not self.shutting_down:
                self.shutting_down = True
                self.shutdown_reason = reason
                should_schedule = True
        if should_schedule:
            threading.Timer(self.shutdown_grace_seconds, self.stop_server).start()

    def stop_server(self) -> None:
        if self.server is not None:
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def monitor_idle(self) -> None:
        while True:
            time.sleep(1.0)
            with self.lock:
                if self.shutting_down:
                    return
                idle_for = time.monotonic() - self.last_activity
                timed_out = idle_for >= self.idle_timeout_seconds
            if timed_out:
                self.begin_shutdown("idle_timeout")
                return


COMMON_CSS = """
@import url('/assets/fonts/pretendard.css');
:root { --blue:#3B5BDB; --blue-dark:#263C96; --dark:#111827; --line:#D8DEE9; --bg:#F4F7FB; --soft:#EEF2F7; --text:#1F2937; --muted:#667085; --warn:#B42318; --ok:#087F5B; --amber:#B54708; --shadow:0 12px 32px rgba(17,24,39,.08); --shadow-soft:0 6px 18px rgba(17,24,39,.06); }
* { box-sizing:border-box; }
body { margin:0; font-family:"Pretendard","Noto Sans KR","Malgun Gothic",system-ui,-apple-system,BlinkMacSystemFont,sans-serif; background:linear-gradient(180deg,#F8FAFF 0%,var(--bg) 42%,#F7F8FB 100%); color:var(--text); line-height:1.6; word-break:keep-all; }
main { max-width:1140px; margin:0 auto; padding:30px 24px 64px; }
header { margin-bottom:20px; }
h1 { color:var(--dark); font-size:30px; margin:0 0 8px; line-height:1.35; overflow-wrap:anywhere; }
h2 { color:var(--dark); font-size:20px; margin:22px 0 10px; }
p { margin:8px 0; }
a { color:var(--blue); font-weight:700; text-decoration:none; }
.lead,.status,.small { color:var(--muted); }
.small { font-size:13px; }
.top-actions,.actions,.btn-row { display:flex; flex-wrap:wrap; gap:8px; }
.top-actions { align-items:center; background:rgba(255,255,255,.86); border:1px solid rgba(216,222,233,.9); border-radius:8px; box-shadow:var(--shadow-soft); padding:8px; position:sticky; top:12px; z-index:20; backdrop-filter:blur(12px); }
.top-actions .danger { margin-left:auto; }
.panel,.card { background:rgba(255,255,255,.96); border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow-soft); padding:18px; margin:14px 0; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,430px),1fr)); gap:12px; }
.hero { background:linear-gradient(135deg,#FFFFFF 0%,#F5F7FF 48%,#EAF0FF 100%); border:1px solid rgba(177,190,235,.8); border-radius:8px; box-shadow:var(--shadow); padding:22px; margin:16px 0 14px; position:relative; overflow:hidden; }
.hero::before { background:var(--blue); border-radius:999px; content:""; height:64px; left:-56px; position:absolute; top:22px; width:72px; }
.hero-title { color:var(--dark); font-size:28px; font-weight:900; line-height:1.35; overflow-wrap:anywhere; }
.hero-subtitle { color:var(--muted); font-size:13px; margin-top:4px; overflow-wrap:anywhere; }
.metric-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,230px),1fr)); gap:12px; }
.metric { background:#fff; border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow-soft); padding:16px; transition:transform .16s ease, box-shadow .16s ease; }
.metric:hover,.action-card:hover,.list-card:hover { box-shadow:var(--shadow); transform:translateY(-1px); }
.metric-label { color:var(--muted); font-size:13px; font-weight:800; }
.metric-value { color:var(--dark); font-size:22px; font-weight:900; line-height:1.35; margin-top:4px; overflow-wrap:anywhere; }
.action-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr)); gap:12px; }
.action-card { background:#fff; border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow-soft); padding:16px; display:flex; flex-direction:column; gap:8px; min-height:150px; transition:transform .16s ease, box-shadow .16s ease; }
.action-card .link-btn { align-self:flex-start; margin-top:auto; }
.list-card { background:#fff; border:1px solid var(--line); border-radius:8px; box-shadow:var(--shadow-soft); margin:12px 0; padding:14px; transition:transform .16s ease, box-shadow .16s ease; }
.list-card-head { align-items:flex-start; display:flex; flex-wrap:wrap; gap:10px; justify-content:space-between; }
.list-card-title { color:var(--dark); font-size:17px; font-weight:900; overflow-wrap:anywhere; }
.section-head { align-items:center; display:flex; flex-wrap:wrap; gap:10px; justify-content:space-between; margin-top:18px; }
.section-head h2 { margin:0; }
.pill-row { display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; }
.pill { background:var(--soft); border:1px solid var(--line); border-radius:999px; color:var(--dark); font-size:12px; font-weight:800; padding:3px 8px; }
.pill.locked { background:#F8FAFC; color:var(--muted); }
.edit-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr)); gap:10px; margin-top:10px; }
.detail-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); gap:10px; margin-top:10px; }
.muted-box { background:var(--soft); border:1px solid var(--line); border-radius:8px; color:var(--muted); padding:12px; }
button,.link-btn { align-items:center; border:1px solid var(--blue); background:#fff; border-radius:8px; color:var(--blue); cursor:pointer; display:inline-flex; gap:7px; font:inherit; font-weight:800; justify-content:center; padding:8px 12px; text-decoration:none; transition:background .14s ease,border-color .14s ease,color .14s ease,box-shadow .14s ease,transform .14s ease; }
.icon { display:inline-block; fill:currentColor; flex:0 0 auto; height:16px; width:16px; }
.icon.large { height:20px; width:20px; }
button.primary { background:var(--blue); color:#fff; box-shadow:0 8px 18px rgba(59,91,219,.18); }
button.danger { border-color:var(--warn); color:var(--warn); }
button.path { border-color:var(--ok); color:var(--ok); }
button.secondary { border-color:var(--muted); color:var(--muted); }
button:hover,.link-btn:hover { background:var(--blue); color:#fff; text-decoration:none; transform:translateY(-1px); }
.link-btn.active { background:var(--blue); color:#fff; box-shadow:0 8px 18px rgba(59,91,219,.16); }
button.path:hover { background:var(--ok); color:#fff; }
button.danger:hover { background:var(--warn); color:#fff; }
button.secondary:hover { background:var(--muted); color:#fff; }
button:disabled,input:disabled,select:disabled,textarea:disabled { cursor:not-allowed; opacity:.55; }
input,select,textarea { width:100%; border:1px solid var(--line); border-radius:8px; padding:9px 10px; font:inherit; min-width:120px; outline:none; transition:border-color .14s ease,box-shadow .14s ease; }
input:focus,select:focus,textarea:focus { border-color:var(--blue); box-shadow:0 0 0 3px rgba(59,91,219,.14); }
input.field-error,select.field-error,textarea.field-error { border-color:var(--warn); box-shadow:0 0 0 3px rgba(180,35,24,.12); }
textarea { min-height:72px; resize:vertical; }
label { color:var(--dark); display:block; font-size:13px; font-weight:700; }
table { width:100%; border-collapse:collapse; background:#fff; min-width:960px; }
th,td { border-bottom:1px solid var(--line); padding:8px; text-align:left; vertical-align:top; }
th { background:var(--soft); color:var(--dark); font-size:13px; }
.table-wrap { overflow-x:auto; }
.summary-row { display:grid; gap:12px; grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr)); }
.summary-card { background:#fff; border:1px solid var(--line); border-radius:8px; padding:14px; }
.summary-card strong { color:var(--dark); display:block; font-size:16px; }
.compact-list { display:grid; gap:10px; }
.compact-item { background:#fff; border:1px solid var(--line); border-radius:8px; padding:12px; }
.advanced { margin-top:12px; }
.advanced summary { color:var(--blue); cursor:pointer; font-weight:800; }
.change-list { margin:8px 0 0; padding-left:18px; }
.change-list li { margin:4px 0; }
code { background:var(--soft); padding:2px 5px; }
.hidden { display:none; }
#sessionOverlay { align-items:center; backdrop-filter:blur(10px); background:rgba(15,23,42,.66); color:#fff; display:none; inset:0; justify-content:center; padding:24px; position:fixed; z-index:9999; }
#sessionOverlay.visible { display:flex; }
.overlay-card { background:rgba(255,255,255,.98); border:1px solid rgba(216,222,233,.92); color:var(--text); max-width:560px; padding:28px; border-radius:8px; box-shadow:0 24px 70px rgba(0,0,0,.30); }
.overlay-card h2 { margin-top:0; }
#sessionBanner { background:#FEF3C7; border-bottom:1px solid #F59E0B; color:#7C2D12; display:none; font-weight:800; left:0; padding:12px 18px; position:sticky; right:0; top:0; z-index:9998; }
#sessionBanner.visible { display:block; }
#toastRegion { bottom:22px; display:grid; gap:8px; position:fixed; right:22px; z-index:10000; }
.toast { background:var(--dark); border-radius:8px; box-shadow:var(--shadow); color:#fff; font-weight:800; max-width:min(420px,calc(100vw - 44px)); padding:12px 14px; }
.toast.ok { background:var(--ok); }
.toast.warn { background:var(--amber); }
.toast.error { background:var(--warn); }
@media (max-width:760px) { main { padding:22px 18px 52px; } .top-actions { position:static; } .top-actions .danger { margin-left:0; } }
"""


COMMON_JS = """
let sessionEnded = false;
let activityTimer = null;
let unsavedChanges = false;
function markActivity() {
  if (sessionEnded) return;
  clearTimeout(activityTimer);
  activityTimer = setTimeout(() => {
    fetch('/api/activity', { method:'POST' }).catch(() => {});
  }, 300);
}
function showToast(message, type = 'ok') {
  const region = document.getElementById('toastRegion');
  if (!region) return;
  const toast = document.createElement('div');
  toast.className = 'toast ' + type;
  toast.textContent = message;
  region.appendChild(toast);
  setTimeout(() => { toast.remove(); }, 2400);
}
function markDirty() {
  unsavedChanges = true;
}
function clearDirty() {
  unsavedChanges = false;
}
function confirmLeaveIfDirty() {
  return !unsavedChanges || confirm('저장되지 않은 변경 사항이 있습니다. 이동하시겠습니까?');
}
function disableInteractive() {
  document.querySelectorAll('button,input,select,textarea').forEach((el) => { el.disabled = true; });
}
function showEnding(message) {
  const banner = document.getElementById('sessionBanner');
  if (banner) {
    banner.textContent = message || '세션이 종료됩니다.';
    banner.classList.add('visible');
  }
}
function showEnded() {
  sessionEnded = true;
  disableInteractive();
  const overlay = document.getElementById('sessionOverlay');
  if (overlay) overlay.classList.add('visible');
}
function fallbackCopy(text) {
  const area = document.createElement('textarea');
  area.value = text;
  area.style.position = 'fixed';
  area.style.left = '-9999px';
  document.body.appendChild(area);
  area.select();
  document.execCommand('copy');
  document.body.removeChild(area);
}
function copyText(text, statusId) {
  const done = () => {
    const status = document.getElementById(statusId || 'status');
    if (status) status.textContent = '복사했습니다: ' + text;
    showToast('경로를 복사했습니다.', 'ok');
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done).catch(() => { fallbackCopy(text); done(); });
  } else {
    fallbackCopy(text);
    done();
  }
}
async function openFolder(folderKey, label) {
  try {
    const response = await fetch('/api/open-folder', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ key:folderKey }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || response.status);
    showToast((label || data.label || '폴더') + '를 열었습니다.', 'ok');
  } catch (error) {
    showToast('폴더를 열지 못했습니다. 경로 복사를 사용해 주세요.', 'error');
  }
}
async function openReportFile(path) {
  if (!path) {
    showToast('연결된 산출물 파일이 없습니다.', 'error');
    return;
  }
  try {
    const response = await fetch('/api/open-report', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ path }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || response.status);
    showToast('산출물 파일을 열었습니다.', 'ok');
  } catch (error) {
    showToast('산출물을 열지 못했습니다. 파일 경로를 확인해 주세요.', 'error');
  }
}
async function checkHeartbeat() {
  if (sessionEnded) return;
  try {
    const response = await fetch('/api/heartbeat', { cache:'no-store' });
    if (!response.ok) throw new Error('heartbeat failed');
    const data = await response.json();
    if (data.shutting_down) {
      showEnding('세션이 종료됩니다. 잠시 후 저장 기능이 비활성화됩니다.');
    }
  } catch (error) {
    showEnded();
  }
}
document.addEventListener('input', markActivity);
document.addEventListener('click', markActivity);
document.addEventListener('keydown', markActivity);
window.addEventListener('load', () => {
  document.querySelectorAll('a[href]').forEach((link) => {
    link.addEventListener('click', (event) => {
      if (!confirmLeaveIfDirty()) event.preventDefault();
    });
  });
  setInterval(checkHeartbeat, 3000);
  checkHeartbeat();
});
window.addEventListener('beforeunload', (event) => {
  if (!unsavedChanges) return;
  event.preventDefault();
  event.returnValue = '';
});
async function shutdownDashboard() {
  if (!confirmLeaveIfDirty()) return;
  try {
    await fetch('/api/shutdown', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ reason:'user_requested' }) });
    showEnding('대시보드 세션을 종료합니다.');
    setTimeout(showEnded, 1200);
  } catch (error) {
    showEnded();
  }
}
"""


def nav_link(label: str, href: str, key: str, active: str) -> str:
    class_name = "link-btn active" if key == active else "link-btn"
    icon_name = {
        "dashboard": "dashboard",
        "profile": "user",
        "reports": "report",
        "references": "folder",
        "changes": "list",
    }.get(key, "list")
    return f'<a class="{class_name}" href="{href}">{icon(icon_name)}{label}</a>'


def layout(title: str, body: str, nav: str = "", active: str = "dashboard") -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="icon" href="data:,">
  <style>{COMMON_CSS}</style>
</head>
<body>
{ICON_SPRITE}
<div id="sessionBanner" role="status"></div>
<main>
  <header>
    <div class="top-actions">
      {nav_link("대시보드", "/", "dashboard", active)}
      {nav_link("프로젝트 정보", "/profile", "profile", active)}
      {nav_link("산출물 관리", "/reports", "reports", active)}
      {nav_link("문서 대장", "/references", "references", active)}
      {nav_link("수정 이력", "/changes", "changes", active)}
      <button class="danger" type="button" onclick="shutdownDashboard()">{icon("stop")}대시보드 종료</button>
    </div>
    {nav}
  </header>
  {body}
</main>
<div id="toastRegion" aria-live="polite" aria-atomic="true"></div>
<div id="sessionOverlay" role="alertdialog" aria-modal="true">
  <div class="overlay-card">
    <h2>대시보드 연결이 종료되었습니다</h2>
    <p>장시간 사용이 없어 서버가 종료되었습니다. 다시 실행 파일을 열어 주세요.</p>
  </div>
</div>
<script>{COMMON_JS}</script>
</body>
</html>"""


def change_list_html(changes: list[dict[str, str]], empty_text: str = "아직 대시보드 저장 이력이 없습니다.") -> str:
    if not changes:
        return f"<p class=\"small\">{html.escape(empty_text)}</p>"
    items = []
    for item in changes[:3]:
        label = f"{item.get('changed_at_kst', '')} · {item.get('scope', '')} · {item.get('summary', '')}"
        items.append(f"<li>{html.escape(label)}</li>")
    return "<ul class=\"change-list\">" + "".join(items) + "</ul>"


def dashboard_page(store: DashboardStore) -> str:
    summary = store.summary()
    profile = store.profile()
    explicit_title = str(profile.get("project_name") or "").strip()
    folder_name = str(summary["project_name"])
    display_title = explicit_title or "프로젝트명 미입력"
    recent_changes = change_list_html(summary.get("recent_changes", []) if isinstance(summary.get("recent_changes"), list) else [])
    project_dir = store.project_dir
    material_path = str(project_dir / "01_자료_넣는_곳")
    logo_path = str(project_dir / "brand_assets")
    reports_path = str(project_dir / "reports")
    share_path = str(project_dir / "04_공유_패키지")
    material_path_js = json.dumps(material_path, ensure_ascii=False)
    logo_path_js = json.dumps(logo_path, ensure_ascii=False)
    reports_path_js = json.dumps(reports_path, ensure_ascii=False)
    share_path_js = json.dumps(share_path, ensure_ascii=False)
    current_task = summary.get("current_task", {}) if isinstance(summary.get("current_task"), dict) else {}
    nav = f"""<div class="hero">
  <div class="hero-title">{html.escape(display_title)}</div>
  <div class="hero-subtitle">폴더명: {html.escape(folder_name)}</div>
  <p class="lead">프로젝트 정보, 산출물 관리, 문서 대장을 다루는 서버형 작업관리 화면입니다. 문서 대장은 사용자 제공 자료와 정확 링크 후보를 정리하고, 출처 위치 보강과 인용 검증은 AI가 별도 작업 흐름에서 수행합니다.</p>
</div>"""
    body = f"""
<section class="metric-grid" aria-label="프로젝트 요약">
  <div class="metric">
    <div class="metric-label">대표 책임자</div>
    <div class="metric-value">{html.escape(str(summary['project_owner']))}</div>
    <p class="small">프로젝트 정보의 첫 번째 책임자가 대표 책임자로 표시됩니다.</p>
  </div>
  <div class="metric">
    <div class="metric-label">보고서</div>
    <div class="metric-value">{summary['report_count']}건</div>
    <p class="small">산출물별 단계와 버전은 산출물 관리에서 확인합니다.</p>
  </div>
  <div class="metric">
    <div class="metric-label">문서</div>
    <div class="metric-value">{summary['reference_count']}건</div>
    <p class="small">사용자 제공 파일과 직접 등록한 정확 링크 후보를 포함한 대장 기준 문서 수입니다.</p>
  </div>
</section>

<section class="panel">
  <h2>기록 기준 현재 작업</h2>
  <div class="summary-row">
    <div class="summary-card">
      <span class="small">현재 단계</span>
      <strong>{html.escape(str(current_task.get('user_label', '확인 필요')))}</strong>
    </div>
    <div class="summary-card">
      <span class="small">AI가 다음에 확인할 일</span>
      <strong>{html.escape(str(current_task.get('ai_task', 'tasks/current_task.md 확인 필요')))}</strong>
    </div>
    <div class="summary-card">
      <span class="small">마지막 갱신</span>
      <strong>{html.escape(str(current_task.get('updated_at_kst', '') or '미확인'))}</strong>
    </div>
  </div>
  <p class="small">이 현황은 AI가 남긴 작업 기록 기준입니다. 실제 보고서 품질, 출처 진위, 인용 가능 여부를 자동 판정하지 않습니다.</p>
</section>

<details class="panel">
  <summary><strong>자료 위치와 폴더 경로</strong></summary>
  <h2>경로 복사</h2>
  <p class="small">복사한 경로는 Windows 탐색기 주소창에 붙여 넣어 여세요. 이 화면에서는 폴더를 직접 실행하지 않습니다.</p>
  <div class="btn-row">
    <button class="primary" type="button" onclick="openFolder('materials','자료 폴더')">{icon("folder")}자료 폴더 열기</button>
    <button class="path" type="button" onclick='copyText({material_path_js})'>{icon("copy")}자료 폴더 경로 복사</button>
    <button type="button" onclick="openFolder('brand_assets','로고 폴더')">{icon("folder")}로고 폴더 열기</button>
    <button class="path" type="button" onclick='copyText({logo_path_js})'>{icon("copy")}로고 폴더 경로 복사</button>
    <button type="button" onclick="openFolder('reports','보고서 폴더')">{icon("folder")}보고서 폴더 열기</button>
    <button class="path" type="button" onclick='copyText({reports_path_js})'>{icon("copy")}보고서 폴더 경로 복사</button>
    <button type="button" onclick="openFolder('share','공유 패키지 폴더')">{icon("folder")}공유 패키지 폴더 열기</button>
    <button class="path" type="button" onclick='copyText({share_path_js})'>{icon("copy")}공유 패키지 경로 복사</button>
  </div>
  <p class="small">로고는 <code>brand_assets/project_logo.png</code> 파일명만 자동 사용합니다. 같은 폴더에 다른 이미지가 있어도 자동 선택하지 않습니다.</p>
</details>

<section class="panel">
  <h2>최근 저장 이력</h2>
  {recent_changes}
  <p><a href="/changes">전체 수정 이력 보기</a></p>
</section>
<p id="status" class="status" aria-live="polite"></p>
"""
    return layout("프로젝트 대시보드", body, nav, "dashboard")


def profile_page(store: DashboardStore) -> str:
    profile_json = json.dumps(store.profile(), ensure_ascii=False)
    recent_changes = change_list_html(store.changes("project_profile", 3))
    nav = """<h1>프로젝트 정보</h1>
<p class="lead">책임자, 결재라인, 담당 실무자, 외부 담당자를 저장합니다. 첫 번째 책임자가 프로젝트 대시보드의 대표 책임자로 표시됩니다.</p>"""
    body = f"""
<section class="panel">
  <div class="actions">
    <button class="primary" type="button" onclick="saveProfile()">{icon("save")}저장</button>
  </div>
  <p id="status" class="status" aria-live="polite"></p>
</section>
<section class="panel">
  <h2>기본 정보</h2>
  <div class="grid">
    <label>프로젝트명 <input id="project_name" type="text"></label>
    <label>조직/회사명 <input id="organization_name" type="text"></label>
  </div>
  <p class="small">프로젝트 로고는 <code>brand_assets/project_logo.png</code>만 자동 사용합니다.</p>
</section>
<section class="panel" id="sections"></section>
<section class="panel">
  <h2>최근 프로젝트 정보 저장 이력</h2>
  {recent_changes}
</section>
<script id="profileData" type="application/json">{profile_json}</script>
<script>
let profile = JSON.parse(document.getElementById('profileData').textContent);
const fieldSets = {{
  responsible_people: ['name', 'title', 'organization', 'phone', 'email', 'notes'],
  approval_line: ['rank', 'name', 'title', 'organization', 'phone', 'email', 'notes'],
  practitioners: ['name', 'title', 'organization', 'phone', 'email', 'notes'],
  external_contacts: ['company', 'department', 'name', 'title', 'phone', 'email', 'notes']
}};
const sectionLabels = {{
  responsible_people: '책임자',
  approval_line: '결재라인',
  practitioners: '담당 실무자',
  external_contacts: '외부 담당자'
}};
const labels = {{ rank:'순번', company:'회사명', department:'부서·팀', name:'이름', title:'직책', organization:'소속', phone:'연락처', email:'이메일', notes:'비고' }};
function emptyContact() {{ return {{ company:'', department:'', name:'', title:'', organization:'', phone:'', email:'', notes:'' }}; }}
function sectionArray(section) {{ if (!Array.isArray(profile[section])) profile[section] = []; return profile[section]; }}
function escapeAttr(value) {{ return String(value || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'); }}
function render() {{
  document.getElementById('project_name').value = profile.project_name || '';
  document.getElementById('organization_name').value = profile.organization_name || '';
  const html = Object.keys(fieldSets).map((section) => {{
    const arr = sectionArray(section);
    const minRows = (section === 'responsible_people' || section === 'practitioners') ? 1 : 0;
    const help = section === 'responsible_people' ? '<p class="small">첫 번째 책임자가 프로젝트 대시보드의 대표 책임자로 표시됩니다.</p>' : '';
    const addLabels = {{ responsible_people:'책임자 추가', approval_line:'결재자 추가', practitioners:'실무자 추가', external_contacts:'외부 담당자 추가' }};
    const rows = arr.map((row, index) => {{
      const canDelete = arr.length > minRows;
      return '<tr>' + fieldSets[section].map((field) => {{
        if (field === 'rank') return '<td><strong>' + String(index + 1) + '</strong></td>';
        return '<td><input data-section="' + section + '" data-index="' + index + '" data-field="' + field + '" value="' + escapeAttr(row[field]) + '"></td>';
      }}).join('') + '<td>' + (canDelete ? '<button class="danger" type="button" onclick="removeRow(\\'' + section + '\\',' + index + ')">삭제</button>' : '<button class="danger" type="button" disabled>필수</button>') + '</td></tr>';
    }}).join('');
    const addButton = '<div class="btn-row"><button type="button" onclick="addRow(\\'' + section + '\\')">+ ' + addLabels[section] + '</button></div>';
    return '<div class="section-head"><h2>' + sectionLabels[section] + '</h2>' + addButton + '</div>' + help + '<div class="table-wrap"><table><thead><tr>' + fieldSets[section].map((field) => '<th>' + labels[field] + '</th>').join('') + '<th>관리</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
  }}).join('');
  document.getElementById('sections').innerHTML = html;
}}
function sync() {{
  profile.project_name = document.getElementById('project_name').value.trim();
  profile.organization_name = document.getElementById('organization_name').value.trim();
  profile.brand_assets = profile.brand_assets || {{}};
  profile.brand_assets.project_logo_filename = 'project_logo.png';
  document.querySelectorAll('input[data-section]').forEach((input) => {{
    const arr = sectionArray(input.dataset.section);
    if (!arr[input.dataset.index]) arr[input.dataset.index] = emptyContact();
    arr[input.dataset.index][input.dataset.field] = input.value.trim();
  }});
}}
function clearValidation() {{
  document.querySelectorAll('.field-error').forEach((el) => el.classList.remove('field-error'));
}}
function markInvalid(input, message) {{
  input.classList.add('field-error');
  if (!document.getElementById('status').textContent) document.getElementById('status').textContent = message;
}}
function hasNamedPerson(section) {{
  return sectionArray(section).some((row) => String(row.name || '').trim() && String(row.name || '').trim() !== '미지정');
}}
function validateProfile() {{
  clearValidation();
  document.getElementById('status').textContent = '';
  let ok = true;
  const emailPattern = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  const contactPattern = /^[0-9+\\-\\s().]*$/;
  document.querySelectorAll('input[data-field="email"]').forEach((input) => {{
    if (input.value.trim() && !emailPattern.test(input.value.trim())) {{
      ok = false;
      markInvalid(input, '이메일 형식을 확인해 주세요.');
    }}
  }});
  document.querySelectorAll('input[data-field="phone"]').forEach((input) => {{
    if (input.value.trim() && !contactPattern.test(input.value.trim())) {{
      ok = false;
      markInvalid(input, '연락처에는 숫자, 공백, +, -, 괄호만 입력해 주세요.');
    }}
  }});
  if (!hasNamedPerson('responsible_people')) {{
    ok = false;
    document.getElementById('status').textContent = '책임자 이름은 1명 이상 입력해야 합니다.';
  }}
  if (!hasNamedPerson('practitioners')) {{
    ok = false;
    document.getElementById('status').textContent = '담당 실무자 이름은 1명 이상 입력해야 합니다.';
  }}
  if (!ok) showToast(document.getElementById('status').textContent || '입력값을 확인해 주세요.', 'error');
  return ok;
}}
function addRow(section) {{ sync(); sectionArray(section).push(emptyContact()); markDirty(); render(); }}
function removeRow(section, index) {{ sync(); sectionArray(section).splice(index, 1); markDirty(); render(); }}
async function saveProfile() {{
  sync();
  if (!validateProfile()) return;
  const response = await fetch('/api/profile', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(profile) }});
  const data = await response.json();
  document.getElementById('status').textContent = response.ok ? '저장되었습니다. ' + data.saved_at_kst : '저장 실패: ' + (data.error || response.status);
  if (response.ok) {{ clearDirty(); showToast('프로젝트 정보를 저장했습니다.', 'ok'); }} else {{ showToast('저장에 실패했습니다.', 'error'); }}
}}
document.addEventListener('input', (event) => {{ if (event.target.matches('input,select,textarea')) markDirty(); }});
render();
</script>
"""
    return layout("프로젝트 정보", body, nav, "profile")


def reports_page(store: DashboardStore) -> str:
    rows_json = json.dumps(store.report_registry(), ensure_ascii=False)
    fields_json = json.dumps(REPORT_REGISTRY_FIELDS, ensure_ascii=False)
    recent_changes = change_list_html(store.changes("report_registry", 3))
    nav = """<h1>산출물 관리</h1>
<p class="lead">한 프로젝트 안에서 만들어지는 여러 문서 산출물의 분류, 버전, 단계, 담당자, 최신 파일을 관리합니다.</p>"""
    body = f"""
<section class="panel">
  <div class="actions">
    <button class="primary" type="button" onclick="saveRows()">{icon("save")}저장</button>
    <button type="button" onclick="addRow()">{icon("plus")}산출물 추가</button>
  </div>
  <p id="status" class="status" aria-live="polite"></p>
  <div id="registryTable"></div>
</section>
<section class="panel">
  <h2>최근 산출물 관리 저장 이력</h2>
  {recent_changes}
</section>
<script id="fields" type="application/json">{fields_json}</script>
<script id="rows" type="application/json">{rows_json}</script>
<script>
const fields = JSON.parse(document.getElementById('fields').textContent);
let rows = JSON.parse(document.getElementById('rows').textContent);
const labels = {{
  report_id:'산출물 ID', report_title:'산출물명', document_classification:'문서 분류', confidentiality_status:'대외비', version:'버전',
  stage:'단계', owner:'산출물 책임자', practitioners:'담당 실무자', reviewers:'검토자', latest_file:'산출물 파일',
  prd_path:'기획 문서', updated_at_kst:'수정일', next_action:'다음 확인 사항', notes:'비고'
}};
const primaryFields = ['report_title','document_classification','confidentiality_status','version','stage','owner'];
const options = {{
  document_classification:['','내부 검토용','상부 보고용','파트너사 공유용','외부 공유용'],
  confidentiality_status:['','대외비','대외비 아님'],
  stage:['','기획','자료수집','장별작성','표·그래프','조립','내부검토','공유준비','완료','보류']
}};
function emptyRow() {{
  const row = {{}};
  fields.forEach((field) => row[field] = '');
  row.version = 'v0.1';
  row.stage = '기획';
  return row;
}}
function escapeAttr(value) {{ return String(value || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'); }}
function escapeHtml(value) {{ return String(value || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }}
function escapeJs(value) {{ return String(value || '').replaceAll('\\\\','\\\\\\\\').replaceAll("'","\\\\'").replaceAll('\\n',' ').replaceAll('\\r',' '); }}
function control(row, index, field) {{
  const value = row[field] || '';
  if (options[field]) {{
    return '<label>' + labels[field] + '<select data-index="' + index + '" data-field="' + field + '">' + options[field].map((option) => '<option value="' + escapeAttr(option) + '"' + (option === value ? ' selected' : '') + '>' + (option || '선택') + '</option>').join('') + '</select></label>';
  }}
  return '<label>' + labels[field] + '<input data-index="' + index + '" data-field="' + field + '" value="' + escapeAttr(value) + '"></label>';
}}
function render() {{
  if (!rows.length) rows = [emptyRow()];
  document.getElementById('registryTable').innerHTML = rows.map((row, index) => {{
    const title = row.report_title || row.report_id || '산출물명 미입력';
    const pills = ['version','stage','document_classification','confidentiality_status','owner'].map((field) => row[field] ? '<span class="pill">' + escapeHtml(labels[field]) + ': ' + escapeHtml(row[field]) + '</span>' : '').join('');
    const allControls = fields.map((field) => control(row, index, field)).join('');
    const filePath = row.latest_file || '';
    const openButton = filePath
      ? '<button class="primary" type="button" onclick="openReportFile(\\'' + escapeJs(filePath) + '\\')">산출물 열기</button><button class="path" type="button" onclick="copyText(\\'' + escapeJs(filePath) + '\\')">경로 복사</button>'
      : '<button class="secondary" type="button" disabled>산출물 파일 없음</button>';
    return '<section class="list-card"><div class="list-card-head"><div><div class="list-card-title">' + escapeHtml(title) + '</div><div class="pill-row">' + pills + '</div></div><div class="btn-row">' + openButton + '<button class="secondary" type="button" onclick="toggleDetails(\\'report-extra-' + index + '\\')">상세 편집</button><button class="danger" type="button" onclick="removeRow(' + index + ')">삭제</button></div></div><div id="report-extra-' + index + '" class="detail-grid hidden">' + allControls + '</div></section>';
  }}).join('');
}}
function toggleDetails(id) {{ const el = document.getElementById(id); if (el) el.classList.toggle('hidden'); }}
function sync() {{
  document.querySelectorAll('input[data-index], select[data-index]').forEach((input) => {{
    rows[Number(input.dataset.index)][input.dataset.field] = input.value.trim();
  }});
}}
function addRow() {{ sync(); rows.push(emptyRow()); markDirty(); render(); }}
function removeRow(index) {{ sync(); rows.splice(index, 1); markDirty(); render(); }}
async function saveRows() {{
  sync();
  const response = await fetch('/api/report-registry', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{ rows }}) }});
  const data = await response.json();
  document.getElementById('status').textContent = response.ok ? '저장되었습니다. ' + data.saved_at_kst : '저장 실패: ' + (data.error || response.status);
  if (response.ok) {{ clearDirty(); showToast('산출물 관리를 저장했습니다.', 'ok'); }} else {{ showToast('저장에 실패했습니다.', 'error'); }}
}}
document.addEventListener('input', (event) => {{ if (event.target.matches('input,select,textarea')) markDirty(); }});
render();
</script>
"""
    return layout("산출물 관리", body, nav, "reports")


def references_page(store: DashboardStore) -> str:
    inventory = store.reference_inventory()
    rows_json = json.dumps(inventory["rows"], ensure_ascii=False)
    fields_json = json.dumps(inventory["fields"], ensure_ascii=False)
    recent_changes = change_list_html(store.changes("reference_inventory", 3))
    visible_fields = [
        "reference_id",
        "title",
        "file_type",
        "material_origin_ko",
        "visibility_ko",
        "source_tier",
        "intake_status",
        "parse_status",
        "ocr_status",
        "normalized_status",
        "context_index_status",
        "original_path",
        "open_path",
        "sha256",
        "file_size_bytes",
        "last_modified_kst",
        "source_id",
        "notes",
    ]
    visible_json = json.dumps(visible_fields, ensure_ascii=False)
    nav = """<h1>문서 대장</h1>
<p class="lead">프로젝트에 들어온 사용자 제공 자료와 정확 링크 후보를 관리합니다. 파일 다운로드 결과가 아니라 원본/링크 위치, 사용자 보강 필요 여부, 로컬 처리 상태를 분리해 봅니다.</p>"""
    body = f"""
<section class="panel">
  <div class="actions">
    <button class="primary" type="button" onclick="saveReferences()">{icon("save")}저장</button>
    <button type="button" onclick="addReference()">{icon("plus")}문서 추가</button>
    <button type="button" onclick="scanMaterials()">{icon("search")}자료 폴더 스캔</button>
    <button type="button" id="normalizeButton" onclick="startNormalization()">{icon("refresh")}파싱/정규화/색인 실행</button>
  </div>
  <p class="small">사용자는 제목, 출처 성격, 공개 범위, 비고를 직접 정리합니다. 시스템은 파일 해시, 읽기/정규화/색인 상태, source_id 연결 같은 보조 상태만 갱신합니다. 외부 URL은 정확 링크와 출처 위치를 보강하거나 필요한 파일을 사용자 제공 요청으로 남깁니다.</p>
  <p id="status" class="status" aria-live="polite"></p>
  <div id="referenceTable"></div>
</section>
<section class="panel">
  <h2>최근 문서 대장 저장 이력</h2>
  {recent_changes}
</section>
<script id="fields" type="application/json">{fields_json}</script>
<script id="visibleFields" type="application/json">{visible_json}</script>
<script id="rows" type="application/json">{rows_json}</script>
<script>
const fields = JSON.parse(document.getElementById('fields').textContent);
const visibleFields = JSON.parse(document.getElementById('visibleFields').textContent);
let rows = JSON.parse(document.getElementById('rows').textContent);
const labels = {{
  reference_id:'문서 ID', title:'제목', file_type:'유형', material_origin_ko:'출처 성격', visibility_ko:'공개 범위',
  source_tier:'자료 성격', intake_status:'등록 상태', parse_status:'내용 읽기 상태', original_path:'원본/링크 위치',
  open_path:'확인 위치', source_id:'출처 연결', sha256:'파일 해시', file_size_bytes:'파일 크기', last_modified_kst:'수정 시각',
  ocr_status:'OCR 상태', normalized_status:'정규화 상태', context_index_status:'색인 상태', notes:'비고'
}};
const primaryFields = ['title','file_type','material_origin_ko','visibility_ko','notes'];
const systemFields = ['reference_id','source_tier','intake_status','parse_status','ocr_status','normalized_status','context_index_status','source_id','sha256','file_size_bytes','last_modified_kst','original_path','open_path','source_record_path','derived_text_path','normalized_text_path','normalized_manifest_path','normalized_unit_index_path'];
const options = {{
  material_origin_ko:[{value:'',label:'선택'},{value:'사용자 제공',label:'사용자 제공'},{value:'AI 수집 후보',label:'링크 확인 후보'},{value:'외부',label:'외부 링크'},{value:'공식 공개자료',label:'공식 공개자료'},{value:'언론/보조자료',label:'언론/보조자료'}],
  visibility_ko:['','내부','대외비','공개','공개 가능','확인 필요'],
  source_tier:[{{value:'',label:'선택'}},{{value:'Tier 1 - Primary official',label:'공식 원출처'}},{{value:'Tier 1 - Primary legal/regulatory',label:'법령·금융당국 원출처'}},{{value:'Tier 2 - Primary commercial/issuer',label:'기업·기관 공식자료'}},{{value:'Tier 2 - Primary organization',label:'정당·기관 공식자료'}},{{value:'secondary',label:'보조자료'}},{{value:'unknown',label:'검토 필요'}}],
  intake_status:[{{value:'',label:'선택'}},{{value:'manual_lead',label:'수동 등록'}},{{value:'received',label:'자료 접수'}},{{value:'inventoried',label:'대장 등록'}},{{value:'blocked',label:'확인 필요'}},{{value:'needs_ai_intake',label:'정리 필요'}}],
  parse_status:[{{value:'',label:'선택'}},{{value:'not_started',label:'읽기 전'}},{{value:'parsed',label:'읽기 완료'}},{{value:'blocked',label:'확인 필요'}},{{value:'not_applicable',label:'해당 없음'}}]
}};
const valueLabels = {{}};
Object.entries(options).forEach(([field, opts]) => {{
  valueLabels[field] = {{}};
  opts.forEach((option) => {{
    const raw = typeof option === 'string' ? option : option.value;
    const label = typeof option === 'string' ? (option || '선택') : option.label;
    valueLabels[field][raw] = label;
  }});
}});
function escapeAttr(value) {{ return String(value || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;'); }}
function escapeHtml(value) {{ return String(value || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }}
function emptyRow() {{
  const row = {{}};
  fields.forEach((field) => row[field] = '');
  row.reference_id = 'REF-MANUAL-' + Date.now();
  row.listed_at_kst = new Date().toISOString();
  row.intake_status = 'manual_lead';
  return row;
}}
function control(row, index, field) {{
  const value = row[field] || '';
  if (systemFields.includes(field)) {{
    const label = (valueLabels[field] && valueLabels[field][value]) || value || '-';
    return '<div><span class="small">' + (labels[field] || field) + '</span><br><span class="pill locked">' + escapeHtml(label) + '</span></div>';
  }}
  if (options[field]) {{
    return '<label>' + (labels[field] || field) + '<select data-index="' + index + '" data-field="' + field + '">' + options[field].map((option) => {{
      const raw = typeof option === 'string' ? option : option.value;
      const label = typeof option === 'string' ? (option || '선택') : option.label;
      return '<option value="' + escapeAttr(raw) + '"' + (raw === value ? ' selected' : '') + '>' + escapeHtml(label || '선택') + '</option>';
    }}).join('') + '</select></label>';
  }}
  if (field === 'notes') return '<label>' + (labels[field] || field) + '<textarea data-index="' + index + '" data-field="' + field + '">' + escapeAttr(value) + '</textarea></label>';
  return '<label>' + (labels[field] || field) + '<input data-index="' + index + '" data-field="' + field + '" value="' + escapeAttr(value) + '"></label>';
}}
function displayValue(row, field) {{
  const value = row[field] || '';
  if (field === 'source_tier') {{
    if (value.includes('Tier 1') && (value.includes('legal') || value.includes('regulatory'))) return '법령·금융당국 원출처';
    if (value.includes('Tier 1')) return '공식 원출처';
    if (value.includes('commercial') || value.includes('issuer')) return '기업·기관 공식자료';
    if (value.includes('organization')) return '정당·기관 공식자료';
  }}
  if (field === 'material_origin_ko' && value === '외부') return '외부 링크/정확 위치 확인';
  if (valueLabels[field] && valueLabels[field][value]) return valueLabels[field][value];
  return value || '-';
}}
function render() {{
  if (!rows.length) {{
    document.getElementById('referenceTable').innerHTML = '<div class="muted-box">아직 등록된 문서가 없습니다. 자료를 넣은 뒤 문서 추가로 직접 등록하거나, 자료 정리를 요청하세요.</div>';
    return;
  }}
  document.getElementById('referenceTable').innerHTML = rows.map((row, index) => {{
    const title = row.title || row.reference_id || '문서명 미입력';
    const pills = ['file_type','source_tier','visibility_ko','intake_status','parse_status','context_index_status'].map((field) => row[field] ? '<span class="pill">' + escapeHtml(labels[field] || field) + ': ' + escapeHtml(displayValue(row, field)) + '</span>' : '').join('');
    const allControls = visibleFields.map((field) => control(row, index, field)).join('');
    return '<section class="list-card"><div class="list-card-head"><div><div class="list-card-title">' + escapeHtml(title) + '</div><div class="pill-row">' + pills + '</div></div><div class="btn-row"><button class="secondary" type="button" onclick="toggleDetails(\\'ref-extra-' + index + '\\')">세부 정보</button><button class="danger" type="button" onclick="removeReference(' + index + ')">삭제</button></div></div><div id="ref-extra-' + index + '" class="detail-grid hidden">' + allControls + '</div></section>';
  }}).join('');
}}
function toggleDetails(id) {{ const el = document.getElementById(id); if (el) el.classList.toggle('hidden'); }}
function sync() {{
  document.querySelectorAll('input[data-index], select[data-index], textarea[data-index]').forEach((input) => {{
    rows[Number(input.dataset.index)][input.dataset.field] = input.value.trim();
  }});
}}
function addReference() {{ sync(); rows.push(emptyRow()); markDirty(); render(); }}
function removeReference(index) {{ sync(); rows.splice(index, 1); markDirty(); render(); }}
async function saveReferences() {{
  sync();
  const response = await fetch('/api/references', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{ rows }}) }});
  const data = await response.json();
  document.getElementById('status').textContent = response.ok ? '저장되었습니다. ' + data.saved_at_kst : '저장 실패: ' + (data.error || response.status);
  if (response.ok) {{ clearDirty(); showToast('문서 대장을 저장했습니다.', 'ok'); }} else {{ showToast('저장에 실패했습니다.', 'error'); }}
}}
async function scanMaterials() {{
  if (unsavedChanges && !confirm('저장되지 않은 변경 사항이 있습니다. 먼저 저장하지 않고 자료 폴더를 스캔할까요?')) return;
  const response = await fetch('/api/scan-materials', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{}}) }});
  const data = await response.json();
  if (!response.ok) {{
    showToast('자료 폴더 스캔에 실패했습니다.', 'error');
    document.getElementById('status').textContent = '스캔 실패: ' + (data.error || response.status);
    return;
  }}
  rows = data.rows || rows;
  render();
  clearDirty();
  const message = data.added ? '신규 자료 ' + data.added + '건을 문서 대장에 추가했습니다.' : '새로 추가할 자료가 없습니다.';
  document.getElementById('status').textContent = message;
  showToast(message, data.added ? 'ok' : 'warn');
}}
let normalizeTimer = null;
let normalizationUserStarted = false;
function setNormalizeRunning(running) {{
  const button = document.getElementById('normalizeButton');
  if (button) button.disabled = running;
}}
async function pollNormalization() {{
  try {{
    const response = await fetch('/api/reference-normalization-status', {{ cache:'no-store' }});
    const data = await response.json();
    setNormalizeRunning(Boolean(data.running));
    if (data.message) document.getElementById('status').textContent = data.message + (data.log_path ? ' 로그: ' + data.log_path : '');
    if (data.running) {{
      normalizeTimer = setTimeout(pollNormalization, 1200);
      return;
    }}
    if (normalizeTimer) clearTimeout(normalizeTimer);
    if (data.status === 'done') {{
      const refreshed = await fetch('/api/references', {{ cache:'no-store' }}).then((r) => r.json());
      rows = refreshed.rows || rows;
      render();
      clearDirty();
      if (normalizationUserStarted) showToast('파싱/정규화/색인 상태를 갱신했습니다.', 'ok');
      normalizationUserStarted = false;
    }} else if (data.status === 'partial') {{
      const refreshed = await fetch('/api/references', {{ cache:'no-store' }}).then((r) => r.json());
      rows = refreshed.rows || rows;
      render();
      clearDirty();
      if (normalizationUserStarted) showToast('파싱/정규화는 완료, 색인은 확인이 필요합니다.', 'warn');
      normalizationUserStarted = false;
    }} else if (data.status === 'failed') {{
      if (normalizationUserStarted) showToast('파싱/정규화/색인 실행에 실패했습니다.', 'error');
      normalizationUserStarted = false;
    }}
  }} catch (error) {{
    setNormalizeRunning(false);
    showToast('파싱/정규화/색인 상태를 확인하지 못했습니다.', 'error');
  }}
}}
async function startNormalization() {{
  if (unsavedChanges && !confirm('저장되지 않은 변경 사항이 있습니다. 먼저 저장하지 않고 파싱/정규화/색인을 실행할까요?')) return;
  normalizationUserStarted = true;
  setNormalizeRunning(true);
  document.getElementById('status').textContent = '파싱/정규화/색인을 시작합니다.';
  const response = await fetch('/api/reference-normalization', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{}}) }});
  const data = await response.json();
  if (!response.ok) {{
    setNormalizeRunning(false);
    document.getElementById('status').textContent = '실행 실패: ' + (data.error || response.status);
    showToast('파싱/정규화/색인 실행에 실패했습니다.', 'error');
    return;
  }}
  showToast(data.message || '파싱/정규화/색인을 실행 중입니다.', 'ok');
  pollNormalization();
}}
pollNormalization();
document.addEventListener('input', (event) => {{ if (event.target.matches('input,select,textarea')) markDirty(); }});
render();
</script>
"""
    return layout("문서 대장", body, nav, "references")


def changes_page(store: DashboardStore) -> str:
    rows_json = json.dumps(store.changes(limit=500), ensure_ascii=False)
    nav = """<h1>수정 이력</h1>
<p class="lead">대시보드에서 직접 저장한 프로젝트 정보, 산출물 관리, 문서 대장 변경만 표시합니다.</p>"""
    body = f"""
<section class="panel">
  <div class="grid">
    <label>화면 필터
      <select id="scopeFilter" onchange="renderChanges()">
        <option value="">전체</option>
        <option value="project_profile">프로젝트 정보</option>
        <option value="report_registry">산출물 관리</option>
        <option value="reference_inventory">문서 대장</option>
      </select>
    </label>
  </div>
  <div class="compact-list" id="changesTable"></div>
</section>
<script id="changeRows" type="application/json">{rows_json}</script>
<script>
const rows = JSON.parse(document.getElementById('changeRows').textContent);
const labels = {{ changed_at_kst:'저장 시각', scope:'화면', target_file:'저장 위치', summary:'변경 요약', pc_name:'PC 이름', anonymous_device_id:'기기 식별값', before_hash:'변경 전 기록', after_hash:'변경 후 기록', app_version:'앱 버전' }};
const scopeLabels = {{ project_profile:'프로젝트 정보', report_registry:'산출물 관리', reference_inventory:'문서 대장' }};
const primaryFields = ['changed_at_kst','scope','summary','pc_name'];
const detailFields = ['target_file','anonymous_device_id','before_hash','after_hash','app_version'];
function escapeHtml(value) {{ return String(value || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }}
function valueFor(row, field) {{ return field === 'scope' ? (scopeLabels[row[field]] || row[field]) : row[field]; }}
function renderChanges() {{
  const scope = document.getElementById('scopeFilter').value;
  const filtered = scope ? rows.filter((row) => row.scope === scope) : rows;
  if (!filtered.length) {{
    document.getElementById('changesTable').innerHTML = '<p class="small">표시할 수정 이력이 없습니다.</p>';
    return;
  }}
  document.getElementById('changesTable').innerHTML = filtered.map((row) => {{
    const summary = primaryFields.map((field) => '<div class="summary-card"><span class="small">' + labels[field] + '</span><strong>' + escapeHtml(valueFor(row, field)) + '</strong></div>').join('');
    const details = detailFields.map((field) => '<div><span class="small">' + labels[field] + '</span><br><code>' + escapeHtml(row[field]) + '</code></div>').join('');
    return '<section class="compact-item"><div class="summary-row">' + summary + '</div><details class="advanced"><summary>상세 기록 보기</summary><div class="detail-grid">' + details + '</div></details></section>';
  }}).join('');
}}
renderChanges();
</script>
"""
    return layout("수정 이력", body, nav, "changes")


class Handler(BaseHTTPRequestHandler):
    store: DashboardStore
    session: SessionState

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str = "text/plain; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html_text: str) -> None:
        self._send(200, html_text.encode("utf-8"), "text/html; charset=utf-8")

    def _json(self, status: int, payload: object) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _payload(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _runtime_file(self, relative: str, content_type: str) -> bool:
        target = (self.store.workspace_dir / "_ai_system" / "runtime" / relative).resolve()
        runtime_root = (self.store.workspace_dir / "_ai_system" / "runtime").resolve()
        try:
            target.relative_to(runtime_root)
        except ValueError:
            return False
        if not target.exists() or not target.is_file():
            return False
        self._send(200, target.read_bytes(), content_type)
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/assets/fonts/pretendard.css":
                if self._runtime_file("fonts/pretendard/pretendard.css", "text/css; charset=utf-8"):
                    return
                css = "body{font-family:Pretendard,'Malgun Gothic','Noto Sans KR',Arial,sans-serif;}"
                self._send(200, css.encode("utf-8"), "text/css; charset=utf-8")
                return
            if parsed.path.startswith("/assets/fonts/pretendard/"):
                rel = "fonts/pretendard/" + parsed.path.rsplit("/", 1)[-1]
                if self._runtime_file(rel, "font/woff2"):
                    return
                self._json(404, {"error": "font_not_found"})
                return
            if parsed.path in {"/", "/dashboard"}:
                self.session.touch()
                self._html(dashboard_page(self.store))
                return
            if parsed.path == "/profile":
                self.session.touch()
                self._html(profile_page(self.store))
                return
            if parsed.path == "/reports":
                self.session.touch()
                self._html(reports_page(self.store))
                return
            if parsed.path == "/references":
                self.session.touch()
                self._html(references_page(self.store))
                return
            if parsed.path == "/changes":
                self.session.touch()
                self._html(changes_page(self.store))
                return
            if parsed.path == "/api/profile":
                self.session.touch()
                self._json(200, self.store.profile())
                return
            if parsed.path == "/api/report-registry":
                self.session.touch()
                self._json(200, {"rows": self.store.report_registry(), "fields": REPORT_REGISTRY_FIELDS})
                return
            if parsed.path == "/api/references":
                self.session.touch()
                self._json(200, self.store.reference_inventory())
                return
            if parsed.path == "/api/changes":
                self.session.touch()
                self._json(200, {"rows": self.store.changes(limit=500), "fields": CHANGE_LOG_FIELDS})
                return
            if parsed.path == "/api/heartbeat":
                self._json(200, self.session.heartbeat())
                return
            if parsed.path == "/api/reference-normalization-status":
                self.session.touch()
                self._json(200, self.store.reference_normalization_status())
                return
            if parsed.path == "/favicon.ico":
                self._send(204, b"", "image/x-icon")
                return
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"error": str(exc)})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            data = self._payload()
            if parsed.path == "/api/activity":
                self.session.touch()
                self._json(200, {"ok": True})
                return
            if parsed.path == "/api/profile":
                self.session.touch()
                self._json(200, self.store.save_profile(data))
                return
            if parsed.path == "/api/report-registry":
                self.session.touch()
                self._json(200, self.store.save_report_registry(data.get("rows", [])))
                return
            if parsed.path == "/api/references":
                self.session.touch()
                self._json(200, self.store.save_reference_inventory(data.get("rows", [])))
                return
            if parsed.path == "/api/open-folder":
                self.session.touch()
                self._json(200, self.store.open_folder(str(data.get("key", ""))))
                return
            if parsed.path == "/api/open-report":
                self.session.touch()
                self._json(200, self.store.open_report_file(str(data.get("path", ""))))
                return
            if parsed.path == "/api/scan-materials":
                self.session.touch()
                self._json(200, self.store.scan_materials())
                return
            if parsed.path == "/api/reference-normalization":
                self.session.touch()
                self._json(200, self.store.start_reference_normalization())
                return
            if parsed.path == "/api/shutdown":
                self.session.begin_shutdown(str(data.get("reason", "user_requested")))
                self._json(200, {"ok": True, "shutting_down": True})
                return
        except Exception as exc:  # noqa: BLE001
            self._json(400, {"error": str(exc)})
            return
        self._json(404, {"error": "not_found"})


def find_port(preferred: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Project directory")
    parser.add_argument("--port", type=int, default=8895)
    parser.add_argument("--idle-timeout-seconds", type=int, default=1800)
    parser.add_argument("--shutdown-grace-seconds", type=int, default=8)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    if not (project_dir / "project_profile.json").exists():
        print(f"Missing project_profile.json under {project_dir}", file=sys.stderr)
        return 1

    port = find_port(args.port)
    store = DashboardStore(project_dir)
    session = SessionState(args.idle_timeout_seconds, args.shutdown_grace_seconds)
    Handler.store = store
    Handler.session = session
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    session.server = server
    threading.Thread(target=session.monitor_idle, daemon=True).start()

    url = f"http://127.0.0.1:{port}/"
    print(f"Project dashboard app running: {url}")
    print(f"Project: {project_dir}")

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

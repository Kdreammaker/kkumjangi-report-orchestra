from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{str(k or "").strip(): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def rel(path: Path, project: Path) -> str:
    return path.relative_to(project).as_posix()


def source_id_from_record(path: Path, text: str) -> str:
    match = re.search(r"\bsource_id\b\s*:\s*`?([^`\n]+)`?", text)
    return match.group(1).strip() if match else path.stem


def create_table(conn: object, name: str, columns: list[str]) -> None:
    cols = ", ".join(f"{col} varchar" for col in columns)
    conn.execute(f"create or replace table {name} ({cols})")


def insert_rows(conn: object, name: str, columns: list[str], rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    placeholders = ", ".join(["?"] * len(columns))
    conn.executemany(
        f"insert into {name} values ({placeholders})",
        [[row.get(col, "") for col in columns] for row in rows],
    )


def update_inventory_index_status(project: Path, unit_counts: dict[str, int]) -> None:
    inventory_path = project / "references" / "reference_inventory.csv"
    rows = read_csv_rows(inventory_path)
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    for required in ["context_index_status", "context_unit_count"]:
        if required not in fieldnames:
            fieldnames.append(required)
    for row in rows:
        ref_id = row.get("reference_id", "")
        if ref_id in unit_counts:
            row["context_index_status"] = "indexed"
            row["context_unit_count"] = str(unit_counts[ref_id])
        elif row.get("normalized_status") == "normalized":
            row["context_index_status"] = row.get("context_index_status") or "not_indexed"
    with inventory_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build(project_name: str) -> dict[str, object]:
    import duckdb  # type: ignore[import-not-found]

    project = PROJECT_ROOT / project_name
    if not project.exists():
        return {"ok": False, "error": f"project not found: {project_name}"}

    db_path = project / "project_state" / "context_index.duckdb"
    manifest_path = project / "project_state" / "context_index_manifest.json"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))

    inventory_rows = read_csv_rows(project / "references" / "reference_inventory.csv")
    inventory_columns = sorted({key for row in inventory_rows for key in row.keys()}) or ["reference_id"]
    create_table(conn, "reference_inventory", inventory_columns)
    insert_rows(conn, "reference_inventory", inventory_columns, inventory_rows)

    unit_rows: list[dict[str, str]] = []
    for unit_csv in sorted((project / "references" / "normalized").glob("*/units.csv")):
        for row in read_csv_rows(unit_csv):
            row["unit_path"] = rel(unit_csv, project)
            unit_rows.append(row)
    unit_columns = ["reference_id", "unit_type", "unit_no", "heading", "text", "token_estimate", "unit_path"]
    create_table(conn, "document_units", unit_columns)
    insert_rows(conn, "document_units", unit_columns, unit_rows)

    source_rows = []
    for path in sorted((project / "references" / "source_records").glob("*.md")):
        text = read_text(path)
        source_rows.append({"source_id": source_id_from_record(path, text), "path": rel(path, project), "text": text})
    create_table(conn, "source_records", ["source_id", "path", "text"])
    insert_rows(conn, "source_records", ["source_id", "path", "text"], source_rows)

    workpack_rows = []
    for path in sorted((project / "reports" / "chapter_workpacks").glob("*.md")):
        workpack_rows.append({"chapter_id": path.stem.replace("_workpack", ""), "path": rel(path, project), "text": read_text(path)})
    create_table(conn, "chapter_workpacks", ["chapter_id", "path", "text"])
    insert_rows(conn, "chapter_workpacks", ["chapter_id", "path", "text"], workpack_rows)

    claim_text = read_text(project / "reports" / "report_claim_register.md")
    create_table(conn, "claim_register", ["path", "text"])
    insert_rows(conn, "claim_register", ["path", "text"], [{"path": "reports/report_claim_register.md", "text": claim_text}] if claim_text else [])

    unit_counts: dict[str, int] = {}
    for row in unit_rows:
        unit_counts[row.get("reference_id", "")] = unit_counts.get(row.get("reference_id", ""), 0) + 1
    update_inventory_index_status(project, unit_counts)

    manifest = {
        "ok": True,
        "project": project_name,
        "created_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
        "db_path": rel(db_path, project),
        "tables": {
            "reference_inventory": len(inventory_rows),
            "document_units": len(unit_rows),
            "source_records": len(source_rows),
            "chapter_workpacks": len(workpack_rows),
            "claim_register": 1 if claim_text else 0,
        },
        "privacy_boundary": "local_only_duckdb_file_no_external_upload",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    conn.close()
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local DuckDB context index for one project.")
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    payload = build(args.project)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

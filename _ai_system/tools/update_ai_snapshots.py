from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime
from pathlib import Path


MANIFEST = Path("_ai_system") / "project_state" / "latest_ai_snapshot_manifest.csv"
SNAPSHOT_ROOT = Path("_ai_system") / "project_state" / "latest_ai_snapshot"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def normalize(path: str) -> str:
    return path.replace("/", "\\")


def read_manifest() -> tuple[list[str], list[dict[str, str]]]:
    if not MANIFEST.exists():
        return ["relative_path", "sha256", "snapshot_path", "updated_at_kst", "file_size_bytes"], []
    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def main() -> int:
    parser = argparse.ArgumentParser(description="Update latest AI snapshots for explicit workspace-relative files.")
    parser.add_argument("paths", nargs="*", help="Workspace-relative files updated by the AI.")
    parser.add_argument(
        "--prune-missing",
        action="store_true",
        help="Remove manifest rows whose active file no longer exists after an intentional archive/reset move.",
    )
    args = parser.parse_args()

    fieldnames, rows = read_manifest()
    for required in ["relative_path", "sha256", "snapshot_path", "updated_at_kst", "file_size_bytes"]:
        if required not in fieldnames:
            fieldnames.append(required)

    by_rel = {normalize(row.get("relative_path", "")): row for row in rows if row.get("relative_path")}
    now = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    updated: list[str] = []

    if args.prune_missing:
        before = len(rows)
        rows = [
            row
            for row in rows
            if not row.get("relative_path") or Path(row.get("relative_path", "")).exists()
        ]
        by_rel = {normalize(row.get("relative_path", "")): row for row in rows if row.get("relative_path")}
        print(f"pruned_missing_rows={before - len(rows)}")

    for raw in args.paths:
        active = Path(raw)
        if not active.exists() or not active.is_file():
            print(f"skip missing file: {raw}")
            continue
        rel = normalize(active.as_posix())
        row = by_rel.get(rel)
        if row is None:
            snapshot_path = (SNAPSHOT_ROOT / active).as_posix()
            row = {
                "relative_path": rel,
                "sha256": "",
                "snapshot_path": snapshot_path,
                "updated_at_kst": "",
                "file_size_bytes": "",
            }
            rows.append(row)
            by_rel[rel] = row
        snapshot = Path(row.get("snapshot_path") or (SNAPSHOT_ROOT / active).as_posix())
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(active.read_bytes())
        row["sha256"] = sha256(active)
        row["snapshot_path"] = snapshot.as_posix()
        row["updated_at_kst"] = now
        row["file_size_bytes"] = str(active.stat().st_size)
        updated.append(rel)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"updated_snapshots={len(updated)}")
    for item in updated:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

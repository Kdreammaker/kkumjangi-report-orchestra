from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path("00_사용자_작업공간")


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the local DuckDB context index for one project.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    import duckdb  # type: ignore[import-not-found]

    project = PROJECT_ROOT / args.project
    db_path = project / "project_state" / "context_index.duckdb"
    if not db_path.exists():
        print(json.dumps({"ok": False, "error": "context_index_not_found", "db_path": db_path.as_posix()}, ensure_ascii=False, indent=2))
        return 1

    like = f"%{args.query.lower()}%"
    conn = duckdb.connect(str(db_path), read_only=True)
    rows = conn.execute(
        """
        select reference_id, unit_type, unit_no, heading, token_estimate, unit_path,
               substr(text, 1, 1200) as text_preview
        from document_units
        where lower(coalesce(text, '')) like ? or lower(coalesce(heading, '')) like ?
        order by try_cast(nullif(token_estimate, '') as integer) asc nulls last
        limit ?
        """,
        [like, like, args.limit],
    ).fetchall()
    columns = [desc[0] for desc in conn.description]
    conn.close()
    print(json.dumps({"ok": True, "results": [dict(zip(columns, row)) for row in rows]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

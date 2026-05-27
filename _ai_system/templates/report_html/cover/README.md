# Reusable Cover Component

Substantial reports should use this cover component instead of recreating cover markup from scratch.

Files:

- `cover.html`: reusable HTML component with placeholders.
- `cover.css`: reusable cover styling.
- `cover.schema.json`: expected data shape.
- `cover.example.json`: default example data.
- `samples/`: copy-ready cover data examples. Prefer `samples/premium_internal_review.json` for executive/internal-review reports.

Use:

1. Copy one sample JSON into a project as `reports/cover.data.json`.
2. Change only values, not the cover HTML structure.
3. Run `python _ai_system/tools/validate_cover_render.py --project <project> --write-preview`.
4. Assemble with `python _ai_system/tools/assemble_report.py --project <project>`.

The cover preview validates visible document-control fields such as classification, report number, date, and approval cells. It does not validate report body quality or source truth.

Design note:

- The cover should read as a serious report cover, not a generic title header.
- Keep the classification badge, report type, strong title hierarchy, metadata table, approval cells, and purpose note.
- Do not recreate cover markup for each project; choose a sample JSON and change values only.

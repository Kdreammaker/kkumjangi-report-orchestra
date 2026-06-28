# Reusable Cover Component

Document artifacts should use this cover component family instead of recreating cover markup from scratch when a cover is needed. Substantial reports normally need it; short artifacts may use a lighter title/header block when the selected preset says a full cover would be excessive.

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

Cover module selection:

- Choose the cover by artifact purpose, not by project default.
- Use only the modules the artifact needs: classification badge, report type, title/subtitle, metadata table, approval cells, purpose note, confidentiality tag, confidentiality notice, contact/release status, or version marker.
- Education handouts, product manuals, press releases, and short briefs often need fewer management fields than substantial internal reports.
- Partner proposals and investor/public documents need stricter distribution, approval, and contact/release status handling.
- If `confidentiality_status` is `대외비 아님` or `not_confidential`, do not render the red confidential tag or confidentiality warning. If the artifact is confidential, render both.

Design note:

- The cover should read as a serious report cover, not a generic title header.
- Keep the classification badge, report type, strong title hierarchy, metadata table, approval cells, and purpose note.
- Keep document classification and confidentiality separate. `classification` should be a document class such as `내부 검토용` or `파트너사 공유용`; confidentiality belongs in `confidentiality_status`, `security_tag`, and `confidential_notice`.
- Do not use the cover as a dumping ground for every project-management field. Keep the title/subtitle concise, put long context in the purpose note or body, and select approval cells only when the preset audience needs them.
- The cover CSS should stay conversion-friendly: no viewport-height spacer, no decorative blank hero area, and no manually rebuilt one-off cover markup.
- Do not recreate cover markup for each project; choose a sample JSON and change values only.

# Report HTML Template

Use this folder when creating substantial HTML reports.

The goal is to make the visual format reproducible across projects and compatible with later DOCX/PDF conversion.

## Files

- `report.css`: reusable report style tokens and component classes.
- `report_template.html`: semantic HTML skeleton for reports.
- `design_reference.html`: visual reference showing conversion-friendly premium report patterns.
- `cover/cover.html`: reusable cover-page component extracted from the stronger legacy cover pattern.
- `cover/cover.css`: cover-page layout and print styling.
- `cover/cover.schema.json`: required cover data fields.
- `cover/cover.example.json`: example values for the cover component.
- `../../chapter_workpack_template.md`: chapter writing brief template.
- `../../chapter_fragment_template.html`: chapter fragment starter.
- `../../visual_plan_template.csv`: role-based visual plan starter.
- `../../export_checklist_template.md`: DOCX/PDF export verification starter.

## Authoring Rules

- Keep report structure semantic: `header`, `section`, `h1`-`h3`, `p`, `table`, `figure`, `figcaption`, `ol`, `ul`, `aside`.
- Use numbered footnotes/endnotes for body citations.
- Use `자료:` and `근거 데이터:` in every material table/figure caption.
- Use `Source:`, `Underlying data:`, `Data basis:`, and `Accessed YYYY-MM-DD` only when the report is explicitly marked as English or mixed-language output, such as `<html lang="en">` or an output-language marker.
- Keep reader-facing references as a separate `참고자료` section, not as a numbered appendix. Tracking-only fields such as access date, use level, source_id, capture path, and user-material processing state belong in registers, not in the reader-facing report.
- Use static SVG/PNG or semantic table visuals in final report HTML. ECharts may be used as a local rendering helper, but the assembled report should not require JavaScript to show material charts.
- If a chart's CSV/XLSX changes, regenerate the static SVG/PNG chart artifact before reassembly.
- Avoid making material evidence depend only on complex CSS effects.
- Put report-specific styles in small scoped overrides only. Large one-off `<style>` blocks reduce reproducibility score.
- Do not use global `word-break: break-all` or page-wide `overflow-wrap: anywhere`. Korean body prose should keep normal word flow; apply long-token wrapping only to scoped elements such as URLs, local path labels, code snippets, and dense table cells.
- For long URLs, file paths, identifiers, and code-like strings, use scoped classes such as `.url`, `.path`, `.code`, `.long-token`, or `.long-text`, or rely on `a[href]`, `code`, `pre`, `th`, and `td` defaults in `report.css`.
- DOCX/PDF readiness must not mean plain or low-design output. Keep the HTML polished, but use semantic headings, tables, figures, captions, and static/conversion-friendly visuals.
- Keep callouts, tables, figures, and captions semantic: callouts should use `aside`, tables should use `table` with `caption`/`thead`/`tbody` where useful, and visual material should use `figure` plus `figcaption` instead of generic layout boxes.
- Final reports should include Chapter 0 / 제0장 요약, written last.
- Each material table and each material graph/figure/chart needs a corresponding CSV/XLSX under the project `data_sources/` folder unless it is a qualitative process diagram backed by a source record.
- Substantial reports should keep chapter prose in `reports/chapters/ch*.html` fragments and use `_ai_system/tools/assemble_report.py` to concatenate cover + chapters into the final `reports/internal_review_report.html`.
- The assembler must not rewrite chapter prose. Edit the relevant chapter fragment, then reassemble.
- Create `reports/chapter_workpacks/ch*_workpack.md` before writing matching chapter fragments. The workpack should define the chapter question, decision use, paragraph plan, evidence, claim rows, counterarguments, visuals, forbidden overclaims, and completion checklist.
- Use `reports/cover.data.json` to populate the cover component instead of asking an AI to recreate cover markup from scratch.
- If a visual is planned in `data_sources/visual_plan.csv`, the final report should implement that visual with a matching caption and data/source reference.
- Treat chapter completeness and decision usefulness as the depth signal. Do not add volume only to satisfy a numeric length target.
- If DOCX/PDF is requested, store verification notes or render evidence under `reports/export_checks/` before calling the export delivery-ready.

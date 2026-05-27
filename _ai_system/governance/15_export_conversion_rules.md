# Export Conversion Rules

## Purpose

HTML is the working report format. DOCX and PDF are export artifacts.

Use this rule when the user asks for DOCX/PDF, when a report is intended for delivery, or when a report claims conversion readiness.

## Core Rule

File creation is not proof of export quality.

A `.docx` or `.pdf` may be described as:

- `created_unverified` when the file exists but has not been opened/rendered,
- `structure_checked` when package structure or PDF pages were inspected,
- `render_verified` when visual output was opened or rendered and checked,
- `delivery_candidate` only after the report source gates and export checks pass.

## Export Sequence

For DOCX/PDF export:

1. Validate assembled HTML.
2. Confirm semantic headings, tables, figures, captions, footnotes, and appendices.
3. Convert to DOCX/PDF using the chosen tool.
4. Check the file can be opened or parsed.
5. Check structure:
   - heading hierarchy,
   - tables,
   - figures/media,
   - footnotes/endnotes or reference section,
   - page breaks where relevant.
6. Render or visually inspect representative pages.
7. Record the result under `reports/export_checks/`.

## DOCX Readiness

DOCX readiness should preserve design quality. Do not flatten a premium HTML report into a plain text document only to make conversion easier.

Prefer:

- semantic HTML,
- static charts/figures,
- plain-text captions,
- conversion-friendly tables,
- reusable cover component,
- local CSS with print rules.

Avoid:

- remote fonts,
- interactive charts as the only material visual,
- CSS-only evidence graphics,
- absolute local paths in reader-facing text.

## Export Check Evidence

Export checks may include:

- `reports/export_checks/docx_structure_check.json`,
- `reports/export_checks/pdf_render_check.json`,
- rendered page images,
- notes explaining known conversion limitations.

If these artifacts are absent, say the export is unverified.


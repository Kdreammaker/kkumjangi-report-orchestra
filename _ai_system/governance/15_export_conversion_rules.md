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

Readiness is not native Word automation support. Presets, design guidance, or validation notes may require conversion-friendly structure, but they must not be read as proof that advanced Word field, numbering, section, or chart-editing features are implemented.

Prefer:

- semantic HTML,
- static charts/figures,
- plain-text captions,
- conversion-friendly tables,
- reusable cover component,
- local CSS with print rules.
- report-width and margin tokens shared by cover and body,
- stable heading hierarchy (`h1`, `h2`, `h3`) that matches the PRD/design file,
- cover metadata modules that avoid duplicate document classification/confidentiality labels.

Avoid:

- remote fonts,
- interactive charts as the only material visual,
- CSS-only evidence graphics,
- absolute local paths in reader-facing text.
- viewport-height cover sizing that consumes a second margin layer during DOCX/PDF conversion,
- background-heavy cover effects that become large images or unstable blocks in word processors.

## Current Export Support

Currently supported export claims are limited to:

- DOCX/PDF file creation through the chosen conversion tool,
- DOCX package or PDF page structure checks,
- checks for headings, tables, figures/media, captions, references, and page breaks where relevant,
- export evidence records under `reports/export_checks/`,
- rendered or visually inspected sample pages when available.

These checks can support `structure_checked`, `render_verified`, or `delivery_candidate` status only under the evidence rules above. They do not prove Word-native automation.

## Unsupported Until PoC

Treat the following as unsupported unless a task adds a documented proof-of-concept, validator, and export evidence:

- Word field codes such as `PAGE` and `NUMPAGES`,
- automatic Word caption numbering with `SEQ Table` or `SEQ Figure` fields,
- Word landscape sections or mixed-orientation section breaks,
- native editable Word chart creation, round-trip editing, or chart data binding.

If a report needs any of these, record it as `unsupported_poc_required` or a known export limitation instead of claiming DOCX support from presets alone.

## Export Check Evidence

Export checks may include:

- `reports/export_checks/docx_structure_check.json`,
- `reports/export_checks/pdf_render_check.json`,
- rendered page images,
- notes explaining known conversion limitations.

If these artifacts are absent, say the export is unverified.


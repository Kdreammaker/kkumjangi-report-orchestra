# Export Conversion Rules

## Purpose

HTML is the working report format. DOCX, PDF, and native HWPX are supported
export artifacts. The owned HWP/HWPX engine is embedded in every distribution,
so HWP-to-HWPX and native report HWPX export need no separate repository or
external engine CLI configuration. When a Report Orchestra document is created
from Report Factory cover/chapter sources, `export_report_hwpx.py` automatically
adapts it through `report_export_ir.v1` before entering the controlled
`hwpx-authoring-html.v1` contract. Only direct low-level conversion of arbitrary
external HTML remains unsupported.

Use this rule when the user asks for DOCX/PDF/HWPX/HWP, when a report is
intended for delivery, or when a report claims conversion readiness.

## Core Rule

File creation is not proof of export quality.

A `.docx` or `.pdf` may be described as:

- `created_unverified` when the file exists but has not been opened/rendered,
- `structure_checked` when package structure or PDF pages were inspected,
- `render_verified` when visual output was opened or rendered and checked,
- `delivery_candidate` only after the report source gates and export checks pass.

For HWPX/Hancom claims, use more specific language:

- `hwpx_compatible_html` when the source is authored for Hancom import/open
  compatibility but no native `.hwpx` file has been produced.
- `hwpx_created_unverified` when a `.hwpx` file exists but has not been opened
  in Hancom or another accepted renderer.
- `hwpx_open_checked` when representative pages were opened and visually
  inspected.
- `hwpx_delivery_candidate` only after source gates, HWPX open checks, and
  known limitation notes are recorded.

## Export Sequence

For DOCX/PDF export:

1. Validate assembled HTML.
2. Confirm semantic headings, tables, figures, captions, footnotes, and appendices.
3. For DOCX, prefer the native DOCX exporter when layout fidelity matters: `python _ai_system/tools/export_report_docx.py --project <project> --render-preview`. Use HTML import/conversion only as a separately verified fallback.
4. For PDF, convert from the chosen stable source and record the converter.
5. Check the file can be opened or parsed.
6. Check structure:
   - heading hierarchy,
   - tables,
   - figures/media,
   - footnotes/endnotes or reference section,
   - page breaks where relevant.
7. Render or visually inspect representative pages.
8. Record the result under `reports/export_checks/`.

For HWPX/Hancom-oriented output:

1. Record whether the target is native `.hwpx`, HWP-to-HWPX conversion, or
   HWPX-compatible HTML for Hancom import.
2. If the target is HWPX-compatible HTML, author the source inline-first with
   Hancom-friendly fonts, simple semantic structure, static images, semantic
   tables, white document background, and list-marker overrides recorded in
   `reports/report_design.md`.
3. For HWP-to-HWPX conversion, verify the owned engine with
   `python _ai_system/tools/convert_hwp_to_hwpx.py --probe`, preserve the source,
   and create the new HWPX through the embedded entrypoint.
4. For direct controlled-authoring-HTML conversion, verify
   `python _ai_system/tools/convert_html_hwpx.py --probe`, require the
   `hwpx-authoring-html.v1` contract, preserve the source, and create the new
   HWPX through the embedded entrypoint. This low-level command intentionally
   rejects arbitrary external web HTML and DOCX-compatible HTML.
5. For Report Factory sources, use `python _ai_system/tools/export_report_hwpx.py
   --project <project_name>`. This normalizes cover/chapter sources through
   `report_export_ir.v1` before the owned Document IR writer. This adaptation is
   automatic; users do not need to relabel or manually rewrite system-authored
   report sources into controlled authoring HTML.
6. Open-check representative pages in Hancom Viewer/Hancom Office when
   available and record the result under `reports/export_checks/`.

## DOCX/HWPX Readiness

DOCX/HWPX readiness should preserve design quality. Do not flatten a premium HTML report into a plain text document only to make conversion easier.

Readiness is not native Word automation support. Presets, design guidance, or validation notes may require conversion-friendly structure, but they must not be read as proof that advanced Word field, numbering, section, or chart-editing features are implemented.

Default report HTML should be authored inline-first for DOCX/Google Docs/HWPX compatibility. This means the report templates, cover renderer, chapter fragments, and report design file should put essential visual styling directly on reader-facing elements with `style=""` wherever practical. This is different from relying on a final post-processing step that converts CSS to inline styles after the report is already written.

Prefer:

- semantic HTML,
- static charts/figures,
- plain-text captions,
- conversion-friendly tables,
- reusable cover component,
- inline-styled headings, paragraphs, captions, tables, callouts, figures, cover badges, cover metadata, and approval blocks,
- local CSS as preview/print/fallback support,
- report-width and margin tokens shared by cover and body,
- stable heading hierarchy (`h1`, `h2`, `h3`) that matches the PRD/design file,
- cover metadata modules that avoid duplicate document classification/confidentiality labels.
- target-format font stacks recorded in the design file:
  - DOCX/Word: Malgun Gothic / 맑은 고딕 unless overridden,
  - HWPX/Hancom: 한컴바탕 or 함초롬바탕 for body, 한컴돋움 or 함초롬돋움 for dense lists/tables, with fallback fonts recorded,
- list marker contracts selected from `LIST_STYLE_PRESETS.md`; HWPX-specific Korean markers should be target overrides, not cross-target defaults.

Avoid:

- remote fonts,
- interactive charts as the only material visual,
- CSS-only evidence graphics,
- absolute local paths in reader-facing text,
- class-only or CSS-variable-only styling for material visual information,
- `nth-child` styling as the only way to distinguish table rows/cells,
- grid/flex-only layouts for cover metadata or approval blocks,
- `@font-face` as the only readable font path,
- inline-SVG-only charts for DOCX/Google Docs/Hancom import targets unless the actual import path has been render-verified,
- viewport-height cover sizing that consumes a second margin layer during DOCX/PDF conversion,
- background-heavy cover effects that become large images or unstable blocks in word processors.

CSS fallback may still carry `@page`, page-break helpers, print color adjustment, long-token handling, and browser preview defaults. These are compatibility aids. They do not prove Word, Google Docs, or Hancom import fidelity without export/render/open evidence. Keep default document/page backgrounds white; do not put browser-preview grey or decorative backgrounds on `body` in report-ready HTML because word processors can convert them into whole-document page shading.

For visual assets, prefer static PNG/JPG `<img>` outputs or simple table-based visuals for DOCX/Google Docs/Hancom import tests. Inline SVG may be kept for browser/PDF preview, but it should not be treated as delivery-ready for Word/Google Docs/Hancom unless the converted artifact has been rendered or opened and inspected.

## Current Export Support

Currently supported export claims are limited to:

- native DOCX file creation from report factory sources (`reports/cover.data.json`, `reports/chapters/ch*.html`, reference registers, and data artifacts) through `_ai_system/tools/export_report_docx.py`,
- native DOCX structure for Word styles, A4 page setup, cover metadata tables, approval blocks, running headers/footers, tables, static images, references, and data appendices,
- DOCX/PDF file creation through the chosen conversion tool,
- DOCX package or PDF page structure checks,
- checks for headings, tables, figures/media, captions, references, and page breaks where relevant,
- export evidence records under `reports/export_checks/`,
- rendered or visually inspected sample pages when available.
- HWPX-compatible HTML authoring guidance for Hancom-oriented import/open tests, when the target format, font fallback, list-marker fallback, and verification method are recorded.
- HWP-to-HWPX file creation through the embedded engine entrypoint `_ai_system/tools/convert_hwp_to_hwpx.py`.
- native HWPX creation from the controlled `hwpx-authoring-html.v1` contract through the embedded entrypoint `_ai_system/tools/convert_html_hwpx.py`.
- native HWPX creation from Report Factory cover/chapter sources through `_ai_system/tools/export_report_hwpx.py` and `report_export_ir.v1`, with package validation and semantic round-trip evidence.
- HWPX-to-controlled-HTML semantic round-trip for adaptation workflows; browser preview visual parity is not implied.

These checks can support `structure_checked`, `render_verified`, `delivery_candidate`, `hwpx_compatible_html`, or `hwpx_open_checked` status only under the evidence rules above. The native DOCX exporter improves Word layout control, but it still requires render/visual review before delivery claims. HWPX-compatible HTML improves Hancom import intent, but it is not a native HWPX export claim.

## Unsupported Until PoC

Treat the following as unsupported unless a task adds a documented proof-of-concept, validator, and export evidence:

- Word field codes such as `PAGE` and `NUMPAGES`,
- automatic Word caption numbering with `SEQ Table` or `SEQ Figure` fields,
- Word landscape sections or mixed-orientation section breaks,
- native editable Word chart creation, round-trip editing, or chart data binding.
- direct native `.hwpx` export from arbitrary assembled report HTML that bypasses `report_export_ir.v1`,
- HWP to HWPX conversion when the embedded owned engine is missing or fails its probe,
- direct low-level conversion of arbitrary external web HTML to native HWPX,
- HWPX to HTML browser-preview visual parity,
- automated HWPX screenshot or visual diff gates without a renderer automation path.

If a report needs any of these, record it as `unsupported_poc_required` or a known export limitation instead of claiming DOCX/HWPX support from presets alone.

## Export Check Evidence

Export checks may include:

- `reports/export_checks/docx_structure_check.json`,
- `reports/export_checks/pdf_render_check.json`,
- rendered page images,
- notes explaining known conversion limitations.

If these artifacts are absent, say the export is unverified.


# Report Design Template

Use this file as `reports/report_design.md` for substantial reports.

## Visual Scope

- Report title:
- PRD path:
- Working output: HTML first, DOCX/PDF conversion-ready if needed
- Target document format: HTML / DOCX / HWPX-compatible HTML / PDF / mixed

## Authoring Structure

- Authoring structure profile: decision_first / proposal / review_opinion / meeting_minutes / education / manual / public_release / custom
- Default paragraph mode: bullet_first / prose_first / mixed
- Conclusion-first rule:
- Bullet-first slots: findings, options, scope, conditions, risks, roles, schedule, decisions, action items
- Prose-only or prose-preferred slots: background, rationale, legal/regulatory context, learning explanation, press lead, quotation, narrative summary
- Slot exceptions:
- Source restructuring allowed: yes / no / conditional

## Page and Layout

- Page basis: A4
- Page margin: HTML screen width should stay DOCX/PDF-friendly, not full browser width
- Cover margin: use cover preset/modules; avoid excessive top whitespace for long Korean titles
- Body max width: keep main text, tables, figures, and captions within the conversion-safe content width
- Shared content width: cover and body should use the same conversion-safe width/margin tokens unless a preset explicitly documents a reason
- Print rule: use A4 print CSS as a compatibility aid, but verify exported DOCX/PDF separately
- Avoid: viewport-height covers, double margin layers, and background-heavy cover effects that become unstable in DOCX/PDF conversion
- Long text wrapping: do not use global `word-break: break-all`; scope `overflow-wrap`/long-token handling to URLs, local path labels, identifiers, code snippets, and table cells only

## Inline-first DOCX/Google Docs/HWPX Compatibility

- Default authoring mode: inline-first HTML. Unless the user asks for a browser-only design, core visual information should be written directly on the element with `style=""` at the template/chapter/cover stage, not added only by a final CSS inlining pass.
- Priority elements for inline styles: cover badges, cover title/subtitle, cover meta table, approval block, `h1`-`h3`, paragraphs, callouts, material tables, `caption`, `figure`, `figcaption`, source/data notes, and appendix tables.
- Class usage: keep classes as semantic markers for validators, structure identification, preview fallback, and print helpers. Do not make class/CSS variables the only source of color, border, font, spacing, or caption styling for reader-facing content.
- CSS variable dependency: record actual colors, font stacks, border widths, spacing, and table styles as literal inline values where practical. CSS variables may remain in shared CSS as browser-preview fallback.
- Avoid for export-oriented reports: complex grid/flex as the only layout, `@font-face` as the only font path, `nth-child`-dependent table styling, CSS-only visuals, inline-SVG-only charts for DOCX/Google Docs/Hancom import, background-heavy effects, viewport-dependent sizing, and canvas/JavaScript-only charts.
- Page/background rule: keep the document/page background white by default. Browser preview backgrounds may not be placed on `body` because Word/Google Docs imports can turn them into whole-document page shading.
- Visual assets: for DOCX/Google Docs/Hancom import tests, prefer static PNG/JPG images referenced by `<img>` or simple table-based visuals. Inline SVG is acceptable as a browser/PDF aid only when export verification confirms it survives the target import path.
- Tables and approval blocks: prefer semantic tables with inline cell borders/backgrounds for conversion stability. Avoid relying on zebra striping or CSS-only header styling to carry meaning.
- Print/page rules: keep `@page`, page-break helpers, print color adjustment, and global fallback styles in CSS because they cannot be fully expressed inline. Treat these as compatibility aids, not proof of DOCX/Google Docs/HWPX fidelity.
- HWPX/Hancom rule: record whether the source is Hancom-import-oriented HTML, a Report Factory source, or the low-level `hwpx-authoring-html.v1` contract. Report Factory cover/chapter sources are automatically adapted through Report Export IR by the embedded exporter; only direct arbitrary external HTML requires explicit adaptation to the controlled contract. A created `.hwpx` is not a delivery-ready claim until an export/open check is recorded.
- Claim language: describe the output as "DOCX/Google Docs/HWPX compatibility-first" or "export-friendly pending verification"; do not claim full Word/Google Docs/Hancom compatibility until actual export/render/open checks are recorded.

## Typography

- Body font:
- Heading font:
- DOCX target font: Malgun Gothic / 맑은 고딕 unless overridden
- HWPX target font: 한컴바탕 or 함초롬바탕 for body; 한컴돋움 or 함초롬돋움 for dense lists/tables, with fallback recorded
- Body size:
- H1/H2/H3 sizes and weights:
- Line height:
- Heading hierarchy rule: H1 is report/chapter title, H2 is 대목차/major section, H3 is 중목차, H4 or bold lead-in is 소목차 only when needed

## Cover

- Cover preset: public_release / team_review / executive_decision / partner_proposal
- Cover modules: classification and confidentiality badges on the same top line / confidentiality notice / author / review-approval / recipient / logo
- Logo priority: report-specific override -> project brand_assets -> common CI -> blank
- Logo path:
- Logo placement:
- Long title handling: allow line wrapping; do not overlap metadata or approval blocks

## Classification Display

- Document classification comes from PRD:
- Confidentiality status comes from PRD:
- Do not duplicate classification and report type. Example: use `내부 검토용` plus `대외비 / Confidential` on the same top line and a non-redundant report type such as `전략 보고서`, not `내부 검토용` plus `내부 검토 보고서`.
- Confidentiality notice placement: cover only unless the user asks for all-page footer
- Confidentiality notice wording:

## Color and CI

- Primary color:
- Secondary color:
- Neutral colors:
- Accessibility notes:

## Tables, Charts, and Diagrams

- Table style:
- Chart style:
- Diagram style:
- Semantic HTML rule: callouts use `aside`, material tables use `table` with `caption`/`thead`/`tbody` where useful, and charts/diagrams/screenshots use `figure` plus `figcaption`
- Data file rule: every material table/chart needs CSV/XLSX or source-backed qualitative artifact
- Visual selection rule: decide whether each visual should remain a table, become a graph/chart, become a timeline/flow/diagram, move to appendix, or be retired
- Source display rule: use `주:` and `자료:` in Korean reader-facing captions
- Data display rule: reader-facing `근거 데이터:` names the dataset in Korean; raw `data_sources/...` paths belong in HTML comments, data indexes, or appendix artifact tables

## List Style Presets

- Default ordered list preset:
- Default unordered list preset:
- Available presets: `formal_outline` (`I -> A -> 1 -> a`), `guide_outline` (`A -> A) -> a) -> (a)`), `procedure_steps` (`1 -> 1) -> a) -> (a)`), `administrative_outline` (`1. -> 1) -> A. -> a)` with HWPX marker overrides), `symbol_bullets` (`• -> ◦ -> ▪ -> -`)
- Selection rule: choose the preset during PRD/design when nested hierarchy matters; record user-requested exceptions here
- HTML rule: put `data-list-preset="<preset_id>"` on the root list and include conversion-relevant spacing/type intent inline where practical
- Export rule: native DOCX export should use the selected list preset for multi-level numbering; Word/Google Docs/Hancom import still requires verification
- HWPX marker rule: if Hancom-style Korean markers such as `가.` or `가)` are needed, record them as HWPX target overrides and verify in Hancom; do not make them the cross-target default for DOCX/Google Docs.
- Avoid: CSS-counter-only numbering, decorative custom bullets as the only hierarchy marker, and Korean alphabetic sequence markers as the cross-target default

## Export PoC Backlog

- Word field code automation:
- SEQ caption automation:
- Landscape section automation:
- Native HWPX export:
- HWP to HWPX conversion:
- HTML/HWPX visual round-trip:
- Notes: keep these out of normal report production until separately implemented and verified

## Revision Log

| Date/KST | Version | Change | Reason |
|---|---|---|---|

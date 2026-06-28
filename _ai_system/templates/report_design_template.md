# Report Design Template

Use this file as `reports/report_design.md` for substantial reports.

## Visual Scope

- Report title:
- PRD path:
- Working output: HTML first, DOCX/PDF conversion-ready if needed

## Page and Layout

- Page basis: A4
- Page margin: HTML screen width should stay DOCX/PDF-friendly, not full browser width
- Cover margin: use cover preset/modules; avoid excessive top whitespace for long Korean titles
- Body max width: keep main text, tables, figures, and captions within the conversion-safe content width
- Shared content width: cover and body should use the same conversion-safe width/margin tokens unless a preset explicitly documents a reason
- Print rule: use A4 print CSS as a compatibility aid, but verify exported DOCX/PDF separately
- Avoid: viewport-height covers, double margin layers, and background-heavy cover effects that become unstable in DOCX/PDF conversion
- Long text wrapping: do not use global `word-break: break-all`; scope `overflow-wrap`/long-token handling to URLs, local path labels, identifiers, code snippets, and table cells only

## Typography

- Body font:
- Heading font:
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

## Export PoC Backlog

- Word field code automation:
- SEQ caption automation:
- Landscape section automation:
- Notes: keep these out of normal report production until separately implemented and verified

## Revision Log

| Date/KST | Version | Change | Reason |
|---|---|---|---|

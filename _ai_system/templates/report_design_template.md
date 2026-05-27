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
- Print rule: use A4 print CSS as a compatibility aid, but verify exported DOCX/PDF separately

## Typography

- Body font:
- Heading font:
- Body size:
- H1/H2/H3 sizes:
- Line height:

## Cover

- Cover preset: public_release / team_review / executive_decision / partner_proposal
- Cover modules: classification badge / confidentiality notice / author / review-approval / recipient / logo
- Logo priority: report-specific override -> project brand_assets -> common CI -> blank
- Logo path:
- Logo placement:
- Long title handling: allow line wrapping; do not overlap metadata or approval blocks

## Classification Display

- Document classification comes from PRD:
- Confidentiality status comes from PRD:
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
- Data file rule: every material table/chart needs CSV/XLSX or source-backed qualitative artifact
- Visual selection rule: decide whether each visual should remain a table, become a graph/chart, become a timeline/flow/diagram, move to appendix, or be retired
- Source display rule: use `주:` and `자료:` in Korean reader-facing captions
- Data display rule: reader-facing `근거 데이터:` names the dataset in Korean; raw `data_sources/...` paths belong in HTML comments, data indexes, or appendix artifact tables

## Revision Log

| Date/KST | Version | Change | Reason |
|---|---|---|---|

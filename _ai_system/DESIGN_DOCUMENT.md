# Report Design Document

## Purpose

This document defines the default writing, layout, and visualization standards for substantial Korean business reports in this workspace.

Design quality matters because it helps readers understand the argument. It must not become a substitute for strong evidence, clear reasoning, useful visuals, and honest residual-risk disclosure.

## Base References

Design references may be stored under:

`_ai_system/base_reference/`

Optional base references can include:

- official/public report samples,
- organization logos or brand guidelines,
- preferred cover samples,
- chart/table examples,
- document export examples.

If a workspace has client-specific or industry-specific design requirements, put them in a design system under `_ai_system/design_systems/` and bind the active defaults in `_ai_system/workspace_config.json`.

## Report Language

- Final reports are written in Korean unless the user says otherwise.
- English source titles, company/product names, laws, and technical terms may appear in parentheses where needed.
- Foreign-language legal or product terms must keep original wording in source records and key appendices.
- Difficult legal, financial, technical, or foreign terms should be collected in a report appendix.

## Design Direction

The target tone is:

- executive-review friendly,
- evidence-heavy,
- conservative but modern,
- closer to a policy, strategy, investment, legal, or institutional report than a marketing page.

Design should combine:

- restrained typography,
- strong hierarchy,
- readable tables,
- source-transparent chart captions,
- enough visual structure to make decisions and risks easy to scan.

Avoid:

- promotional wording,
- overly decorative design,
- one-color saturation,
- unsupported infographics,
- chart elements without source data files,
- design choices that imply more certainty than the evidence supports.

## Typography Specification

Use these as document-generation defaults. If the final output format requires another tool, preserve the hierarchy.

| Element | Font | Size | Weight | Line spacing | Color |
|---|---|---:|---|---:|---|
| Cover title | Pretendard, Malgun Gothic fallback | 24pt | Bold | 1.15 | `#172033` or white on dark background |
| Cover subtitle | Pretendard, Malgun Gothic fallback | 13pt | Regular | 1.35 | `#4B5565` |
| Report title H1 | Pretendard, Malgun Gothic fallback | 20pt | Bold | 1.20 | `#172033` |
| Section H2 | Pretendard, Malgun Gothic fallback | 16pt | Bold | 1.25 | `#1F4E79` |
| Subsection H3 | Pretendard, Malgun Gothic fallback | 13pt | Bold | 1.35 | `#172033` |
| Small heading H4 | Pretendard, Malgun Gothic fallback | 11pt | Bold | 1.45 | `#1F4E79` |
| Body | Pretendard, Malgun Gothic fallback | 11pt | Regular | 1.60 | `#172033` |
| Footnote/source | Pretendard, Malgun Gothic fallback | 9pt | Regular | 1.35 | `#667085` |
| Table body | Pretendard, Malgun Gothic fallback | 9.5pt | Regular | 1.30 | `#172033` |
| Table header | Pretendard, Malgun Gothic fallback | 9.5pt | Bold | 1.25 | white or `#172033` |

## Color Palette

Use a restrained, report-neutral palette unless a project-specific design system overrides it.

| Role | Color | Usage |
|---|---|---|
| Primary accent | `#1F6FEB` | Main section accents, key chart series, route highlight |
| Dark ink | `#172033` | Titles, high-emphasis text |
| Sub accent | `#1F4E79` | Header bands, dividers, dark chart series |
| Soft surface | `#F6F8FB` | Section background, table fill |
| Border | `#D7DEE8` | Borders and gridlines |
| Muted text | `#667085` | Captions, source notes, secondary labels |
| Risk red | `#B42318` | High-risk flags only |
| Warning amber | `#9A5B00` | Medium-risk or caution |
| Positive green | `#15803D` | Confirmed positive status only |

## Writing Style

- Use plain Korean business prose.
- Keep claims direct and evidence-backed.
- Track confirmed facts, interpretations, estimates, assumptions, and unresolved issues in claim/evidence registers.
- Avoid absolute claims unless supported by strong primary evidence.
- Avoid marketing expressions such as "혁신적", "압도적", "세계 최초", or "완전한" unless the evidence directly supports them.
- Use a conclusion-first structure when helpful: main judgment first, then evidence, caveat, and implication.
- Keep sentences readable. Split overloaded sentences that mix legal classification, business implication, and unresolved risk.
- Use cautious modal expressions such as `가능성이 있다`, `검토할 필요가 있다`, and `추가 확인이 필요하다` when evidence is incomplete.
- Do not soften confirmed risks. If a risk is material, state it directly and then explain mitigation options.
- Avoid ambiguous subjects. Make clear whether the actor is a company, regulator, investor, customer, partner, platform, or internal team.

## Expression Calibration

Use the following as style examples, not substantive conclusions.

### Claim

Avoid:

> 이 제휴는 시장을 압도할 수 있다.

Use:

> 이 제휴는 기존 고객 접점과 신규 서비스 접근성을 결합한다는 점에서 고객 유입 가능성을 높일 수 있다. 다만 역할 분담이 판매, 중개, 투자권유, 수탁 중 어느 행위에 가까운지에 따라 필요한 인허가와 소비자보호 장치가 달라진다.

### Estimate

Avoid:

> 출시하면 거래량이 크게 늘어날 것이다.

Use:

> 거래량 효과는 대상 고객군, 접근 가능한 상품 수, 투자자 제한, 시장조성 조건, 수수료 구조에 따라 크게 달라질 가능성이 높다. 따라서 1차 보고서에서는 단일 수치보다 저·중·고 시나리오로 효과 범위를 제시한다.

### Interpretation

Avoid:

> 해외 사례가 있으므로 국내에서도 가능하다.

Use:

> 해외 사례는 구조 설계의 참고점이 될 수 있다. 그러나 발행 주체, 권리 구조, 공시 체계, 투자자 보호 장치, 관할 규제가 다르면 국내 적용 가능성을 별도로 검토해야 한다.

## Report Structure Rules

Substantial reports normally include:

- Chapter 0 final executive summary,
- business or policy question,
- current-state diagnosis,
- market or operating context,
- legal/regulatory or institutional context where relevant,
- benchmark cases,
- candidate structures or options,
- quantitative or qualitative impact analysis,
- risk map,
- implementation path,
- recommendation or decision memo,
- appendices.

Appendices may include:

- source index,
- issue matrix,
- benchmark case cards,
- data and assumptions,
- glossary,
- translation notes for key foreign sources.

## HTML-First Report Format

- Until a final delivery format is selected, write reports as `.html`.
- HTML must be structured as a printable report, not as an interactive web app.
- Use semantic sections and stable heading hierarchy so later DOCX/PDF conversion preserves structure.
- Avoid JavaScript-dependent content.
- Avoid remote web assets; use local images, local chart outputs, and local data references.
- Use print-aware CSS and A4-friendly layout constraints.
- Put chart/table source notes directly below the relevant figure/table.
- Keep the report readable if copied into a document editor.

## DOCX-Conversion Friendly Contract

The report does not need to look like an A4 paper sheet on screen, but its content width and margins should be chosen so later DOCX conversion does not unexpectedly crop tables, figures, or long headings.

- Use the reusable report CSS page tokens for width and margins instead of ad hoc full-viewport layouts.
- Keep material content inside the report content width. Wide tables should be split, summarized, or moved to an appendix.
- Use `h1`, `h2`, `h3`, and optional `h4` in the same hierarchy as the detailed TOC. Do not simulate headings with bold paragraphs.
- Use normal `ul`/`ol` lists for enumerated issues, options, and decision criteria.
- Final report charts should be static SVG/PNG or inline SVG generated from the project data files. ECharts may be used locally to render the chart, but the assembled report should not require JavaScript to display it.
- If a chart data file changes, regenerate the static chart artifact and rerun the visual review before assembly.
- Do not promise that DOCX charts will remain editable as native Word charts unless a separate export workflow has explicitly created them that way.

## Citation and Source Display

- Body text should use numbered footnotes/endnotes or another reader-facing citation style chosen in the PRD.
- Tables and figures should display `주:`, `자료:`, and `근거 데이터:` where relevant.
- `자료:` names original sources or publishers.
- `근거 데이터:` names the local dataset or auditable artifact used to reproduce the visual.
- Do not show internal source ids in visible prose unless the report itself is a methodology document.
- Preserve exact internal ids and local paths in comments, data indexes, or appendices.

## Table Design

- Use clear headers, modest row height, and visible borders.
- Split very wide tables or move detail to an appendix.
- Every material table must be backed by a source record, CSV/XLSX, or documented qualitative artifact.

## Chart and Figure Design

- Charts must answer a specific analytical question.
- Use diagrams, timelines, heatmaps, scenario charts, and decision matrices when they improve comprehension.
- Every quantitative chart needs a CSV/XLSX data file or a clearly preserved original dataset.
- Qualitative diagrams need source-record-backed artifacts or source references.
- Do not create decorative charts without analytical purpose.

## Page and Layout Guidance

Recommended for PDF/DOCX output:

- Page size: A4.
- Margins: 20-25 mm.
- Header: short report title and date/status when useful.
- Footer: page number and confidentiality marker when useful.
- Cover: report title, project name, date, confidentiality label, approval/review fields where relevant.

## Confidentiality Label

Use labels that match the actual status, such as:

`내부 검토용 / 대외비 / 초안`

Do not use:

- `정부 제출용`
- `확정안`
- `법률의견`

unless those statuses are actually approved.

## Current Design Status

Before calling a report formatted or delivery-ready, review:

- title hierarchy,
- table readability,
- chart source captions,
- cover completeness,
- color consistency,
- appendix completeness,
- DOCX/PDF conversion evidence if export was requested.

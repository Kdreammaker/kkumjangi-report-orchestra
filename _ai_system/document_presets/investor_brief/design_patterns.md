# Investor Brief Design Patterns

## Document Purpose And Reader

- Purpose: Provide a controlled document-style IR brief, investor factbook, or investor Q&A reference.
- Primary readers: existing shareholders, prospective investors, lenders, strategic investors, board members, or internal IR reviewers.
- The document should help readers verify facts, understand assumptions, and prepare questions. It must not become an IR deck or pitch deck.

## Recommended Document Structure

- Cover and document control: version, date, confidentiality, approval status, and intended sharing scope.
- Executive snapshot: company identity, investment context, key facts, and current ask or review purpose.
- KPI summary: concise table or trend block for revenue, users, margins, retention, pipeline, funding, or other approved metrics.
- Business and market fact table: business model, customer segment, product status, market context, competitive position, and source status.
- Financial or operating narrative: historical facts first, then assumptions and forward-looking views.
- Risk section: commercial, execution, governance, funding, legal, and data limitations.
- Investor Q&A section: likely diligence questions with evidence-backed answers and unresolved items.
- Appendix or source notes: source dates, approved data scope, and open diligence requests.

## Recommended Layout Blocks

- KPI summary strip or two-column KPI table with metric, period, value, source, and status.
- Fact table with fact, evidence/source, approval state, and caveat.
- Risk/Q&A section using paired question-answer blocks, not slide headlines.
- Small trend charts for KPIs when data periods are reliable.
- Callout boxes for assumptions, forward-looking statements, and approval limits.

## Design Application Priorities

- Use KPI strips or compact cards only for metrics that have an approved period, unit, source, and sharing status.
- Separate public-approved metrics from confidential or diligence-only metrics before placing them in the executive snapshot.
- Put fact tables near the opening summary when they clarify company, market, funding, customer, or governance basics.
- Place risk blocks before investor Q&A when the expected question depends on unresolved risk, approval, or data limits.
- Use investor Q&A blocks for diligence readiness, not for repeating promotional claims.
- Split wide KPI, financial, or cap-table material into a short body summary and appendix detail when the table would dominate the page.

## Tables, Figures, And Captions

- KPI trend charts need period, unit, data 기준일, and source note.
- Fact tables should stay narrow: split company facts, market facts, and financial facts when the table grows wide.
- Captions should state what the chart/table proves and what it does not prove.
- Use static charts and images with alternative descriptions for exportable documents.

## AI Judgment Needed

- Decide whether each metric is approved for public sharing, controlled investor review, confidential diligence, or exclusion.
- Decide whether a cap table, KPI grid, or funding history belongs in the body, appendix, or a separate diligence package.
- Decide whether risks should be grouped by commercial, execution, governance, funding, legal, or data limitation categories.
- Decide whether a chart helps interpretation or whether a short fact table is safer and clearer.

## Deferred Export-Native Features

- Do not claim automatic landscape sections for cap tables, KPI grids, or appendix tables.
- Do not claim Word-native field codes, automatic page fields, generated DOCX captions, or native table-of-contents support.
- Treat landscape layout, native caption numbering, and investor-package automation as separate export-native work outside this module.

## Word/DOCX Compatibility

- Keep tables within Word page width; avoid wide cap-table or KPI grids that require horizontal scrolling.
- Long company names, URLs, investor questions, and table cells must wrap cleanly.
- Avoid interactive HTML, viewport-dependent hero sections, slide-like layouts, and complex absolute positioning.
- Prefer static charts/images with captions and alternative descriptions.
- DOCX/PDF conversion still requires separate export validation; this pattern does not guarantee conversion success.

## Patterns To Avoid

- Pitch-deck tone, oversized claims, slogan-first page structure, or slide-style fragments.
- Hiding risk, limitation, or assumption notes after promotional claims.
- Mixing audited facts, management estimates, and forward-looking assumptions in one unlabeled table.
- Recommending investment action as a certainty.

## Reviewer Checkpoints

- Does the document read as a controlled IR brief/factbook rather than a pitch deck?
- Are KPI summary, fact table, risk section, and Q&A section visible and well ordered?
- Are facts, assumptions, forward-looking statements, and unknowns separated?
- Is the cover choice aligned with sharing mode: `executive_decision` by default, `public_release` only for approved broad external sharing?
- Are tables and charts exportable to Word without horizontal overflow?
- Are appendix candidates clearly separated from body-level investor summaries?

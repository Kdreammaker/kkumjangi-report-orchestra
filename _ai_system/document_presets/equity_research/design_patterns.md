# Equity Research Design Patterns

## Document Purpose And Reader

- Purpose: Produce a sector, company, peer, or theme analysis in an equity-research style.
- Primary readers: internal strategy teams, finance teams, executives, investors, or research readers.
- The document should support analysis and scenario thinking, not provide unqualified investment advice.

## Recommended Document Structure

- Cover and disclaimer: scope, non-advisory status, data 기준일, and source limitations.
- Investment or research context: sector/company thesis, relevant period, and key questions.
- Sector and company snapshot: market drivers, business model, competitive context, and operating metrics.
- Financial review: revenue, margin, cash flow, earnings, balance sheet, or other relevant measures.
- Peer table: comparable companies, valuation multiples, performance metrics, and basis of comparison.
- Valuation and sensitivity: assumptions, methods, scenarios, and sensitivity table.
- Catalysts and risks: upside/downside events, timing, probability, and uncertainty.
- Conclusion and limitations: what the data supports, what remains uncertain, and what should be refreshed.

## Recommended Layout Blocks

- Disclaimer box near the beginning and before any recommendation-like conclusion.
- Data 기준일 box listing market price date, financial period, filing date, and source freshness.
- Peer table with consistent columns and short headers.
- Sensitivity table with base case, upside/downside scenarios, and key assumptions.
- Risk/catalyst matrix separated from the final interpretation.

## Design Application Priorities

- Use a peer table when comparison criteria, periods, currency, and source freshness can be kept consistent.
- Use valuation multiple tables for selected metrics only; keep the interpretation beside the table rather than hidden in notes.
- Use sensitivity tables when a small number of assumptions materially changes the result.
- Use an earnings bridge when the reader needs to see period-to-period drivers such as volume, price, margin, cost, or one-off effects.
- Use catalyst/risk matrices when timing, probability, impact, and uncertainty must be compared together.
- Split wide peer, valuation, and sensitivity tables into body summary, vertical metric families, appendix detail, or a landscape candidate for manual export review.

## Tables, Figures, And Captions

- Peer tables should use consistent periods, currencies, metrics, and source dates.
- Sensitivity tables should identify the changed assumptions and avoid implying certainty.
- Financial charts need units, periods, data 기준일, and source notes.
- Captions should state whether the table is factual, assumption-based, or analyst interpretation.

## AI Judgment Needed

- Decide which companies belong in the peer set and explain exclusions or imperfect comparability.
- Decide whether a valuation output is factual data, assumption-based scenario work, or analyst interpretation.
- Decide whether target price, rating, buy/sell/hold, or portfolio-action language is explicitly authorized; otherwise exclude it.
- Decide whether table width is best handled by vertical splitting, body summary, appendix detail, or a landscape candidate for later export review.

## Deferred Export-Native Features

- Do not claim automatic landscape sections for peer, valuation, sensitivity, or appendix tables.
- Do not claim Word-native field codes, generated DOCX captions, page fields, or native table-of-contents support.
- Treat regulated recommendation formats, rating templates, native caption numbering, and market-data refresh automation as separate work outside this module.

## Word/DOCX Compatibility

- Split wide financial, peer, and sensitivity tables by topic or metric family.
- Avoid tiny fonts, horizontal scrolling, embedded interactive charts, viewport-dependent layouts, and complex absolute positioning.
- Long issuer names, metric labels, URLs, and assumptions must wrap cleanly.
- Use static charts/images with captions and alternative descriptions.
- DOCX/PDF conversion still requires separate export validation; this pattern does not guarantee conversion success.

## Patterns To Avoid

- Buy/sell/hold certainty language unless an explicitly authorized regulated context exists.
- Hiding disclaimer or data 기준일 after the conclusion.
- Comparing peers on inconsistent periods or unlabeled currencies.
- Presenting stale market data as current.

## Reviewer Checkpoints

- Are disclaimer box and data 기준일 visible before analysis conclusions?
- Are peer table and sensitivity table readable within page width?
- Are data, assumptions, interpretation, risks, and limitations separated?
- Does the conclusion avoid investment-advice certainty?
- Are source dates and data freshness limits present for financial and market claims?
- Are wide-table decisions documented as body summary, split table, appendix detail, or export review candidate?

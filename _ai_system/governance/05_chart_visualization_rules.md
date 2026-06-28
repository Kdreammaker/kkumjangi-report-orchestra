# Chart and Visualization Rules

## Purpose

These rules govern report charts, graph images, legends, color use, and visualization appendices.

## Core Principles

- The main body should contain only charts that directly support the report's decision logic.
- Final table/chart/diagram production happens after body chapter fragments exist. Early visual planning may happen in the skeleton, but the final visual pass must answer the written chapter argument.
- Do not let tables substitute for every visual. If the reader needs to see movement, sequence, share, dependency, trade-off, or a route, prefer a chart, timeline, flow, map, or diagram over another table.
- Use the appendix for large tables, detailed charts, source images, screenshots, sensitivity views, and benchmark matrices that are important but too dense for the main flow.
- A chart must answer a specific analytical question. Do not add decorative visuals.
- Reader-facing chart notes must cite original sources as `자료:`. Local CSV/XLSX files are reproducibility artifacts and may appear only as `근거 데이터:`.
- Do not show raw local paths such as `../data_sources/example.csv` in chart images or captions.
- For delivery-stage reports, every material table, chart, graph, or process diagram must have a matching data/evidence artifact. Quantitative visuals need a CSV/XLSX under `data_sources/`; qualitative process diagrams need a source-record-backed artifact or source record reference. A generic phrase such as "internal review material" is not a sufficient `근거 데이터`.
- Preserve exact data-file paths in HTML comments, data indexes, or appendix artifact tables.

## Table vs Graph vs Diagram Selection

Use the visual form that matches the reader's question.

| Reader question | Prefer | Avoid |
|---|---|---|
| What are the exact criteria, conditions, or checklist items? | Table | Decorative chart |
| Which option is stronger across multiple criteria? | Matrix, heatmap, grouped bar, or table plus highlight | Long prose-only comparison |
| What changed over time or what happens next? | Line chart, timeline, roadmap, milestone diagram | Static table unless exact dates are the point |
| How much of the whole does each part represent? | Stacked bar, 100% bar, donut only when very simple | Dense table of percentages |
| What is the dependency or process path? | Flow diagram, Sankey, swimlane, decision tree | Table that hides sequence |
| What is the risk-return or feasibility-impact trade-off? | Quadrant, scatter, bubble, heatmap | Sorted checklist only |
| Which claims need exact legal/source traceability? | Table with source columns | Chart without source notes |

The visual pass must explicitly decide: keep as table, convert to chart, convert to diagram, move to appendix, or retire.

## Preferred Chart Library

- Use the locally installed Apache ECharts asset under `_ai_system/runtime/vendor/echarts/` as the preferred open-source renderer when an AI or local helper needs to generate bar, line, scatter, heatmap, timeline-like, or relationship charts from CSV/XLSX data.
- Final report HTML should not depend on runtime JavaScript charts. Render material charts to static SVG or PNG before assembly, then place the static artifact in the chapter fragment with a normal `figure`, `img`/`svg`, caption, and data/source note.
- Do not load CDN chart scripts in versioned, review-candidate, shared, confidential, or export-intended report HTML. CDN use in a scratch draft is at most a temporary limitation to record in `reports/visual_review.md`, not a delivery-ready state. If the user explicitly approves external network use for a draft, still replace it with local/static output before versioned sharing.
- Use the workspace color tokens and typography when configuring ECharts. The library supplies rendering; the report design still controls palette, labels, and source notes.
- If ECharts is not available in the local package, produce accessible inline SVG as the fallback and record the limitation in `reports/visual_review.md`.
- When a CSV/XLSX changes, regenerate the static chart artifact and update `reports/visual_review.md`; do not hand-edit a chart image without updating the data artifact.

## Supported Chart Types

Use these chart types first because they convert well to HTML, PDF, and DOCX.

| Chart type | Use case | Main elements |
|---|---|---|
| Bar chart | Category comparison, competitor count, fee comparison, designation count | axis, sorted bars, value labels, source note |
| Grouped bar chart | Comparing categories across scenarios or participants | grouped legend, consistent series order, value labels where space permits |
| Stacked bar chart | Composition by category, revenue mix, obligation mix | total label, segment legend, avoid too many small segments |
| Line chart | Time series, policy timeline metric, market volume trend | date axis, clear interval, endpoint labels |
| Area chart | Cumulative or share-of-total trend | baseline, transparent fill, avoid stacking more than 4 series |
| Scatter or bubble chart | Risk-return, market size vs. regulatory complexity | axis definitions, bubble legend, outlier labels |
| Heatmap | Legal matrix, jurisdiction comparison, risk scoring | discrete scale, cell labels, clear scale legend |
| Waterfall chart | Market-size bridge, revenue/cost build-up | start/end totals, positive/negative colors, subtotal labels |
| Timeline | Regulation, competitor launches, sandbox process | milestones, period bands, source note |
| Sankey or flow diagram | Asset, order, custody, settlement, or data flow | labeled nodes, directional arrows, limited node count |
| Matrix / quadrant | Prioritization, regulatory risk vs. business effect | axis meaning, placement rationale, caveat note |

## Color System

### Base Palette

| Token | Hex | Recommended use |
|---|---:|---|
| `primary-blue` | `#1F6FEB` | primary series, key bars, key route |
| `point-blue` | `#3485FF` | highlight, secondary point, selected item |
| `deep-blue` | `#1F4E79` | dark series, header, high-emphasis line |
| `dark-ink` | `#172033` | title dark, highest emphasis, dark background |
| `gray-1` | `#EEEFF0` | light fill, grid band |
| `gray-2` | `#CFD0D3` | border, gridline |
| `gray-3` | `#8D9299` | secondary labels |
| `gray-4` | `#616670` | axis labels, notes |

### Extended Chart Palette

Use this when a chart needs more than the core workspace palette.

| Token | Hex | Use |
|---|---:|---|
| `success-green` | `#289B6E` | positive result, permitted/low-risk item |
| `warning-gold` | `#C78A1B` | caution, dependency, medium risk |
| `risk-red` | `#C75252` | high risk, prohibition, loss |
| `violet` | `#6B5FB5` | additional neutral series |
| `teal` | `#158A9C` | additional neutral series |
| `rose` | `#B8567A` | additional neutral series |
| `slate` | `#46505C` | baseline, benchmark, other |

Rules:

- Use no more than 5 categorical colors in one chart unless the chart is in an appendix and has a clear legend.
- Do not rely on similar blues alone when categories need precise distinction. Add label text, shape, or pattern.
- Keep the same category color across the report. For example, if one market or scenario uses `primary-blue` in one chart, do not change it in another chart.
- For risk scales, use discrete classes rather than smooth gradients whenever possible.

## Pattern and Texture Rules

Use patterns when color alone is insufficient or when printed grayscale readability matters.

| Pattern | Use |
|---|---|
| Solid fill | Primary category or measured value |
| Diagonal hatch | Estimate, scenario, or projected value |
| Dotted fill | Unverified or partial evidence |
| Horizontal stripe | Benchmark or external comparator |
| Outline only | Target, threshold, or requested sandbox treatment |

Rules:

- Patterns supplement color; they do not replace labels or legends.
- Use thin, low-opacity patterns so the chart does not look noisy.
- Explain pattern meaning in the legend when it changes interpretation.

## Labels and Legends

- All labels placed on a dark bar or dark area must be white or near-white and pass visual contrast review.
- If a bar is too small for an internal label, place the label outside the bar with a leader line or show it in the legend/table.
- Avoid labels smaller than 11px in SVG and 8.5pt in print.
- Use endpoint labels for line charts when there are only a few series; use legends for many series.
- Put legends near the chart area, not far below a long note block.
- Keep legend order identical to visual stacking order.

## Source and Evidence Display

- Chart image footer may include `자료:` only when it names original institutions, authors, datasets, reports, statutes, or publications.
- Chart image footer must not cite local workspace files as the source.
- Report captions may include both:
  - `자료:` original source names,
  - `근거 데이터:` Korean dataset label.
- Exact local file paths belong in HTML comments, `data_sources/data_source_index.md`, or appendix artifact tables.

## Main Body vs Appendix

Main body charts should be:

- limited to the decision-critical message,
- visually simple,
- readable in one glance,
- backed by a short caption and source note.

Appendix charts may include:

- full sensitivity ranges,
- alternate scenario views,
- source screenshots or captured images,
- detailed benchmark comparison tables,
- larger legal matrices,
- multi-page data tables,
- chart methodology notes.

When the main body uses a summarized chart, add a short note pointing to the appendix for detail.

## Implementation Checklist

Before finalizing a chart:

- Confirm the body chapter fragment exists and the visual still fits the actual argument.
- Confirm whether the visual should be a table, graph/chart, timeline, flow, matrix, or appendix artifact by using the selection table above.
- Confirm the underlying CSV/XLSX exists and points back to original source ids.
- Confirm one visual maps to one declared data/evidence artifact. Multiple visuals may share a dataset only when the caption or data index explains the shared relationship.
- Confirm chart captions do not cite local files as `출처` or `자료`.
- Confirm labels are legible on desktop and printed A4 scale.
- Confirm color and pattern meanings are documented.
- Confirm the chart remains understandable in grayscale or low-saturation print.
- Save generated chart files under `figures/`.
- Record the chart creation or revision in the active worklog.
- Record the post-body visual review in `reports/visual_review.md` using `_ai_system/templates/report_visual_review.md` or an equivalent checklist.
- Optionally run `_ai_system/tools/finalize_visual_pass.py --project <project_name>` after that review to record hashes. Treat it as an audit hook, not as a visual design tool.

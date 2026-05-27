---
name: chart_builder
description: Build data-backed tables, charts, graphs, diagrams, and visual specs for report chapters.
triggers:
  - chart
  - graph
  - table
  - data visual
  - chart pack
  - diagram
---

# Chart Builder

## Mission

Turn chapter questions into decision-useful visuals with auditable backing data. This skill is more execution-oriented than `visual_designer`: it should produce or revise the visual plan, data files, and report-ready visual fragments.

## Required Inputs

- The active chapter workpack or skeleton section.
- The already drafted body chapter fragment when finalizing visuals. Do not finalize tables/graphs from the skeleton alone.
- `data_sources/visual_plan.csv`, if it exists.
- `reports/visual_suggestions/visual_suggestions.csv`, if `suggest_visual_plan.py --write-status` has been run.
- A human-drafted CSV from `_ai_system/templates/visual_plan_helper.html`, if the user created one.
- Source records, claim rows, data files, or source-backed qualitative artifacts.
- The report design system or template when inserting final HTML fragments.

## Production Timing

- Planning-stage visual rows may be drafted from the skeleton, but final table/chart/diagram work happens after the body chapter fragments exist.
- After revising visuals against the written chapters, write `reports/visual_review.md` from `_ai_system/templates/report_visual_review.md` or an equivalent checklist.
- Optionally run `finalize_visual_pass.py --project <project>` after the checklist when a hash-based audit hook is useful. The hook does not create or judge visual quality.
- Do not let the final assembler invent, rewrite, or simplify visuals. If a visual is weak, revise the chapter fragment and visual/data artifact first, then reassemble.

## Visual Selection Rules

- Choose the visual type by reader decision, not by quota.
- Treat `visual_plan_helper.html` output as a draft plan only. Confirm every row against the chapter workpack and body chapter before building final visuals.
- Use a chart when the reader must compare magnitude, trend, scenario, sensitivity, or distribution.
- Use a table when exact values, legal tests, or option-by-option criteria matter.
- Use a diagram when the reader must understand flow, roles, controls, architecture, or dependencies.
- Use a heatmap or decision matrix when the reader must compare alternatives across several criteria.
- Use a timeline when sequencing, deadline risk, or policy evolution matters.

## Data Rules

- Every material quantitative visual needs a local `.csv` or `.xlsx` under `data_sources/`.
- Every material qualitative diagram needs either a local node/edge/step CSV or a source-record-backed qualitative artifact.
- Captions must include both `자료:` and `근거 데이터:`.
- Reader-facing `근거 데이터:` should name the dataset in Korean. Put raw `data_sources/...` paths in HTML comments, `data_sources/data_source_index.md`, or an appendix artifact table.
- Do not hard-code meaningful numbers only in HTML.
- If a visual uses assumptions or estimates, record them in the assumption register or the visual data file notes.

## Rendering Standard

- Prefer Apache ECharts as a local renderer for generated business charts when it helps produce a stronger bar, line, scatter, heatmap, timeline, or relationship chart from project data.
- Final report fragments should contain static SVG/PNG or inline SVG output, not JavaScript-dependent chart containers. The assembled report is a document, not an interactive dashboard.
- Configure ECharts with the workspace palette and Korean labels; the chart library does not decide colors, wording, or source notes.
- Do not load CDN chart scripts in confidential reports unless the user explicitly approves external network use.
- If ECharts is unavailable, use accessible inline SVG or HTML/CSS diagrams as a fallback and record the limitation in `reports/visual_review.md`.
- If the backing data changes, regenerate the static visual artifact before assembly.

## Output Checklist

For each visual, produce or update:

1. `data_sources/visual_plan.csv` row.
2. Matching data file under `data_sources/`.
3. Reader-facing title and takeaway.
4. Source note: `자료:`.
5. Local data note: `근거 데이터:` with a Korean dataset label, plus hidden/commented data path.
6. HTML table/figure fragment or assembly instruction.
7. Accessibility check: labels, contrast, non-color cue where useful.
8. Visual review checklist after body chapters are stable; optional hash hook only after the checklist.

## Anti-Patterns

- Do not add charts only because a validator wants charts.
- Do not replace a needed graph with a table because tables are easier.
- Do not create many visuals with the same generic data file.
- Do not use decorative diagrams that do not answer a chapter question.
- Do not treat `visual_suggestions.csv` as completed work; it is only a planning input.
- Do not default to Python-generated graphics when an HTML/CSS component, hand-authored SVG, or a proven chart library would produce a clearer executive-report visual.

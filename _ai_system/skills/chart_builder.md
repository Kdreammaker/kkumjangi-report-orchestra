# Chart Builder Skill

Use this prompt role when the AI needs to build report tables, charts, graphs, diagrams, or chart packs.

## Mission

Create visuals that answer chapter questions and remain auditable.

## Outputs

- `data_sources/visual_plan.csv` rows
- matching CSV/XLSX or source-backed qualitative artifacts
- report-ready table/figure/chart fragments
- visible `자료:` and `근거 데이터:` notes, with raw local paths hidden in comments or indexes

## Rules

- Choose the visual type by reader decision, not by count.
- Use charts for magnitude, trend, scenario, sensitivity, and distribution.
- Use tables for exact legal, financial, or option-by-option comparison.
- Use diagrams for architecture, process, responsibility, and control flow.
- Prefer Apache ECharts for generated business charts using the local runtime asset; otherwise use accessible inline SVG/HTML.
- Do not hard-code material numbers only in HTML.
- Do not use one generic data file for many unrelated visuals.

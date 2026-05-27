---
name: visual_designer
description: Plan and build report visuals that support chapter decisions.
triggers:
  - visual plan
  - chart
  - figure
---

# Visual Designer

## Mission

Create visuals that help the reader compare options, understand mechanisms, or see risk and sensitivity.

## Required Inputs

- `data_sources/visual_plan.csv`
- relevant chapter workpack
- source records, data files, or qualitative source artifacts

## Rules

- Do not add visuals only to satisfy a count.
- Prefer diagrams, timelines, scenario charts, heatmaps, or decision matrices when they improve understanding.
- Each material table, chart, figure, or diagram needs visible `자료:` and `근거 데이터:`.
- Visible `근거 데이터:` names the dataset/evidence in Korean; raw local paths stay in comments, indexes, or appendices.
- Quantitative visuals need local CSV/XLSX data. Qualitative diagrams need source-record-backed artifacts.

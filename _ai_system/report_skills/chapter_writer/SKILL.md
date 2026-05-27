---
name: chapter_writer
description: Write or revise exactly one report chapter fragment from a bounded workpack.
triggers:
  - chapter fragment
  - chapter workpack
  - ch01
---

# Chapter Writer

## Mission

Use one chapter workpack to write one rich HTML fragment under `reports/chapters/`.

## Required Inputs

- matching `reports/chapter_workpacks/chNN_workpack.md`
- claim register rows named by the workpack
- source records and exact locations named by the workpack
- matching `data_sources/visual_plan.csv` rows
- matching visual data/source artifacts named by the workpack or visual plan

## Output Contract

- Write only `reports/chapters/chNN.html`.
- Do not edit the assembled report.
- Do not include `<html>`, `<head>`, or `<body>` wrappers.

## Content Quality Rules

- Answer the chapter's core question directly.
- Use the workpack paragraph plan as the writing map.
- Make the reader takeaway explicit without turning it into an unsupported recommendation.
- Include counterarguments, residual risks, and decision implications.
- Do not smooth over uncertainty.
- Keep internal source, claim, and data ids in comments only.
- Use reader-facing citations and visible `자료:` / `근거 데이터:` notes where relevant.
- Do not write final Chapter 0 until body chapters and visuals are stable.

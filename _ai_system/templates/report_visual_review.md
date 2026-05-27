# Visual Review Checklist

Use this after body chapter fragments are drafted and before Chapter 0, assembly, or final handoff.

This file is a working checklist. It is not a validator result and does not prove that the report is true or well written.

## Scope

- Project:
- Report:
- Reviewer:
- Review date:
- Body chapters reviewed:
- Design reference used:

## Visual Decisions

For each material table, chart, graph, diagram, matrix, or timeline:

| Visual ID | Chapter | Type | Reader decision it supports | Keep / revise / remove | Data or source artifact | Notes |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## Fit to Chapter Prose

- Does each visual answer a question raised by the drafted chapter text?
- Does any chapter need a visual because the prose currently hides a comparison, sequence, scenario, or risk trade-off?
- Are any tables being used only because they are easier than charts?
- Are any charts decorative, vague, or too thin to justify their space?

## Data and Captions

- Every material visual has `자료:`.
- Every material visual has a reader-facing data note that names the dataset in Korean, not a raw local path.
- Quantitative visuals point to CSV/XLSX files under `data_sources/` in HTML comments, `data_source_index.md`, or an appendix artifact table.
- Visual form was chosen deliberately: table, chart/graph, timeline, flow/diagram, matrix/heatmap, appendix artifact, or retired.
- Any table that represents movement, sequence, share, dependency, or trade-off was reconsidered as a graph/diagram before final assembly.
- Qualitative diagrams point to a source-record-backed artifact or node/edge/step data.
- Assumptions and estimates are named in the assumption register or data notes.

## Design Review

- Visual hierarchy is consistent with the report template.
- Labels are readable on desktop and print/PDF export.
- Color is not the only cue where comparison or risk is important.
- Tables are not overloaded with small text.
- Graphs reveal the decision pattern faster than a table would.

## Known Gaps

- Unresolved source gaps:
- Unresolved data gaps:
- Visuals to remove before handoff:
- Visuals to rebuild before handoff:

## Optional Audit Hook

After this checklist is complete, `finalize_visual_pass.py` may be run to record hashes of the reviewed body chapters and data artifacts.

The hook is only an integrity aid. It does not replace this checklist, the `chart_builder` skill, or human/AI design judgment.

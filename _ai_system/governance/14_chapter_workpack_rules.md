# Chapter Workpack Rules

## Purpose

Chapter workpacks make AI writing smaller, richer, and less context-heavy.

Use this rule before drafting, revising, or reviewing any substantial report chapter.

## Required Folder

For substantial reports, store chapter workpacks under:

`reports/chapter_workpacks/`

Use names such as:

- `ch01_workpack.md`
- `ch02_workpack.md`
- `ch07_workpack.md`
- `ch00_summary_workpack.md` only after body chapters are stable

The matching chapter prose fragment should live under:

`reports/chapters/ch01.html`

## Workpack Required Fields

Each chapter workpack should include:

1. Chapter purpose.
2. Reader decision this chapter supports.
3. Reader takeaway.
4. Core question.
5. Required answer boundary.
6. Paragraph/block plan.
7. Evidence inputs.
8. Claim register rows to use or create.
9. Assumptions and estimates.
10. Counterarguments, residual risks, evidence limits, and what would change the conclusion.
11. Required visuals from `data_sources/visual_plan.csv`.
12. Figure/table integration notes with `자료:` and `근거 데이터:` captions.
13. Appendix or glossary needs.
14. Forbidden claims or over-certainty terms.
15. Completion checklist.

The workpack is not reader-facing prose. It is the AI's bounded writing brief.

## Before Chapter Writing

Before writing a chapter fragment, confirm:

- report PRD exists,
- detailed TOC exists,
- major skeleton exists or the task is explicitly scoped as a short brief,
- the chapter workpack exists,
- source and claim inputs are sufficient for the chapter's intended conclusion,
- visuals required by the workpack are listed in `data_sources/visual_plan.csv`.

If these are missing, create or update the planning artifacts instead of drafting full prose.

Use `_ai_system/tools/compose_report_context.py --project <project_name> --stage chapter --chapter chNN --write-packet` before a chapter run. The output should be the chapter writer's read list and `context_packets/chapter_chNN.compact.md` packet. Do not ask the AI to load the assembled report as the main source when the chapter fragment and workpack exist.

The context composer should pull the chapter workpack, the claim/source indexes, source records named by the workpack, visual-plan rows for the chapter, and the matching data/source artifacts. If the composer cannot find those referenced files, fix the planning artifacts before asking the AI to write rich prose.

If the chapter's strategic answer is still unclear, use `_ai_system/tools/compose_report_context.py --project <project_name> --stage interview --chapter chNN` and run a short `decision_interviewer` pass before drafting.

## Chapter Fragment Standard

Chapter fragments must:

- be HTML fragments, not complete HTML documents,
- avoid `<html>`, `<head>`, and `<body>` wrappers,
- use semantic `section`, `h1`-`h3`, `p`, `table`, `figure`, `figcaption`, `ol`, `ul`, and `aside`,
- keep internal source/claim ids in comments only,
- use reader-facing citations, `자료:`, and `근거 데이터:` where applicable,
- avoid final recommendations unless the body evidence is stable and the workpack allows it.

## Reader-Scannable Writing Structure

Do not draft substantial chapters as uninterrupted paragraphs. Use the structure that best matches the reader decision:

- bullet lists for evidence, conditions, risks, and options;
- numbered lists for action sequences, approval gates, and implementation steps;
- nested or indented blocks only when they clarify hierarchy;
- short `aside`/callout blocks for 핵심 판단, 소결, 중단조건, or unresolved issues;
- tables for structured comparison and charts/diagrams for trends, timing, flow, dependency, scale, or tradeoff patterns.

Each major subsection should normally contain a clear judgment, supporting evidence, implication, and visible limitation or counterargument when material. A subsection that ends after two or three generic sentences is not complete for a substantial report unless the workpack explicitly marks it as a short bridge.

## After Chapter Writing

After writing a chapter:

- check whether every workpack question was answered,
- update claim/data/source registers if new material claims or visuals were added,
- verify that planned visuals are either implemented, deferred with reason, or moved to the appendix,
- keep unresolved risks visible instead of smoothing them out.

For chapter visuals, use `_ai_system/tools/compose_report_context.py --project <project_name> --stage chart --chapter chNN --write-packet` when the AI needs to create concrete chart/table/diagram data files and HTML fragments. This is separate from writing prose so the AI does not choose the easiest visual just to satisfy a count.

## Chapter 0 Workpack

Create `ch00_summary_workpack.md` last. It should summarize:

- body chapter conclusions,
- decision options,
- tradeoffs,
- residual risks,
- required next actions,
- evidence limits.

Do not create a final Chapter 0 summary from an early PRD or TOC alone.

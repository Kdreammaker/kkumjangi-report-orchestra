# Report Quality Scoring Rules

## Purpose

Use this rule when the workspace needs to judge whether a report is merely runnable, draftable, internally reviewable, or delivery-ready.

Gate rules decide what is allowed or blocked. Quality scoring shows how strong the work is and gives AI assistants a positive target to optimize for.

The goal is not to add more prohibitions. The goal is to reward better work and make shortcuts visible:

- better original source preservation,
- better claim traceability,
- deeper analysis,
- richer charts and tables,
- stronger DOCX/PDF conversion readiness,
- more honest residual-risk reporting.

Scores therefore use interaction:

`quality_score = bonus_score - deduction_points`, then hard blockers cap the level.

An AI should feel that better work earns a higher score, while shortcuts lower the score even when a loose validator passes.

## Core Principle

Do not ask only, "Did it pass?"

Ask:

1. What level is this report now?
2. What score did it earn?
3. What would raise the score?
4. What hard blockers prevent the next level?

AI assistants should be encouraged to reach higher quality levels, not merely avoid forbidden words.

Level 4 report-factory constraint:

- A substantial report should not reach Level 4 from word count, tables, or green validators alone.
- Level 4 requires the modern report factory path: chapter workpacks, matching chapter HTML fragments, reusable cover data/component, an assembled-report marker from `assemble_report.py`, a Chapter 0 summary, and a role-based `visual_plan.csv`.
- Visual counts should count material visual blocks, not repeated markup inside the same visual. A single `<figure>` that contains an SVG is one figure, not two.
- When changing these constraints, run `_ai_system/tools/smoke_report_quality_constraints.py`.

## Report Levels

| Level | Name | Meaning | Typical allowed description |
|---|---|---|---|
| Level 0 | Environment Ready | Workspace and launchers are runnable, but report work is not proven. | 작업환경 정상 |
| Level 1 | Planning Ready | PRD, detailed TOC, and source collection plan exist or are being prepared. | 기획 준비 완료 |
| Level 2 | Evidence Mapping Draft | User-provided sources are inventoried and claims are being mapped. | 자료 매핑 초안 |
| Level 3 | Original-Backed Draft | Key domestic/foreign originals are preserved and major claims have source records. | 원문 기반 초안 |
| Level 4 | Internally Reviewable Candidate | Substantial body, footnotes, appendices, charts/tables, data files, and strict checks are mostly satisfied. | 내부 검토 후보 |
| Level 5 | Delivery Candidate | Strict research, report artifact, workspace validation, and DOCX/PDF conversion verification all pass or residual risks are explicitly accepted. | 납품 후보 |

Never use a higher label when hard blockers remain.

## Score Categories

Score reports on a 100-point scale.

| Category | Points | Rewarded behavior |
|---|---:|---|
| Source originality and preservation | 20 | Exact official URLs, user-provided/preserved originals when needed, access dates, non-generic URLs, and honest user-request-needed status. |
| Source record and quote traceability | 15 | Source records point to exact URLs or originals; exact quotes and page/section/location locators are present. |
| Claim readiness and uncertainty handling | 15 | Claims have source ids, locations, assumptions, confidence, unresolved issues, and counsel-review markers where needed. |
| Analytical depth and chapter completeness | 15 | Body depth fits PRD/TOC; chapter workpacks are answered; analysis includes evidence, interpretation, counterarguments, residual risk, and implications. |
| Data, tables, charts, and figures | 15 | Material visuals have a decision purpose, CSV/XLSX backing or source-record support, assumptions, captions, and accessible design. |
| Template and reproducibility | 10 | Uses reusable cover, chapter fragments, assembler, and workspace report templates/styles instead of one-off hardcoded formatting. |
| DOCX/PDF conversion readiness | 10 | Semantic HTML, static figures, footnote mapping, conversion artifacts, and rendered verification exist. |

## Deduction Categories

Apply deductions when an artifact chooses the easiest route instead of the strongest route.

| Deduction | Typical points | Why it matters |
|---|---:|---|
| Missing Chapter 0 final summary | 8 | The final synthesis must be written last and appear as report Chapter 0. |
| Thin body or unanswered chapter questions for stated scope | 10 | A substantial report needs section depth and answered chapter workpacks, not only a scaffold. |
| No charts/figures in analysis-heavy report | 8 | Market, scenario, financial, risk, roadmap, and benchmark analysis usually need visuals. |
| Visuals outnumber data files | 10 | Each material table, graph, chart, or figure should have its own CSV/XLSX or source-record-backed qualitative artifact. |
| Weak claim locations | 8 | Claims without page/section/URL/quote locations are difficult to audit. |
| Fewer than 8 source records for substantial report | 8 | Thin source records usually mean the report is still evidence-mapping, not reviewable. |
| Generic homepage or vague URL used as evidence | 10 | A homepage is not an original document. |
| Fake or prompt-token Exact Quotes | 20 | This is a research integrity failure, not a formatting issue. |
| One-off styling instead of reusable template | 5 | Reproducibility and DOCX/PDF readiness fall. |
| Unverified DOCX/PDF conversion | 10 | File creation alone does not prove usable conversion quality. |
| Strict validation failure hidden or omitted | hard blocker | Status reporting becomes unreliable. |
| Project drift after user says continue | hard blocker | “진행하세요” means continue the active project/workstream unless the user changes it. |

Do not rename a report from `내부 검토용` to `brief`, `scaffold`, or `자체 분석용` merely to avoid deductions. If the PRD and TOC describe a substantial internal report, either meet that standard or report the lower level honestly.

## Skeleton-First Expansion Flow

Substantial reports should not jump directly from TOC to a full final-looking HTML.

Use this sequence:

1. Report PRD.
2. Report design file.
3. Detailed TOC.
4. TOC self-review and user approval for substantial reports.
5. Major skeleton / 주요 골조.
6. Skeleton score.
7. Chapter workpacks and chapter-by-chapter full text expansion.
8. Chapter-by-chapter tables, graphs, figures, and diagrams with matching data files.
9. Final Chapter 0 summary and recommendations.
10. Strict research/artifact/workspace checks and AI quality review, with optional quality score if a numeric panel is useful.

The major skeleton should contain the chapter logic, thesis, evidence needs, counterarguments, risk questions, data needs, visual plan, and DOCX/design notes. It should not contain reader-facing final tables or graphs. Tables and graphs belong in the chapter visual/data stage after the full text direction is stable.

Chapter workpacks should then translate the skeleton into bounded writing briefs. A good workpack gives the AI one chapter question, the decision use, source inputs, claim rows, counterarguments, visual needs, appendix needs, and forbidden overclaims.

Apply the skeleton scoring checklist after creating the major skeleton. `_ai_system/tools/report_skeleton_score.py --project <project_name>` is available as a mechanical aide, but the AI must still read the skeleton against the PRD and TOC. Improve the skeleton before writing full text if it lacks thesis, evidence paths, counterarguments, risks, data/visual intent, or decision use.

## Chapter 0 Summary Rule

The final summary must be report Chapter 0, not a casual preface and not a first-draft executive summary.

Chapter 0 is written last, after:

- body chapters have been expanded,
- material claims have been mapped,
- tables and graphs have corresponding data files,
- major residual risks are visible,
- appendices and footnotes are stable.

Strict delivery checks should fail when a report lacks Chapter 0 / 제0장 요약.

## Table and Graph Data Pairing

Each material table and each material graph/figure/chart needs a corresponding data artifact:

- quantitative items: one CSV/XLSX per visual where practical,
- qualitative process diagrams: a source-record-backed artifact or a CSV/XLSX describing nodes/edges/steps,
- all visible captions: `자료:` for reader-facing source and `근거 데이터:` for a Korean dataset/evidence label, with raw local paths preserved in comments, indexes, or appendix artifact tables.

Using one generic CSV for many unrelated tables or graphs lowers the score unless the CSV is explicitly a multi-sheet/multi-section workbook equivalent and the caption points to the relevant section.

## Positive Optimization Prompts

Prefer this:

> To earn a higher source score, record the exact official URL and access date, add page/section/quote locators, and ask the user for any file that must be provided manually.

Instead of only this:

> Do not cite AI summaries.

Prefer this:

> To earn a higher visualization score, convert market, scenario, risk, or roadmap sections into charts/figures with matching CSV/XLSX files and visible `자료:` / `근거 데이터:` notes.

Instead of only this:

> Do not omit charts.

Prefer this:

> To earn an internally reviewable level, draft by chapter workpack until each body section answers its decision question with evidence, interpretation, counterargument, implications, footnotes, visuals, and appendices.

Instead of only this:

> Do not write a short report.

## Hard Blockers

These are not score issues. They prevent a report from reaching Level 3 or higher:

- A `report_citable` source has no source record.
- A `report_citable` source record has no exact official URL, user-provided/preserved original, or quote/page/section locator.
- `Exact Quotes` text cannot be found in the preserved original or captured text where a local original exists.
- A generic homepage is marked `original_verified=yes` or `report_citable`.
- A source record uses AI-generated text as exact source text.
- A strict validation failure is reported as a pass.
- A report is called internally reviewable while strict delivery checks fail.
- `validate_closeout.py` or `run_guarded_step.py --step closeout` fails.
- A generated DOCX/PDF is called conversion-ready without opening/rendering/structure verification.

Quality scoring is not a substitute for closeout. A high score can still be blocked by dummy originals, missing workspace deliverables, snapshot mismatches, active `.bak` files, or failed closeout validation.

## DOCX/PDF Readiness

If DOCX conversion is likely, HTML authoring should remain conversion-friendly:

- Prefer semantic headings, paragraphs, lists, tables, footnotes, figures, and appendices.
- Avoid relying on complex CSS-only charts for material evidence.
- Use static SVG/PNG figures or Word-compatible tables for important visuals.
- Keep figure/table captions in plain text.
- Preserve footnote/endnote mapping.
- Keep local data files under `data_sources/`.
- Verify generated DOCX/PDF by structure and rendered output before calling it delivery-ready.

## Length as a Depth Signal

Visible length is a weak proxy. It can detect a thin memo, but it should not become the AI's writing target.

Use chapter-workpack coverage as the main depth signal, not a fixed character threshold. A shorter report can be strong if the PRD is narrower and the chapter workpacks are fully answered. A longer report can still be weak if it lacks counterarguments, source linkage, visuals, or decision implications.

When reporting score-lift opportunities, prefer chapter-completeness feedback over padding advice.

## Required Status Report Shape

When reporting a substantial report status, include the following. The numeric fields are optional if the score script was not run; do not let missing numeric scoring prevent a substantive AI review.

- `current_level` when available
- `quality_score` when available
- `highest_scoring_areas`
- `score_lift_opportunities`
- `hard_blockers`
- `validations_run`
- `not_tested`
- `residual_risk`

If a report is only Level 1 or Level 2, say so plainly. It can still be useful, but it is not an internally reviewable report.

## User-Facing Quality Status

`_ai_system/tools/report_quality_score.py --project <project_name> --write-status` can export a small human-readable status panel under `reports/quality_status/`.

Use this only when a non-technical user needs a numeric status view without reading terminal JSON. It is not part of the default report-writing flow.

The exported panel is a convenience view only:

- it does not replace research integrity validation,
- it does not replace closeout validation,
- it does not replace AI judgment under the PRD, TOC, chapter workpacks, and visualization rules,
- it does not prove legal, factual, or business correctness,
- it should not turn score, length, or visual count into writing targets,
- it should be regenerated after material report changes.

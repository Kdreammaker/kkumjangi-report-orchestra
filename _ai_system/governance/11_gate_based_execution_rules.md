# Gate-Based Execution Rules

## Purpose

Use this rule when a project or report task can move through multiple stages: setup, planning, source collection, source/claim mapping, drafting, review, and delivery.

This rule exists because adding more instructions is not enough. AI assistants may still optimize for a green validation result instead of doing the real work. The workspace therefore treats stage movement as a gate decision with explicit allowed and blocked actions.

Use `_ai_system/governance/12_report_quality_scoring_rules.md` after drafting or when reviewing another AI's output. Gates decide whether an action is allowed; AI review decides whether the writing is actually useful. `_ai_system/tools/report_quality_score.py` is an optional advisory panel, not a gate.

## User Approval vs Internal Gates

Do not confuse internal safety gates with user approval gates.

User approval is required for:

- creating a new project after a setup brief,
- confirming report purpose, scope, audience, and evidence bar,
- sensitive reference intake or changed confidentiality handling,
- starting substantive body drafting after a major direction choice,
- external sharing, cloud handoff, or packaging,
- changing the strength of legal, regulatory, policy, or business conclusions.

AI may continue these internal production steps without asking for a fresh approval every time, unless the user explicitly says to stop before file creation:

- creating a detailed TOC after PRD approval,
- registering source leads and link states,
- updating source/workflow status panels,
- creating a major skeleton and chapter workpacks,
- running validators and recording failure reasons,
- repairing source/claim records within the approved report scope.

Internal gates still decide whether drafting, delivery, or closeout claims are allowed. User approval does not override failed evidence, preflight, or closeout gates.

When a guarded chain fails, report it as blocked. Do not summarize a failed review-candidate, handoff, or closeout run as `완료`, `최종 완료`, `Green Pass`, or `검증 통과`. The status must name the failed gate, the first blocking check, and the remaining action.

Do not run the same validator in a loop to create a sense of progress. If the same validator fails twice with the same blocker and no new actionable information, stop the loop and translate the blocker into one of:

- a production repair the AI can do now,
- a source/material request for the user,
- a scope or approval question,
- a known limitation to carry into the status report.

Record the repeated failure and the chosen next action in the active worklog.

## Core Principle

Do not ask, "Did the validation pass?" first.

Ask, "What is the highest safe action now?"

Every major project/report status update must distinguish:

- `allowed_actions`: what the AI may do next.
- `blocked_actions`: what the AI must not do yet.
- `blockers`: what evidence, approval, source, data, or validation is missing.
- `not_tested`: what was not checked.
- `quality_score` and `current_level` when a report artifact exists.

Workspace validation only proves that the container is organized and runnable. It never authorizes report conclusions.

## Gate 1: Planning

Planning is the default state for a new or reset project.

Allowed:

- create or update a project setup brief,
- create or update report PRD,
- create or update detailed TOC,
- create or update source collection plan,
- ask and log clarification questions,
- create a report scaffold with placeholder sections only,
- run workspace validation.

Blocked:

- reader-facing report conclusions,
- `confirmed_fact` claims,
- internally reviewable or final labels,
- benchmark conclusions,
- quantitative charts or market sizing not backed by data files.

Exit condition:

- PRD exists,
- detailed TOC exists,
- source collection plan exists or the TOC itself maps sections to source needs,
- user decisions needed for scope are logged.

## Gate 2: Evidence Mapping

Evidence mapping is where material is collected and registered before body writing.

Allowed:

- process files in the project drop zone,
- collect external originals, exact URLs, official PDFs, web captures, or screenshots,
- create source records,
- create claim register rows,
- create data files under `data_sources/`,
- create benchmark cards,
- create legal matrix drafts,
- run report preflight.

Blocked:

- treating AI summaries as originals,
- using internal slides to verify foreign benchmark facts,
- promoting OCR-needed or empty extracted-text sources to `report_citable`,
- saying a report is internally reviewable,
- writing executive summary or final recommendations.

Exit condition:

- `report_preflight.py --project <project_name> --for-drafting` passes,
- source records and claim register support the specific sections to be drafted,
- material tables/charts have data files or source-record-backed qualitative artifacts.

## Gate 3: Major Skeleton

Major skeleton is where the report's argument is designed before long-form prose.

Allowed:

- create or update the major skeleton / 주요 골조,
- map each chapter to thesis, evidence needs, claims, risks, counterarguments, data needs, visual candidates, appendix candidates, and DOCX/design notes,
- run `_ai_system/tools/report_skeleton_score.py --project <project_name>`,
- improve the skeleton until it can guide full text.

Blocked:

- adding reader-facing final tables, graphs, or decorative visuals to the skeleton,
- writing Chapter 0 summary,
- calling the skeleton an internal review report,
- using skeleton score as source truth or legal validation.

Exit condition:

- skeleton score is normally 70 or higher,
- chapter-by-chapter full text expansion plan exists,
- data/visual plan identifies which chapters need CSV/XLSX-backed visuals.

## Gate 4: Section Drafting

Section drafting starts only after the drafting gate allows it.

Allowed:

- draft report sections in the detailed TOC order,
- draft one chapter or bounded section at a time for substantial reports,
- create section-specific footnotes and appendices,
- write chapter full text before adding chapter visuals,
- update claims as interpretations or unresolved issues where evidence is incomplete.

Blocked:

- writing the executive summary before the body evidence is stable,
- adding final graphs/tables before the chapter's full-text direction and data needs are clear,
- calling the document complete when only a brief/scaffold exists,
- changing the title label to avoid strict report requirements,
- hiding strict-research failures behind non-strict validation results,
- calling a failed guarded run complete because later workspace or snapshot checks passed.

Exit condition:

- all body sections required for the current draft scope exist,
- chapter-by-chapter visual/data pass is ready,
- report artifact validation and research integrity checks pass or residual risks are visible.

## Gate 5: Chapter Visual/Data Pass

Chapter visual/data pass adds the evidence display layer after full prose exists.

Allowed:

- add tables, charts, graphs, figures, and process diagrams chapter-by-chapter,
- create the corresponding CSV/XLSX or source-record-backed qualitative artifact for each material visual,
- add `자료:` and `근거 데이터:` captions,
- place detailed chart packs and sensitivity tables in appendices.

Blocked:

- using one vague data file for unrelated visuals,
- hard-coding material numbers only in HTML,
- calling a visual data-backed without a local data artifact,
- writing the final Chapter 0 summary before visuals and appendix notes are stable.

Exit condition:

- each material table and graph/figure/chart has a corresponding data artifact,
- report artifact validation does not report missing visual captions or data references,
- chart/table choices support the report questions.

## Gate 6: Chapter 0 Summary

Chapter 0 is the final synthesis gate.

Allowed:

- write `Chapter 0` / `제0장 요약`,
- summarize decision questions, findings, quantified scenarios, major risks, unresolved issues, and next actions,
- write final recommendations only where evidence and uncertainty allow.

Blocked:

- writing Chapter 0 before body chapters and visual/data pass,
- using Chapter 0 to introduce unsupported new claims,
- presenting unresolved legal/business issues as settled facts.

Exit condition:

- Chapter 0 exists in the report,
- it is consistent with body chapters, risk sections, data files, and appendices.

## Gate 7: Review Candidate

A report may become a review candidate only when the evidence and artifact gates support it.

Allowed:

- describe the report as `internally_reviewable_draft`,
- ask for business, legal, compliance, or executive review,
- prepare cross-check prompts for another AI or reviewer.

Blocked:

- claiming legal approval,
- claiming regulatory approval probability as fact,
- describing workspace validation as report-quality validation,
- hiding strict gate failures,
- presenting quote-verification, reference-appendix, export, or closeout blockers as residual notes while still claiming completion.

Exit condition:

- `report_preflight.py --project <project_name> --for-delivery --strict-research` passes for substantial internal-review reports,
- `validate_research_integrity.py --project <project_name>` passes or clearly reports residual risks,
- `validate_report_artifact.py --project <project_name> --strict-delivery` passes or clearly reports residual risks,
- `validate_closeout.py --project <project_name>` passes,
- workspace validation is reported separately.

Prefer `run_guarded_step.py --project <project_name> --step closeout` before moving any report to review-candidate or closeout status. If the consolidated gate fails, the report remains blocked even when individual non-strict checks look green.

## Stage Promotion Rule

The AI must not manually promote a report stage just because it wrote a document.

`project_state/report_stage_manifest.json` is a record, not proof. If the manifest says `review_candidate` but gate checks indicate missing evidence, the gate result wins and the stage must be treated as blocked or stale.

Use `_ai_system/tools/report_gate_status.py --project <project_name>` before:

- drafting beyond a scaffold,
- saying a report is internally reviewable,
- accepting a handoff from another AI,
- auditing a suspicious pass report.

## Source Collection Plan Rule

For broad or substantial reports, create or update a source collection plan before large-scale collection.

The plan should state:

- report section,
- evidence needed,
- likely source type,
- minimum official/original source target,
- whether domestic and foreign sources are both required,
- whether OCR, translation, web capture, or data cleaning is expected,
- collection status.

The plan can be a section in the detailed TOC for simple work. For large reports, keep it as a separate file under `notes/` or `drafts/`.

## Large Report Drafting Rule

Do not try to produce a substantial internal-review report in one burst.

For reports with broad legal, regulatory, market, and benchmark analysis, draft by section:

1. method and scope,
2. market/business background,
3. domestic regulatory baseline,
4. foreign benchmark and regime comparison,
5. candidate structures,
6. risk and control matrix,
7. data and financial/market effect sections,
8. appendix pack,
9. chapter-by-chapter visual/data pass,
10. Chapter 0 executive summary and recommendations.

The executive summary is written last and appears as Chapter 0 / 제0장 요약.

## Reporting Standard

When reporting status to the user, use this shape:

- `현재 게이트`: planning / evidence_mapping / writing_allowed / review_candidate / blocked.
- `allowed_actions`: what may safely happen next.
- `blocked_actions`: what must not happen yet.
- `blockers`: concrete missing items.
- `validation`: workspace, research, preflight, report artifact, each separated.
- `quality`: hard blockers, concrete improvement opportunities, and optional level/score when a score panel was actually run.
- `residual risk`: legal/business/content risks not solved by tools.

Avoid phrases such as "완벽히 통과", "무결점", or "완료" unless the report scope and all required gates actually support that statement.

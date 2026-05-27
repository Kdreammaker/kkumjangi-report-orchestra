# Report PRD Rules

## Purpose

A report PRD, also called a report brief, controls how a report should be produced. It is not part of the reader-facing report unless the user explicitly asks for a methodology appendix.

Use the PRD to keep production metadata out of the final HTML while preserving enough context for consistent drafting, review, conversion, and later updates.

## When a Report PRD Is Required

Create or update a report PRD before:

- starting any substantial internal review report,
- revising the report's audience, purpose, scope, or classification,
- changing output format, such as HTML to DOCX/PDF,
- adding or removing major sections,
- changing evidence standards, citation style, chart standards, or appendix policy,
- changing the report from internal review to external proposal or government submission,
- resuming work after a long gap where assumptions may have drifted.

Tiny notes, one-off answers, and narrow fact lookups do not need a PRD unless they become report artifacts.

## Location and Naming

Store report PRDs under the project folder:

`00_사용자_작업공간/<project>/report_prd/`

Recommended filename:

`<report_slug>_prd.md`

Examples:

- `project_01_internal_review_report_prd.md`
- `project_02_korea_stock_rwa_internal_review_report_prd.md`
- `phase_01_comparative_memo_prd.md`

If a project has multiple reports, create one PRD per report.

## Required Contents

Each report PRD should include:

- `report_id`: stable report identifier.
- `report_title`: working Korean report title.
- `document_classification`: one of `내부 검토용`, `상부 보고용`, `파트너사 공유용`, or `외부 공유용`, unless the user explicitly defines another label.
- `confidentiality_status`: `대외비` or `대외비 아님`.
- `recipient_or_distribution`: intended recipient group and sharing boundary.
- `external_sharing_allowed`: whether the report may leave the organization/project workspace.
- `reader`: expected primary and secondary readers.
- `decision_context`: what decision or discussion the report should support.
- `business_questions`: key questions the report must answer.
- `scope_in`: topics included.
- `scope_out`: topics excluded or deferred.
- `assumptions`: working assumptions that shape the report.
- `evidence_standard`: required source tiers, source records, screenshots, datasets, and review level.
- `citation_display`: reader-facing citation style.
- `claim_handling`: how facts, interpretations, estimates, and unresolved issues are tracked.
- `data_and_chart_plan`: expected tables, charts, source datasets, and appendix chart packs.
- `appendix_plan`: expected glossary, source captures, detailed tables, matrices, and methodology notes.
- `reader_visible_metadata`: what metadata may appear in the rendered report.
- `hidden_or_managed_metadata`: what belongs in PRD, worklog, source index, claim register, data files, or HTML comments.
- `output_format`: working format and future conversion requirements.
- `design_document`: path to the report-specific design file, normally `reports/report_design.md`.
- `review_gates`: checks required before treating the report as draft/final.
- `status`: `planning`, `drafting`, `review`, `final_candidate`, `final`, or `archived`.
- `open_questions`: unresolved questions for the user, counsel, partners, or regulators.
- `revision_log`: dated change history.

## Reader-Facing vs Managed Metadata

Reader-facing reports may show:

- document classification,
- confidentiality status or warning when approved,
- report title,
- date or 기준일,
- version only if useful to the reader,
- authoring organization or team if approved,
- short scope note when it helps interpretation.

Reader-facing reports should generally not show:

- output-format instructions such as `HTML-first`,
- internal production workflow,
- internal source ids or claim ids,
- assumption ids,
- raw local file paths,
- task-management notes,
- prompt or agent instructions,
- detailed report PRD fields.

Manage those items in:

- report PRD,
- worklog,
- source index,
- claim register,
- assumption register,
- data files,
- HTML comments near the relevant paragraph/table/chart.

## Classification and Confidentiality Boundary

Document classification and confidentiality are report-level decisions, not project-level defaults.

- Do not store default document classification, default confidentiality, or external sharing permission in `project_profile.json`.
- Confirm `document_classification`, `confidentiality_status`, and `recipient_or_distribution` in the PRD before substantive drafting.
- If the user has not confirmed them, use the conservative working assumption `내부 검토용 / 대외비` for handling and do not claim the report is externally shareable.
- Internal formats (`내부 검토용`, `상부 보고용`, `파트너사 공유용`) should be treated as `대외비` unless the user explicitly says otherwise.
- `외부 공유용` still needs explicit confirmation of what can be shared and which source materials are excluded.

The project profile stores stable project logistics: responsible people, approval line, practitioners, external contacts, organization, and CI/logo references. It must not decide a report's sharing class.

`reports/report_registry.csv` may mirror report-level metadata for dashboards: report title, classification, confidentiality, version, stage, owner, practitioners, reviewers, latest file, PRD path, and next action. Treat it as a report/version index, not as a replacement for the PRD. If the registry and PRD conflict, update the registry from the PRD or ask the user before changing the report's distribution status.

## PRD vs Report Design

The PRD defines why and for whom the report is written. The report design file defines how it looks.

PRD owns:

- purpose, reader, decision context, scope,
- document classification and confidentiality,
- distribution/recipient boundary,
- evidence bar, citation policy, and conclusion strength,
- open questions and review gates.

`reports/report_design.md` owns:

- page size, A4 margins, print rules,
- typography, font sizes, heading hierarchy,
- color palette and accessibility constraints,
- cover preset, logo placement, and CI priority,
- table/chart/diagram style,
- confidentiality warning placement and wording.

Do not duplicate full PRD scope fields in `report_design.md`, and do not put visual styling decisions only in the PRD when the report has a separate design file.

## HTML Comment Boundary

Use HTML comments only for local auditability near a specific report element.

Appropriate HTML comments:

```html
<!-- claim_type: interpretation; source_ids: source-a, source-b; claim_id: project-c001 -->
<!-- data_file: ../data_sources/example_chart_data.csv; assumption_ids: a001, a002 -->
```

Do not use HTML comments as a substitute for the report PRD. Whole-report metadata belongs in the PRD.

## Update Criteria

Update the report PRD when any of the following changes:

- audience,
- document classification,
- confidentiality status or distribution boundary,
- decision context,
- scope in/out,
- key business questions,
- report title,
- output format,
- evidence standard,
- citation or chart standard,
- appendix policy,
- status,
- open questions,
- review gate results,
- major section structure,
- assumptions that affect conclusions.

Do not update the PRD for minor grammar edits or purely cosmetic HTML changes unless they affect design requirements.

## Revision Log Format

Every report PRD must include a revision log table:

| Date/KST | Version | Change Type | Changed By | Summary | Reason | Impacted Sections |
|---|---|---|---|---|---|---|

Use change types:

- `created`
- `scope_change`
- `audience_change`
- `evidence_change`
- `format_change`
- `design_change`
- `section_change`
- `status_change`
- `correction`

When a PRD change affects existing report text, record the follow-up action in the active worklog.

Also record the PRD update in the active worklog whenever:

- a PRD is created,
- a PRD status changes,
- a PRD revision changes report scope, audience, output format, evidence standard, citation/chart policy, appendix policy, or review gates,
- a PRD change requires report, TOC, source, claim, or data-file updates.

If the PRD change came from user feedback, record the decision in `questions/question_log.md` unless it is already captured in the same conversation and has no durable impact beyond the current edit.

## Relationship to Other Artifacts

- `detailed TOC`: derives from the PRD and maps sections to evidence.
- `source index`: stores source records and reliability tracking.
- `claim register`: stores claim status and support.
- `worklog`: stores actual actions and decision changes during work sessions.
- `_ai_system/DESIGN_DOCUMENT.md`: stores global design rules.
- `reports/report_design.md`: stores report-specific visual rules when a substantial report needs them.
- final HTML report: shows only reader-facing content and minimal approved metadata.

## Review Checklist

Before drafting:

- PRD exists.
- reader and decision context are clear.
- scope in/out is explicit.
- citation, data, chart, and appendix standards are defined.

Before final candidate:

- PRD status and report status match.
- visible report metadata matches `reader_visible_metadata`.
- production metadata has not leaked into the report body.
- all major scope changes are in the revision log and worklog.

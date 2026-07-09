# Report PRD Rules

## Purpose

A report PRD, also called a report brief, controls how a report should be produced. It is not part of the reader-facing report unless the user explicitly asks for a methodology appendix.

Use the PRD to keep production metadata out of the final HTML while preserving enough context for consistent drafting, review, conversion, and later updates.

## When a Report PRD Is Required

Create or update a report PRD before:

- starting any substantial internal review report,
- revising the report's audience, purpose, scope, or classification,
- changing output format, such as HTML to DOCX/PDF/HWPX-compatible HTML,
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
- `document_type_preset`: selected document preset id, or `undecided` until the interview/PRD resolves it.
- `authoring_structure_profile`: `decision_first`, `proposal`, `review_opinion`, `meeting_minutes`, `education`, `manual`, `public_release`, `custom`, or `undecided`.
- `authoring_structure_basis`: selected document type default, user request, source document structure, target reader, target file type, or custom rationale.
- `default_paragraph_mode`: `bullet_first`, `prose_first`, `mixed`, or `undecided`.
- `prose_preferred_slots`: slots where prose is intentionally kept, such as background, rationale, legal/regulatory context, learning explanation, press lead, quotation, or narrative summary.
- `list_style_preset`: `formal_outline`, `guide_outline`, `procedure_steps`, `administrative_outline`, `symbol_bullets`, `not_applicable`, or `undecided` when nested numbered or bulleted hierarchy matters.
- `list_style_preset_basis`: selected preset default, user request, source document style, target file type, or not applicable.
- `artifact_workflow_mode`: `brief`, `standard`, `substantial`, or `specialized`. Start from the selected preset's `default_artifact_workflow_mode` and `stage_overlays.md`; this decides whether the full report-factory sequence is required or whether some stages are skipped/compressed with a recorded rationale.
- `content_depth`: `concise`, `standard`, or `expanded`. Default to `standard` unless the user asks otherwise or the artifact purpose clearly implies a shorter or deeper treatment.
- `content_depth_basis`: why the chosen depth fits the reader, artifact purpose, evidence depth, and time/use context. `concise` should target roughly 30-60% of standard; `expanded` should target roughly 180-250% of standard when useful evidence supports it.
- `execution_control_mode`: `checkpointed` or `delegated`. Use `checkpointed` by default for setup, TOC approval, high-risk distribution, legal/regulatory, securities, or external sharing decisions. Use `delegated` when the user asks the AI to proceed to a target point and report issues afterward.
- `execution_control_target`: the target point for delegated work, such as `draft`, `review_candidate`, `approved_enhancement`, `assembly`, or a user-defined point.
- `output_language`: `ko`, `en`, `mixed`, or `undecided`. Do not draft while this remains `undecided`.
- `language_decision_basis`: `user_request`, `target_reader`, `distribution_market`, `source_material`, or `user_confirmed`.
- `language_confirmation_required`: `yes` or `no`. Use `yes` before drafting when language choice affects external sharing, investors, partners, legal/regulatory, securities, jurisdiction, or distribution-market risk.
- `language_variant`: `ko-KR`, `en-US`, `en-GB`, `other`, or `undecided`.
- `target_jurisdiction`: jurisdiction to consider when relevant; language guidance does not create jurisdiction-specific legal advice.
- `distribution_market`: market or audience region when relevant.
- `style_profile`: selected style profile id, or `undecided` when the user has not chosen a reader tone.
- `target_reader_tone`: short description of the expected tone for the reader and use case.
- `register_overlay`: selected Korean register overlay id, `none`, `section_specific`, or `undecided`. This is a delivery-mode layer over the selected style profile, not a separate reader profile.
- `register_overlay_need`: `yes`, `no`, or `conditional`.
- `honorific_policy`: `default_off`, `conditional_review`, `not_applicable`, or `undecided`. 압존법 must not be enabled by default.
- `user_instructional_overlay`: `yes`, `no`, `conditional`, or `undecided`.
- `protected_spans_policy`: how tone/style changes must preserve direct quotes, numbers, statutes, proper nouns, citation locators, and source-backed claims.
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
- `citation_display_language`: `ko`, `en`, or `mixed`.
- `caption_label_profile`: `ko_default`, `en_default`, or `custom`.
- `disclaimer_profile`: guidance only. Do not auto-generate legal, securities, jurisdiction, or regulatory disclaimer text.
- `claim_handling`: how facts, interpretations, estimates, and unresolved issues are tracked.
- `style_profile_claim_boundary`: confirmation that style profile guidance does not verify source truth, claim readiness, citation accuracy, legal correctness, or evidence sufficiency.
- `data_and_chart_plan`: expected tables, charts, source datasets, and appendix chart packs.
- `appendix_plan`: expected glossary, source captures, detailed tables, matrices, and methodology notes.
- `reader_visible_metadata`: what metadata may appear in the rendered report.
- `hidden_or_managed_metadata`: what belongs in PRD, worklog, source index, claim register, data files, or HTML comments.
- `output_format`: working format and future conversion requirements.
- `target_document_format`: `HTML`, `DOCX`, `HWPX-compatible HTML`, `PDF`, `mixed`, or `undecided`.
- `target_format_basis`: why the target format matters and what verification method is expected.
- `design_document`: path to the report-specific design file, normally `reports/report_design.md`.
- `cover_module_plan`: which cover modules are needed for this artifact: classification badge, report type, title/subtitle, metadata table, approval cells, purpose note, confidentiality tag/notice, contact/release status, version marker, or light title header.
- `style_pass_required`: `yes`, `no`, or `conditional`. Use `yes` for substantial reports, external-facing documents, investor/partner/public documents, or any report where tone/reader-fit is material.
- `style_pass_timing`: normally `pre_assembly_after_chapter0`. Do not place the main expression correction pass before chapter drafting is stable.
- `style_pass_artifact_dir`: normally `reports/style_pass/`.
- `style_pass_register_trace`: where register/honorific/user-instructional checks are recorded inside the style-pass artifact set. Normally this is `style_risk_findings`, `protected_spans`, `style_rewrite_diff`, `style_fidelity_review`, and `style_naturalness_review`.
- `style_pass_tpo_checks`: reader level, artifact genre, delivery scene, protected spans, over-formality, translationese, report-like leakage into non-report artifacts, and human-review holds.
- `review_gates`: checks required before treating the report as draft/final.
- `status`: `planning`, `drafting`, `review`, `final_candidate`, `final`, or `archived`.
- `artifact_status`: `draft`, `review_candidate`, `approved`, or `archived`.
- `mode_rationale`, `skipped_or_compressed_stages`, and `specialized_preset_guidance` when `artifact_workflow_mode` differs from the preset default or is not `substantial`. Note the selected preset `stage_overlays.md` path when it drives workflow changes.
- `source_project_id`, `source_artifact_path`, `source_artifact_version`, `source_artifact_type`, `derived_artifact_goal`, `derived_artifact_reader`, `derived_artifact_expected_output`, `reuse_scope`, `new_verification_scope`, and `anti_anchoring_note` when the artifact derives from another saved artifact. The source artifact may be any document type, not only a report.
- `open_questions`: unresolved questions for the user, counsel, partners, or regulators.
- `revision_log`: dated change history.

Style profile and overlay responsibilities must stay separate in the PRD. The style profile is the reader/purpose-based writing standard. Register, honorific, and user-instructional overlays are guidance-only delivery-mode layers used by the AI during the pre-assembly style pass. They do not perform automatic rewrite, do not verify source truth, and do not override protected spans or English `language_guidance.md`.

`document_type_preset` is an internal routing id, not a reader-facing artifact label. It must match a supported `preset_id` in `_ai_system/document_presets/INDEX.json` or remain `undecided` until resolved. Do not invent ids such as `research_note` because the user used a natural-language phrase. If the user asks for a "research note", "debate brief", "seminar memo", or similar label, map it to the closest supported preset such as `general_report`, `academic_research`, `academic_paper`, or another indexed preset, and keep the natural-language label in `report_title`, `report_type`, or a reader-facing metadata field.

`authoring_structure_profile` is a document-type writing contract, not an institution persona. Use it to decide whether the artifact should be conclusion-first, bullet-first, prose-led, procedure-led, or slot-specific. Proposals usually lead with recipient need/value/scope/terms/next decision. Review opinions usually lead with opinion/conclusion and then separate facts, interpretation, effect, options, and uncertainty. Meeting minutes separate metadata, decisions, discussion, action owners, deadlines, and unresolved issues. Education, manual, and press-release artifacts each keep their own structure rather than copying a government-agency voice.

`list_style_preset` is a hierarchy/format contract, not permission to rewrite content. Use `_ai_system/document_presets/LIST_STYLE_PRESETS.md` when the document uses nested lists. The default formal outline is `I -> A -> 1 -> a`; guide documents usually use `guide_outline`, manuals/procedures use `procedure_steps`, administrative/review-opinion documents may use `administrative_outline`, and symbol-only support lists use `symbol_bullets`. Preserve original wording and order unless the PRD explicitly allows restructuring.

The expression correction system is an AI review workflow, not a Python rewrite feature. The PRD should tell the AI which TPO matters: executive scanability, learner explanation, partner professionalism, public-release discipline, procedural clarity, academic formality, or another reader context. Style-pass artifacts should show whether the selected profile and overlays were actually considered.

Content depth and execution control are AI operating guidance, not quality guarantees. They help the AI choose how much to write and when to stop, but they do not prove usefulness, truth, legal correctness, or approval readiness. Delegated mode must still end with an issue briefing that separates completed work, assumptions, failed checks, user-confirmation needs, and residual risk.

For Korean honorifics, 압존법 is `default_off`. Use `conditional_review` only when the artifact is a Korean spoken briefing, same-organization hierarchy and speaker/listener/referent relationship are known, and the change will not affect approval wording, quotes, legal/public/partner/customer wording, attribution, responsibility, or source-backed claims.

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

Document classification and confidentiality are artifact-level decisions, not project-level defaults.

- Do not store default document classification, default confidentiality, or external sharing permission in `project_profile.json`.
- Confirm `document_classification`, `confidentiality_status`, and `recipient_or_distribution` in the PRD before substantive drafting.
- If the user has not confirmed them, use the conservative working assumption `내부 검토용 / 대외비` for handling and do not claim the report is externally shareable.
- Internal formats (`내부 검토용`, `상부 보고용`, `파트너사 공유용`) should be treated as `대외비` unless the user explicitly says otherwise.
- `외부 공유용` still needs explicit confirmation of what can be shared and which source materials are excluded.

The project profile stores stable project logistics: responsible people, approval line, practitioners, external contacts, organization, and CI/logo references. It must not decide a report's sharing class.

`reports/report_registry.csv` may mirror artifact-level metadata for dashboards: artifact title, classification, confidentiality, version, stage, owner, practitioners, reviewers, latest file, PRD path, and next action. The filename is retained for compatibility, but the registry can track reports, handouts, proposals, manuals, briefs, press releases, and other document artifacts. Treat it as an artifact/version index, not as a replacement for the PRD. If the registry and PRD conflict, update the registry from the PRD or ask the user before changing the artifact's distribution status.

When a versioned artifact is created, `reports/report_registry.csv` should point to the latest versioned file or current pointer. `reports/version_history.md` should explain what changed, why the version number was chosen, and whether the artifact is still a draft, a review candidate, or approved for a defined use.

## PRD vs Report Design

The PRD defines why and for whom the report is written. The report design file defines how it looks.

PRD owns:

- purpose, reader, decision context, scope,
- output language, decision basis, language variant, jurisdiction/distribution-market question, citation display language, caption label profile, and disclaimer guidance boundary,
- document type preset, style profile, target reader tone, register overlay need, honorific policy need, user-instructional overlay need, and protected spans policy,
- style-pass requirement, timing, and artifact directory,
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
- source artifact lineage, reuse scope, or new verification scope for a derived artifact,
- artifact workflow mode, stage compression, or specialized preset guidance,
- content depth or execution control mode,
- document type preset, style profile, target reader tone, register overlay, honorific policy, user-instructional overlay, or protected spans policy,
- output language, language variant, citation display language, caption label profile, jurisdiction, distribution market, or disclaimer guidance boundary,
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
- document type preset, artifact workflow mode, style profile, target reader tone, register overlay need, honorific policy need, user-instructional overlay need, and protected spans policy are confirmed or explicitly marked unresolved.
- output language is not `undecided`, language confirmation is resolved when required, and any jurisdiction/distribution-market language risk is recorded.
- scope in/out is explicit.
- citation, data, chart, and appendix standards are defined.

Before final candidate:

- PRD status and report status match.
- visible report metadata matches `reader_visible_metadata`.
- production metadata has not leaked into the report body.
- all major scope changes are in the revision log and worklog.

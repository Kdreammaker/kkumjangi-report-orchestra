# Report PRD Template

## Report Identity

- `report_id`:
- `report_title`:
- `document_type_preset`: general_report / business_strategy / regulatory_review / academic_research / technical_design / service_planning / product_prd / extension preset id
- `authoring_structure_profile`: decision_first / proposal / review_opinion / meeting_minutes / education / manual / public_release / custom / undecided
- `authoring_structure_basis`: selected document type default / user request / source document structure / target reader / target file type / custom rationale
- `default_paragraph_mode`: bullet_first / prose_first / mixed / undecided
- `prose_preferred_slots`: background / rationale / legal-regulatory context / learning explanation / press lead / quotation / narrative summary / custom
- `list_style_preset`: formal_outline / guide_outline / procedure_steps / administrative_outline / symbol_bullets / undecided / not_applicable
- `list_style_preset_basis`: selected document preset default / user request / source document style / export target / not_applicable
- `artifact_workflow_mode`: brief / standard / substantial / specialized
- `artifact_workflow_mode_basis`: preset default / user request / evidence depth / distribution risk / selected preset stage_overlays.md
- `content_depth`: concise / standard / expanded
- `content_depth_basis`: user request / artifact purpose / reader time / evidence depth / default
- `content_depth_rule`: standard is the baseline for the chosen preset; concise targets roughly 30-60% of standard; expanded targets roughly 180-250% of standard when evidence and reader need justify it
- `execution_control_mode`: checkpointed / delegated
- `execution_control_target`: next approval gate / draft / review_candidate / approved enhancement / assembly / user-defined
- `execution_control_notes`: delegated mode proceeds to the target point but reports assumptions, unresolved issues, failed checks, and user-confirmation needs after completion
- `output_language`: ko / en / mixed / undecided
- `language_decision_basis`: user_request / target_reader / distribution_market / source_material / user_confirmed
- `language_confirmation_required`: yes / no
- `language_variant`: ko-KR / en-US / en-GB / other / undecided
- `target_jurisdiction`: if relevant
- `distribution_market`: if relevant
- `style_profile`:
- `target_reader_tone`:
- `register_overlay`: none / written_report / oral_briefing / public_written / educational_explanation / user_instructional / section_specific / undecided
- `register_overlay_need`: yes / no / conditional
- `honorific_policy`: default_off / conditional_review / not_applicable / undecided
- `user_instructional_overlay`: yes / no / conditional / undecided
- `protected_spans_policy`: direct quotes, numbers, statutes, proper nouns, source-backed claims, and citation locators must be preserved during tone adjustment
- `style_pass_required`: yes / no / conditional
- `style_pass_timing`: pre_assembly_after_chapter0
- `style_pass_artifact_dir`: reports/style_pass/
- `style_pass_register_trace`: record register/honorific/user-instructional checks in style_risk_findings, protected_spans, style_rewrite_diff, style_fidelity_review, and style_naturalness_review
- `style_pass_tpo_checks`: reader level, artifact genre, delivery scene, protected spans, over-formality, translationese, report-like leakage into non-report artifacts, and human-review holds
- `document_classification`: 내부 검토용 / 상부 보고용 / 파트너사 공유용 / 외부 공유용
- `confidentiality_status`: 대외비 / 대외비 아님
- `target_document_format`: HTML / DOCX / HWPX-compatible HTML / PDF / mixed / undecided
- `target_format_basis`: reader/use case, target app, expected verification method, and known limitations
- `recipient_or_distribution`:
- `external_sharing_allowed`: yes / no / needs_approval
- `status`:
- `version`:
- `artifact_status`: draft / review_candidate / approved / archived
- `기준일`:

## Workflow Mode

- `brief`: short artifact such as press release, announcement, memo, one-page brief, compact handout. Use only the stages needed for purpose, source integrity, review, style pass, assembly/versioning, and approval boundary.
- `standard`: structured artifact such as proposal, manual, curriculum handout, PRD, investor brief. Use PRD, outline/TOC, source/claim mapping where needed, section drafting, review, style pass, assembly/versioning.
- `substantial`: long evidence-backed report or analysis. Use the full report-factory sequence including detailed TOC, skeleton, workpacks, chapter fragments, visual/data pass, Chapter 0, style pass, assembly, and gates.
- `specialized`: selected document preset requires a different mandatory structure or approval boundary. Read only the selected preset module and document which standard stages are skipped, compressed, or replaced.
- `mode_rationale`: why this mode fits the user's purpose and artifact type
- `skipped_or_compressed_stages`: none / list with reason
- `specialized_preset_guidance`: selected preset files that must be read
- `selected_preset_workflow_guidance`: path to selected preset stage_overlays.md when it changes stage depth or section structure

## List Style Preset

- `formal_outline`: formal hierarchy using `I -> A -> 1 -> a`
- `guide_outline`: guide hierarchy using `A -> A) -> a) -> (a)`
- `procedure_steps`: procedure hierarchy using `1 -> 1) -> a) -> (a)`
- `administrative_outline`: decision-first administrative/review hierarchy using `1. -> 1) -> A. -> a)` with HWPX marker overrides recorded separately
- `symbol_bullets`: symbol-only hierarchy using `• -> ◦ -> ▪ -> -`
- `list_style_exception`: record any user-requested marker set that differs from the preset default
- `export_note`: HTML and DOCX should preserve list intent, HWPX-compatible HTML should record Hancom marker/font overrides, and Word/Google Docs/Hancom import still requires verification

## Authoring Structure

- Use document-type structure instead of institution persona imitation.
- Decision/review outputs usually open with conclusion, recommendation, requested decision, basis, risk, and next action.
- Proposal outputs usually open with recipient need, proposed value, scope, terms, risk/assumption, and next decision.
- Meeting minutes separate metadata, decisions, discussion points, action owners, deadlines, and unresolved issues.
- Education, manual, and press-release outputs keep their own slot structure; do not force report-style bullets into prose-led press releases or explanation-led learner materials.

## Content Depth And Control Mode

- `concise`: produce the same decision structure with fewer examples, shorter explanations, and tighter visuals; target about 30-60% of the standard volume, not a fixed character count.
- `standard`: default density for the selected preset and reader. Use this when the user gives no depth preference.
- `expanded`: add more explanation, examples, alternatives, caveats, and appendices only when useful evidence exists; target about 180-250% of standard, not padded prose.
- `checkpointed`: stop at explicit approval gates such as setup brief, TOC approval, or sensitive distribution decisions.
- `delegated`: continue to the requested target point when the path is clear, then brief what was assumed, what needs user confirmation, what failed, and what remains risky. Delegated mode does not bypass language, source, safety, confidentiality, external-sharing, or legal/regulatory approval boundaries.

## Source Artifact Lineage

Use this section only when the current artifact is derived from another project artifact. The source may be a report, handout, proposal, manual, brief, or any other saved artifact.

- `source_project_id`: none / project id
- `source_artifact_path`: none / project-relative path
- `source_artifact_version`: none / version id if known
- `source_artifact_type`: report / handout / proposal / manual / brief / other / unknown
- `derived_artifact_goal`: what the new artifact is meant to accomplish
- `derived_artifact_reader`: who will use the new artifact
- `derived_artifact_expected_output`: handout / proposal / manual / brief / report / press release / other
- `reuse_scope`: what may be reused from the source artifact
- `new_verification_scope`: what must be checked again for this artifact
- `inheritance_boundary`: source conclusions and source lists are context, not newly verified evidence unless rechecked
- `anti_anchoring_note`: do not preserve the source artifact's tone, structure, visuals, or conclusions when they conflict with the new purpose, reader, preset, or evidence standard

## Reader and Decision Context

- `primary_reader`:
- `secondary_reader`:
- `decision_context`:
- `business_questions`:
- `initial_questions_resolved`: yes / no / partial

## Style Profile And Overlay Boundary

- `style_profile_responsibility`: reader/purpose-based writing standard; not an automatic rewrite or evidence validation tool
- `register_overlay_responsibility`: Korean delivery-mode layer on top of the selected style profile; guidance-only for style pass
- `honorific_boundary`: 압존법 is default-off and only conditionally reviewed for Korean spoken/internal hierarchy contexts with clear speaker/listener/referent relationships
- `user_instructional_boundary`: adult procedural guidance only; not child education, marketing copy, legal drafting, or hidden humanizer
- `english_language_layer_boundary`: do not create `*_en` presets/profiles; use language_guidance.md where relevant without automatic translation/rewrite

## Scope

### Scope In

- 

### Scope Out

- 

## Working Assumptions

| Assumption | Status | Review Need | Notes |
|---|---|---|---|

## Evidence Standard

- `source_tiers_required`:
- `source_records_required`:
- `exact_links_required`:
- `user_requested_materials_path`: references/user_requested_materials.md
- `datasets_required`:
- `legal_or_expert_review_required`:

## Citation and Claim Handling

- `citation_display`:
- `citation_display_language`: ko / en / mixed
- `caption_label_profile`: ko_default / en_default / custom
- `disclaimer_profile`: guidance only, not autogenerated legal text
- `claim_register_path`:
- `source_index_path`:
- `assumption_register_path`:
- `html_comment_policy`:
- `style_profile_claim_boundary`: style profile guidance does not verify source truth, claim readiness, citation accuracy, or legal correctness

## Data, Charts, and Appendix Plan

| Item | Main Body or Appendix | Data File | Source Requirement | Notes |
|---|---|---|---|---|

## TOC Approval

- `toc_approval_required`: yes
- `toc_approval_status`: not_requested / requested / approved / waived_by_user
- `toc_review_path`:
- `approved_at_kst`:
- `approved_by`:

## Reader-Facing Metadata

Show in rendered report:

- 

Do not show in rendered report:

- 

## Output and Design Boundary

- `working_format`:
- `future_conversion`:
- `design_document`: reports/report_design.md
- `cover_preset`:
- `cover_module_plan`: classification badge / report type / title-subtitle / metadata table / approval cells / purpose note / confidentiality tag-notice / contact-release status / version marker / light title header
- `logo_priority`: report-specific override -> project brand_assets -> common CI -> blank
- `classification_display`:
- `confidential_notice_required`:

Design details such as color, font, A4 margins, cover layout, table/chart style, and confidentiality warning placement belong in `reports/report_design.md`. Keep purpose, reader, distribution, evidence bar, and conclusion strength in this PRD.

## Review Gates

| Gate | Required Check | Status | Notes |
|---|---|---|---|
| Scope | PRD and TOC aligned | not_started | |
| TOC Approval | Detailed TOC self-review and user approval completed before evidence/drafting | not_started | |
| Evidence | Source index and claim register complete | not_started | |
| Data | Tables/charts backed by data files | not_started | |
| Style Pass | Body chapters, Chapter 0, captions, and reader-fit expression checked before assembly | not_started | |
| Citation | Reader-facing citation style checked | not_started | |
| Design | HTML visual check completed | not_started | |
| Final | Production metadata not visible in report body | not_started | |

## Open Questions

| Question | Owner | Needed By | Status | Answer / Impact |
|---|---|---|---|---|

## Revision Log

| Date/KST | Version | Change Type | Changed By | Summary | Reason | Impacted Sections |
|---|---|---|---|---|---|---|

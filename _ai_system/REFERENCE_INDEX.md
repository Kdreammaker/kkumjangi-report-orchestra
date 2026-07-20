# Report Integrity Orchestrator Reference Index

This file is the detailed map for governance documents, report skills, templates, and tools. `AGENTS.md` should stay small and route here only when a detailed index is needed.

## Governance Documents

| Document | Purpose | When to read |
|---|---|---|
| `_ai_system/governance/00_workspace_overview.md` | Workspace map, root layout, project locations, validation meaning. | Choosing a project, checking folder conventions, or understanding workspace boundaries. |
| `_ai_system/governance/01_research_evidence_rules.md` | Source reliability, direct quote/summary/interpretation/estimate separation, legal/source boundaries. | Source collection, regulatory/legal analysis, foreign-language source use, or estimates. |
| `_ai_system/governance/02_report_workflow_rules.md` | Report language decision, preset/style/register flow, HTML-first format, detailed TOC, claim register, citations, tables/graphs, appendices. | Creating TOCs, writing reports, using claims, deciding output language, choosing style/register guidance, or producing report HTML. |
| `_ai_system/governance/03_question_worklog_rules.md` | Clarifying questions, durable user decisions, worklogs, scope alignment. | Asking the user questions, recording decisions, or changing scope/conclusions. |
| `_ai_system/governance/04_benchmark_review_rules.md` | Benchmark case cards and red-team review. | Building or reviewing benchmark cases. |
| `_ai_system/governance/05_chart_visualization_rules.md` | Chart type selection, visual usefulness, color/legend/label/source rules. | Creating or reviewing charts, diagrams, timelines, graph packs, or visual captions. |
| `_ai_system/governance/06_report_prd_rules.md` | Report PRD/brief, required fields, style profile/register overlay decisions, revision log, boundary with design metadata. | Starting or revising report purpose, audience, classification, scope, evidence bar, style/register choices, or output format. |
| `_ai_system/governance/07_ai_snapshot_change_detection_rules.md` | AI snapshot and manual-edit detection. | Before/after material file edits. |
| `_ai_system/governance/08_reference_intake_rules.md` | File/URL intake, original-file ledger, Docling/DuckDB derived artifacts, user data harness. | User-provided files/URLs, document ledger work, reference normalization, or source-register repair. |
| `_ai_system/governance/09_workspace_setup_and_migration_rules.md` | Install, migration, project initialization, dashboard, OJT, and A-to-Z setup flow. | New PC setup, workspace repair, new project creation, OJT updates, or full-flow orchestration. |
| `_ai_system/governance/10_research_quality_gate_rules.md` | Source readiness, claim readiness, citation gate, report stage labels, tone gate. | Citing sources, promoting facts, drafting conclusions, or calling work evidence-backed. |
| `_ai_system/governance/11_gate_based_execution_rules.md` | Allowed/blocked actions by stage. | Stage transitions, drafting beyond scaffold, or status claims. |
| `_ai_system/governance/12_report_quality_scoring_rules.md` | Advisory scoring, hard blockers, score-lift opportunities. | Reviewing report quality or explaining current level/quality limits. |
| `_ai_system/governance/13_report_factory_rules.md` | End-to-end Report Factory production flow, assembly, hooks/skills boundary, status reporting. | Running or auditing substantial report production. |
| `_ai_system/governance/14_chapter_workpack_rules.md` | Chapter workpack standard and chapter-level writing structure. | Drafting or revising substantial chapter fragments. |
| `_ai_system/governance/15_export_conversion_rules.md` | DOCX/PDF conversion statuses and verification evidence. | Exporting or claiming conversion readiness. |
| `_ai_system/governance/16_system_core_packaging_rules.md` | GitHub/ZIP/new-PC package boundaries and release hygiene. | Packaging, publishing, or pushing system-core changes. |
| `_ai_system/governance/17_document_adaptation_rules.md` | Existing document refinement, format adaptation, file-type conversion, and derived-artifact intake. | Polishing or adapting an existing file into a target format, template, reader style, file type, or new artifact. |

## Report Skills

| Skill | Path | Use |
|---|---|---|
| Decision Interviewer | `_ai_system/report_skills/decision_interviewer/SKILL.md` | Short scope/strategy/risk interview before PRD, TOC, skeleton, or final synthesis when direction is ambiguous. |
| Source Collector | `_ai_system/report_skills/source_collector/SKILL.md` | Source collection and source-record work when evidence is needed. |
| Report Architect | `_ai_system/report_skills/report_architect/SKILL.md` | PRD/TOC/skeleton architecture and report structure. |
| Chapter Writer | `_ai_system/report_skills/chapter_writer/SKILL.md` | Chapter fragment drafting/revision from workpacks and compact context. |
| Visual Designer | `_ai_system/report_skills/visual_designer/SKILL.md` | Visual intent and report layout/design review. |
| Chart Builder | `_ai_system/report_skills/chart_builder/SKILL.md` | Concrete chart/table/diagram data files and report-ready fragments. |
| Report Assembler | `_ai_system/report_skills/report_assembler/SKILL.md` | Assembly and Chapter 0 integration without rewriting source fragments. |
| Report Reviewer | `_ai_system/report_skills/report_reviewer/SKILL.md` | Independent report/chapter quality review and revision guidance. |
| Export Operator | `_ai_system/report_skills/export_operator/SKILL.md` | DOCX/PDF export workflows and verification. |
| Document Adapter | `_ai_system/report_skills/document_adapter/SKILL.md` | Preserve and adapt an existing document into a requested format, file type, reader fit, or derived artifact before routing to reports/export when needed. |
| Cloud Platform Bridge | `_ai_system/report_skills/cloud_platform_bridge/SKILL.md` | Local outbox and approval-gated cloud handoff planning. |

## Core Templates And Design

| Item | Path | Use |
|---|---|---|
| Design document | `_ai_system/DESIGN_DOCUMENT.md` | Korean writing style, report design, A4/HTML-first layout, typography, colors, tables/charts. |
| Current task template | `_ai_system/templates/current_task_template.md` | New project task manifest and read-budget structure. |
| Source record template | `_ai_system/templates/source_record_template.md` | Source-record fields and quote/paraphrase/inference separation. |
| Claim register template | `_ai_system/templates/report_claim_register_template.md` | Claim fields, citation type, and support status. |
| Visual plan template | `_ai_system/templates/visual_plan_template.csv` | Visual rows and data artifact planning. |
| Visual review checklist | `_ai_system/templates/report_visual_review.md` | Human/AI visual pass checklist after body chapters. |
| Document adaptation plan | `_ai_system/templates/document_adaptation_plan_template.md` | Plan template for existing-document adaptation, protected spans, target output, and verification. |
| Document adaptation manifest | `_ai_system/templates/document_adaptation_manifest_template.json` | Machine-readable manifest shape for source preservation, requested mode, outputs, and verification status. |
| Report HTML templates | `_ai_system/templates/report_html/` | Reusable cover/body/page shell and report styling. |
| Cover component guide | `_ai_system/templates/report_html/cover/README.md` | Cover presets and cover-data validation. |
| Embedded owned HWP/HWPX engine | `_ai_system/engines/owned_hwp_hwpx/` | Distributed system-core HWP-to-HWPX, controlled authoring HTML/HWPX, Document IR, writer, validation, and import provenance. |
| Report Export IR and native HWPX exporter | `_ai_system/tools/report_export_ir.py`, `_ai_system/tools/export_report_hwpx.py` | Normalize Report Factory cover/chapter sources before native HWPX creation and semantic round-trip validation. |

## Document Preset Modules

| Item | Path | Use |
|---|---|---|
| Preset index | `_ai_system/document_presets/INDEX.json` | Compact routing index for base, extension, and hold document preset candidates. |
| Preset codemap | `_ai_system/document_presets/CODEMAP.md` | Human-readable map for choosing which preset files to read without opening every module. |
| List style presets | `_ai_system/document_presets/LIST_STYLE_PRESETS.md` and `_ai_system/document_presets/list_style_presets.json` | Multi-level list marker contract for formal outlines, guide outlines, procedure steps, and symbol-only bullets across HTML and DOCX export paths. |
| Preset modules | `_ai_system/document_presets/<preset_id>/` | Per-preset PRD questions, stage overlays, `design_patterns.md`, optional `language_guidance.md`, validation checklists, layout standards, and DOCX export-readiness guidance; extension modules may be guidance-only before workflow/tool automation is added. |

Read `_ai_system/document_presets/INDEX.json` first when the user names a document type, asks for a new kind of output, or the interview/PRD stage must choose `document_type_preset`. Use its `default_artifact_workflow_mode` and `read_for_workflow` fields to decide whether the selected artifact should use full report stages or a compressed/specialized sequence. Read `CODEMAP.md` only when the compact index is not enough, then read only the selected preset's current-stage files and `stage_overlays.md` when workflow depth is being decided. Read `LIST_STYLE_PRESETS.md` when nested numbered/bulleted hierarchy matters. When `output_language` is `en` or `mixed`, include the selected preset's `language_guidance.md` if present; do not create a `*_en` preset or enable translation.

## Style Profile Modules

| Item | Path | Use |
|---|---|---|
| Style profile overview | `_ai_system/style_profiles/README.md` | Guidance-only contract for reader- and purpose-specific tone calibration, protected spans, and limited rewrite review. |
| Style profile index | `_ai_system/style_profiles/INDEX.json` | Compact routing index for supported style profiles, executable aliases, descriptive routing cues, ambiguity prompts, and recommended document preset pairings. |
| Style profile codemap | `_ai_system/style_profiles/CODEMAP.md` | Human-readable map for choosing which style profile files to read without opening every module. |
| Style profile route examples | `_ai_system/style_profiles/ROUTE_EXAMPLES.md` | Descriptive-query examples, collision notes, cue-routing checks, and ask-when-ambiguous behavior. |
| Style profile modules | `_ai_system/style_profiles/<profile_id>/` | Per-profile `profile.json`, tone rules, forbidden patterns, rewrite protocol, examples, and optional `language_guidance.md`. Use for PRD/review/limited rewrite guidance only; no automatic rewrite or workflow automation is provided. |
| Register overlays | `_ai_system/style_profiles/register_overlays/` | Guidance-only Korean delivery-mode overlays layered over a selected style profile, including written report, oral briefing, public written copy, educational explanation, adult user instruction, and conditional honorific/압존법 policy. |

Read `_ai_system/style_profiles/INDEX.json` first when the user asks for a specific tone, the reader/use case implies a tone choice, or the PRD must choose `style_profile` / `target_reader_tone`. Read `CODEMAP.md` only when the compact index is not enough; read `ROUTE_EXAMPLES.md` when a descriptive request overlaps profiles or document presets, then read only the selected profile's current-stage files. Use `_ai_system/tools/query_style_profile.py` for alias-first routing, cue scoring, ambiguous returns, and overlay candidates when the choice is unclear. When `output_language` is `en` or `mixed`, include profile `language_guidance.md` if present. Language choice belongs in new-project/interview/PRD work before drafting; the expression-correction style pass belongs after body chapters, visual captions, and Chapter 0 are stable, but before assembly. A style profile is a protected writing aid, not an automatic polish tool: it must preserve direct quotes, numbers, statutes, proper nouns, source-backed claims, approval/contract/public wording, citation locators, and evidence wording unless a deliberate source/claim correction is recorded.

Register, honorific, and user-instructional overlays are separate from style profiles. A style profile answers reader/purpose fit; a register overlay answers Korean delivery mode. Use `_ai_system/tools/query_style_profile.py` to surface overlay candidates when the query is 말투/높임말/절차 안내 중심, but do not treat those candidates as selected profiles. Read `_ai_system/style_profiles/register_overlays/README.md` only when that layer may be needed, then read the selected overlay file only. These overlays are guidance-only for AI style-pass judgment. 압존법 is default-off and should be considered only for special Korean spoken/internal hierarchy contexts; public, partner, legal, approval-sensitive, quote-sensitive, mixed-organization, and ordinary written-report contexts should preserve neutral names/titles or hold for review.

Use `_ai_system/tools/validate_style_profiles.py` to verify aliases, `read_first` files, profile metadata, `automation_status=guidance_only`, language guidance paths, codemap presence, and protected span coverage.

## Main Tools

| Tool | Path | Use |
|---|---|---|
| Runtime dependency installer | `_ai_system/tools/install_runtime_dependencies.py` | Install/verify Python packages and local ECharts/Pretendard runtime assets. |
| Local runtime validator | `_ai_system/tools/validate_local_runtime.py` | Check Python, pypdf, Docling, DuckDB, python-docx, ECharts, and Pretendard. |
| Workspace bootstrap | `_ai_system/tools/bootstrap_workspace.py` | Create initial `00_사용자_작업공간/` if absent. |
| Workspace validator | `_ai_system/tools/validate_workspace_setup.py` | Validate root, runtime, projects, HTML, API/UI flow, snapshots, and local leftovers. |
| Core worktree guard | `_ai_system/tools/validate_core_worktree_clean.py` | Detect accidental system-core edits during ordinary project/report workflows. |
| Project initializer | `_ai_system/tools/init_project_workspace.py` | Create a new project foundation after user approval. |
| Current task validator | `_ai_system/tools/validate_current_task.py` | Validate `tasks/current_task.md` and refresh `task_status.html`. |
| Stage context composer | `_ai_system/tools/compose_report_context.py` | Produce stage-specific read lists and `context_packets/*.compact.md`; `--output-language en|mixed` adds selected language guidance without translation/rewrite automation. |
| Document preset query | `_ai_system/tools/query_document_preset.py` | Resolve a document-type query to preset read guidance, design assets, language guidance, or unsupported hold candidates without enabling workflow automation. |
| Document preset validator | `_ai_system/tools/validate_document_presets.py` | Validate preset module files, list style preset contracts, design-stage read guidance, language guidance paths, module-only boundaries, and hold-candidate routing. |
| Style profile query | `_ai_system/tools/query_style_profile.py` | Resolve a reader-tone/style query to guidance-only profile files and optional language guidance while explicitly keeping rewrite automation disabled. |
| Style profile validator | `_ai_system/tools/validate_style_profiles.py` | Validate style profile aliases, `read_first` paths, language guidance paths, module files, profile id alignment, guidance-only status, query routing, and protected span policy coverage. |
| Workflow navigator | `_ai_system/tools/report_workflow_next.py` | Suggest next production action, blockers, and status panel. |
| Artifact version finalizer | `_ai_system/tools/finalize_artifact_version.py` | Preserve a versioned artifact and update `report_registry.csv`, `version_history.md`, `version_pointer.json`, and dashboard change logs. |
| Gate status | `_ai_system/tools/report_gate_status.py` | Compute current report/project gate and blocked actions. |
| Guarded step runner | `_ai_system/tools/run_guarded_step.py` | Run bundled gate chains for drafting, review-candidate, closeout, export, handoff, or workspace checks. Review/closeout/handoff include the core worktree guard. |
| Reference intake batch | `_ai_system/tools/intake_reference_batch.py` | Register source files, preserve originals, normalize with Docling/PDF parsing where available. |
| Project context DB builder | `_ai_system/tools/build_project_context_db.py` | Build DuckDB context index from references, normalized units, source records, claims, and workpacks. |
| Project context query | `_ai_system/tools/query_project_context.py` | Query targeted snippets instead of reading full originals. |
| Source link recorder | `_ai_system/tools/record_source_link.py` | Record exact official URLs, source locators, use level, and user-file request status. |
| Source quote verifier | `_ai_system/tools/verify_source_link_quotes.py` | Optional manual audit helper for fetched/captured source text; not part of the default report workflow. |
| Source status panel | `_ai_system/tools/build_source_status_panel.py` | Build source/link status panels for non-technical review. |
| Reference consistency validator | `_ai_system/tools/validate_reference_register_consistency.py` | Check reference inventory, source link register, source index, and source records agree. |
| Research integrity validator | `_ai_system/tools/validate_research_integrity.py` | Check source, claim, citation, and tone risks. |
| Report preflight | `_ai_system/tools/report_preflight.py` | Check PRD, TOC, stage, sources, and claims before drafting/delivery. |
| Skeleton scorer | `_ai_system/tools/report_skeleton_score.py` | Advisory skeleton completeness check. |
| Chapter quality coach | `_ai_system/tools/report_chapter_quality_coach.py` | Hook that detects missing/weak chapter signals and required AI action. |
| Visual plan suggester | `_ai_system/tools/suggest_visual_plan.py` | Optional prompt generator for candidate visuals. |
| Visual pass finalizer | `_ai_system/tools/finalize_visual_pass.py` | Hash/status helper after visual review. |
| Cover render validator | `_ai_system/tools/validate_cover_render.py` | Validate `cover.data.json` and optionally write cover preview. |
| Report assembler | `_ai_system/tools/assemble_report.py` | Concatenate reusable cover and chapter fragments without rewriting prose. |
| Report factory validator | `_ai_system/tools/validate_report_factory.py` | Check PRD, TOC, skeleton, workpacks, chapter fragments, cover, visuals, and assembly readiness. |
| Report artifact validator | `_ai_system/tools/validate_report_artifact.py` | Check rendered HTML structure, citations, captions, internal leakage, and tone risk. |
| Quality score | `_ai_system/tools/report_quality_score.py` | Advisory score/status panel with hard-blocker caps. |
| Native DOCX exporter | `_ai_system/tools/export_report_docx.py` | Create a Word-native DOCX from report factory sources and optionally write render evidence. |
| Export artifact validator | `_ai_system/tools/validate_export_artifact.py` | Verify DOCX/PDF export evidence. |
| Document adaptation initializer | `_ai_system/tools/init_document_adaptation.py` | Preserve an existing source file and write a document adaptation plan/manifest before editing or converting. |
| Closeout validator | `_ai_system/tools/validate_closeout.py` | Check declared deliverables, snapshots, and active report folders. |
| Delivery outbox builder | `_ai_system/tools/build_delivery_outbox.py` | Build local handoff package without cloud upload. |
| Cloud handoff planner | `_ai_system/tools/prepare_cloud_handoff.py` | Create approval-gated cloud upload plan; does not upload by itself. |
| Workspace configurator | `_ai_system/tools/configure_workspace.py` | List/change domain preset safely. |

## Smoke Tests

Smoke scripts under `_ai_system/tools/smoke_*.py` are developer release tests, not ordinary report-production steps. The most relevant system-core checks are:

- `_ai_system/tools/smoke_context_composer.py`
- `_ai_system/tools/smoke_english_language_layer.py`
- `_ai_system/tools/smoke_report_workflow_next.py`
- `_ai_system/tools/smoke_report_skills_and_hooks.py`
- `_ai_system/tools/smoke_reference_register_consistency.py`
- `_ai_system/tools/smoke_report_chapter_quality_coach.py`
- `_ai_system/tools/smoke_project_dashboard_app.py`
- `_ai_system/tools/smoke_cover_render.py`
- `_ai_system/tools/smoke_delivery_outbox.py`
- `_ai_system/tools/smoke_document_adaptation.py`

## Notes On Legacy Mentions

Legacy references are allowed when they support migration, validation, or explicit "do not generate this old artifact" rules. They should not appear in ordinary OJT prompts or new-project user-facing instructions.

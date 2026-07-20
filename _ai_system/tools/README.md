# Python Tool Boundary

This folder contains small local helpers. They are not the report-writing system itself.

The system objective is better AI-written reports. Rules, skills, PRDs, TOCs, chapter workpacks, source records, and human/AI review carry the judgment work. Python tools should be used only when the job is deterministic enough that code is safer than prose.

## Use Python For

- workspace bootstrap and routing,
- source file intake, URL/link status recording, and quote checks,
- local reference normalization and rebuildable context indexing,
- exact file assembly without rewriting chapter prose,
- native DOCX export from stable report factory sources,
- HWP-to-HWPX conversion through the embedded owned engine,
- controlled HWPX authoring HTML conversion through the embedded owned engine,
- snapshot/hash comparison,
- export/outbox packaging,
- structural validation and smoke tests for system releases.

## Prefer Rules Or Skills For

- deciding whether an argument is strong,
- deciding whether a chart is useful,
- interpreting law, policy, market meaning, or strategy,
- judging writing depth and tone,
- deciding whether a report is persuasive for its intended reader.

Score or coach tools may create useful status panels, but they must not become writing targets. In guarded review/closeout chains they are used as routing and contradiction checks: they can block false readiness, but they cannot certify that analysis is persuasive.

Local Python cannot directly invoke Codex/AI skills. A hook can only write a clear `required_ai_action`, set `skill_action_required`, and fail the guarded step. The AI must then follow the named skill workflow and rerun the hook.

Do not run tools just to create a sense of progress. During ordinary report production, use the current `tasks/current_task.md` row to decide the next small set of tools. Developer smoke tests, package checks, and broad workspace checks are for install, release, repair, or closeout, not for every chapter.

If the same validator fails twice with the same blocker and no underlying production artifact has changed, stop rerunning it. Record the blocker in the worklog and move to the repair action named by the active task or validator output.

## Operational Tools

Default operational tools are the tools an AI may normally use during setup, report production, or closeout:

- `assemble_report.py`
- `export_report_docx.py`
- `export_report_hwpx.py`
- `report_export_ir.py`
- `smoke_report_hwpx_export.py`
- `bootstrap_workspace.py`
- `build_delivery_outbox.py`
- `build_project_context_db.py`
- `build_source_status_panel.py`
- `check_system_version.py`
- `compose_report_context.py`
- `configure_workspace.py`
- `convert_hwp_to_hwpx.py`
- `convert_html_hwpx.py`
- `finalize_visual_pass.py`
- `init_project_workspace.py`
- `install_runtime_dependencies.py`
- `intake_reference_batch.py`
- `prepare_cloud_handoff.py`
- `record_source_link.py`
- `report_factory_migration_plan.py`
- `report_gate_status.py`
- `report_preflight.py`
- `report_skeleton_score.py`
- `report_workflow_next.py`
- `resolve_workspace_preset.py`
- `run_guarded_step.py`
- `update_ai_snapshots.py`
- `validate_closeout.py`
- `validate_cover_render.py`
- `validate_current_task.py`
- `validate_export_artifact.py`
- `validate_local_runtime.py`
- `validate_reference_register_consistency.py`
- `validate_report_artifact.py`
- `validate_report_factory.py`
- `validate_research_integrity.py`
- `validate_workspace_setup.py`
- `verify_source_link_quotes.py`
- `workspace_config.py`

`intake_reference_batch.py` may use Docling to create derived normalized files under `references/normalized/`. Those files are not originals. `build_project_context_db.py` may use DuckDB to build `project_state/context_index.duckdb`, a local cache that can be rebuilt from project files.

`convert_hwp_to_hwpx.py` calls the embedded owned engine under `_ai_system/engines/owned_hwp_hwpx/`. It needs no external CLI environment variable. The imported engine snapshot is maintained independently in Report Orchestra after import; the source repository is not a runtime dependency.

`convert_html_hwpx.py` is the matching embedded entrypoint for `hwpx-to-html` or `html-to-hwpx`. Only the controlled
`hwpx-authoring-html.v1` contract is supported; ordinary report HTML and
DOCX-compatible HTML are not silently accepted.

`report_export_ir.py` normalizes Report Factory cover and chapter sources into `report_export_ir.v1`. `export_report_hwpx.py` renders that bounded model into the owned Document IR/HWPX path and checks native package structure plus text, section, resource, table, image, and list round-trip parity. It does not claim Hancom visual identity without a separate native open/render review.

Document preset and style profile routing should use compact indexes before opening module folders: `_ai_system/document_presets/INDEX.json`, `_ai_system/document_presets/CODEMAP.md`, `_ai_system/style_profiles/INDEX.json`, and `_ai_system/style_profiles/CODEMAP.md`. These indexes reduce read cost, but they do not replace the selected module's source files when a PRD, stage overlay, or style pass needs them. `query_document_preset.py` exposes `default_artifact_workflow_mode` and `workflow_assets` so AI can read the selected preset's `stage_overlays.md` before compressing or replacing stages; it does not automate writing quality or document approval.

`query_style_profile.py` resolves exact profile aliases first, then uses style-profile cue scoring from `_ai_system/style_profiles/INDEX.json` and `ROUTE_EXAMPLES.md`; when cue confidence is low, close, or register/honorific/user-instructional-only, it returns `ambiguous` with candidates and a short confirmation question instead of selecting a profile. Its payload must keep `automation_status=guidance_only` and `rewrite_automation=not_enabled`.

The project dashboard owns user-facing project profile, report registry, document ledger, and change-log editing. Do not recreate the removed standalone `reference_library_app` or a separate per-project `reference_library/` launcher for new active projects. The old `cover_renderer.py` path was also removed; cover output is produced through the reusable cover component and validated by `validate_cover_render.py`.

## Routing / Advisory Tools

These tools are allowed as advisory panels and may also be called by guarded chains when their signals are needed to prevent false readiness:

- `report_chapter_quality_coach.py`
- `report_quality_score.py`
- `suggest_visual_plan.py`

`report_chapter_quality_coach.py` is a routing hook. If it says `needs_attention`, the AI must run a chapter review/revision action; Python has not judged the final quality of the prose.

`report_quality_score.py` is a contradiction detector. It caps levels when live chapter hooks, cover render, strict factory/artifact checks, or stage manifests disagree with a readiness claim. It still does not judge legal analysis, business feasibility, or executive persuasiveness.

`validate_reference_register_consistency.py` checks whether `reference_inventory.csv`, `source_link_register.csv`, `source_master_index.md`, and `source_records/*.md` are describing the same sources. It is a source-ledger consistency check, not proof that the source is true or that the report analysis is strong. Normal URL source handling is link-first: exact official URL, access date, source locator, and use level. URL fetch/capture helpers are optional manual audit tools, not ordinary production gates.

If any routing/advisory output conflicts with the PRD, chapter workpack, or substantive AI review, resolve the contradiction before reporting readiness.

## Smoke Tests

Files named `smoke_*.py` are developer release tests for this system core. They are not part of ordinary user operation, OJT, or report production. Run them after changing system tools, skills, package boundaries, or release behavior; otherwise prefer the narrow validator named by the active task.

`smoke_english_language_layer.py` verifies that English output uses the same document presets and style profiles with `language_guidance.md` layered in only for `en` or `mixed`, validates synthetic English fixtures, blocks English labels in Korean/unmarked reports, and keeps automatic translation/rewrite/disclaimer generation disabled.

Private maintainer release helpers should live outside this user-facing tools folder. In particular, public/private package builders, package-boundary validators, and release-only smoke tests should stay out of ordinary report-production tools so they are not mistaken for user operations.

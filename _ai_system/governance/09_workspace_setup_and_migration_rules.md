# Workspace Setup and Migration Rules

## Purpose

Use this file when setting up the workspace on a new PC, creating a new project, repairing moved paths, or running a report workflow from start to finish.

`AGENTS.md` remains the root AI entry point. It is intentionally AI-service-agnostic: Codex, Claude, Antigravity, or another AI assistant should read it as the routing index before loading detailed rules. Detailed AI operating files live under `_ai_system/`.

## Workspace Boundary

Human-facing entry points:

- `README.md`: first landing document for GitHub/ZIP users.
- `INSTALL.md`: installation and first-run setup guide.
- `START_HERE.html`: user OJT and operating manual.
- `00_사용자_작업공간/`: active project folders.
- `00_사용자_작업공간/<project>/프로젝트_대시보드_실행.vbs`: primary user launcher for the local project dashboard app.
- `00_사용자_작업공간/<project>/01_자료_넣는_곳/`: project-specific user drop zone.
- `00_사용자_작업공간/<project>/references/reference_inventory.csv`: original-file/document ledger managed through the project dashboard.

AI-facing operating area:

- `_ai_system/governance/`: rules loaded through `AGENTS.md`.
- `_ai_system/tools/`: scripts and local apps.
- `_ai_system/templates/`: reusable source, report, claim, and register templates.
- `_ai_system/`: workspace-level governance, tools, templates, design systems, and system design notes.
- `_ai_system/environment/`: package, runtime, and new-PC setup notes.
- `_ai_system/runtime/`: transient or tool-created runtime artifacts that should not clutter the root.
- `_ai_system/project_state/`: workspace-level AI snapshots and operational state.
- `_ai_system/base_reference/`: common design/reference assets.

Project research artifacts remain under `00_사용자_작업공간/<project>/`.

The workspace root should stay simple:

- `README.md`
- `INSTALL.md`
- `START_HERE.html`
- `AGENTS.md`
- `VERSION.json`
- `CHANGELOG.md`
- `LICENSE`
- `docs/`
- `.github` when GitHub issue templates are included
- `.git` when the workspace is a Git clone
- `.gitignore` when the workspace is a GitHub/ZIP system-core package
- `00_사용자_작업공간/`
- `_ai_system/`

If an AI tool recreates a root runtime folder such as `.playwright-mcp`, move it after use into `_ai_system/runtime/playwright-mcp/` and record the action in the worklog. Do not expose tool runtime folders as user-facing work areas.

## New PC Setup Flow

1. Open the workspace root folder in the AI service.
2. If this is a fresh GitHub/ZIP install, read `INSTALL.md`, run `_ai_system/tools/install_runtime_dependencies.py`, then run `_ai_system/tools/bootstrap_workspace.py` before full workspace validation.
3. Ask the AI to read `AGENTS.md`.
4. Ask the AI to follow `_ai_system/governance/09_workspace_setup_and_migration_rules.md`.
5. Ask the AI to verify:
   - `_ai_system/governance/` exists,
   - `_ai_system/tools/project_dashboard_app/app.py` exists,
   - `START_HERE.html` exists,
   - `00_사용자_작업공간/` exists,
   - each active project, if any, has `프로젝트_대시보드_실행.vbs` and `project_dashboard/open_project_dashboard.bat`,
   - each active project, if any, has `01_자료_넣는_곳/`,
   - each active project has a working dashboard document-ledger page.
6. Run the validation commands or equivalent checks recorded in the active worklog.

Do not assume previous absolute paths are still valid on a new PC. Prefer paths relative to the workspace root.

Recheck/update requests are not fresh-install proof. If a Git checkout is available, the AI may compare local `VERSION.json`/HEAD with `origin/main`, but it may pull only when `origin` matches the installed release channel/repository, the system-core worktree has no local changes, and the update can fast-forward. If the workspace is a ZIP install, has an unexpected origin, has local system-core changes, has conflicts, or is ambiguous, do not update; report the state and ask for user direction. Do not use `git restore`, hard reset, or destructive repair to make a recheck look clean unless the user explicitly requested that operation.

Use `_ai_system/tools/validate_workspace_setup.py --include-user-flow` for repeatable full validation where possible. Validation must suppress browser auto-open by using the dashboard app's silent mode or `PROJECT_DASHBOARD_NO_BROWSER=1`; opening the user's browser is reserved for explicit visual/browser checks. A manual check is acceptable only when the AI service cannot run local scripts; in that case the final report must state which checks were skipped.

Report workspace validation as environment/structure validation. Do not call it document content validation, source verification, legal review, citation validation, or external sharing approval. If no active project artifact was inspected, say project artifact/content validation was `not_run`.

## Setup Validation Scope

A setup check is not complete unless it covers all of the following categories:

1. Root layout:
   - root contains only `README.md`, `INSTALL.md`, `START_HERE.html`, `AGENTS.md`, `VERSION.json`, `CHANGELOG.md`, `LICENSE`, `docs/`, optional `.github/`, optional `.git`/`.gitignore`, `00_사용자_작업공간/`, and `_ai_system/`,
   - root has no `.playwright-mcp`, `projects/`, `__pycache__`, or other runtime clutter.
2. Project required files:
   - each active project has all standard folders and ledgers,
   - `reports/report_claim_register.md` exists even when a project also has report-specific claim registers.
3. Launchers:
   - each project has `프로젝트_대시보드_실행.vbs`,
   - each project has `project_dashboard/open_project_dashboard.bat`,
   - dashboard launcher paths resolve to `_ai_system/tools/project_dashboard_app/app.py` by relative path,
4. Reference library:
   - Level 1 API check: start the local project dashboard app with `--no-browser` and report the reference count by project,
   - Level 2 launcher check: execute each project's `프로젝트_대시보드_실행.vbs` in silent validation mode and confirm it starts the local dashboard app,
   - Level 3 browser UI check: open the dashboard document-ledger page and confirm the page renders the reference inventory table,
   - the default target is Level 1 through Level 3 for each active project,
   - if the AI service cannot execute VBS/BAT or cannot control/render a browser, classify the item as `blocked / not tested`, state the exact reason, and do not report the setup as fully user-flow verified.
   - `_ai_system/tools/validate_workspace_setup.py --include-user-flow` covers Level 1, Level 2, and served UI HTML checks without opening the browser. If a real browser automation tool is available and visual inspection is explicitly needed, additionally open at least one active reference-library URL in the browser and visually confirm the rendered UI. If a browser tool is unavailable, explicitly report that visual rendering was not tool-verified.
5. HTML:
   - separately count user-facing HTML, report HTML, and evidence/web-capture HTML,
   - state the category counts in the result,
   - do not report a single ambiguous page count.
6. Environment:
   - verify Python,
   - verify packages listed in `_ai_system/environment/requirements.txt`,
   - distinguish current required packages from optional future OCR/browser/rendering tools.
7. Portability:
   - scan active rules, OJT, tools, PRDs, notes, and worklogs for local absolute paths,
   - normalize active operational documents to workspace-relative paths,
   - if a historical worklog keeps an absolute path for audit reasons, explicitly label it as historical.
8. Snapshot state:
   - validate all latest AI snapshot manifests,
   - report missing snapshots, hash mismatches, and invalid manifest rows.
9. Process cleanup:
   - stop validation-only local servers,
   - remove `__pycache__` folders created by validation,
   - move root runtime artifacts into `_ai_system/runtime/`.

When reporting validation results, separate:

- `passed`,
- `fixed during check`,
- `warning / residual risk`,
- `not tested`.

Deleting validation-created cache files is still a filesystem change. If only such cleanup occurred, say “only temporary validation artifacts were removed,” not “no file changes occurred.”

## New Project Initialization Flow

When a new project is requested:

Natural-language requests such as “새 프로젝트 시작하자”, “새 폴더 세팅해줘”, or “이 주제로 새 보고서 프로젝트 만들어줘” should be treated as a new-project setup request even when the user does not name this rule file.

Before creating files, apply the short-request confirmation flow:

1. Extract the minimum information from the user's request:
   - project name,
   - one-line purpose.
2. If either project name or purpose is missing, ask only for the missing minimum field.
3. If both are present, reconstruct a full project setup brief and ask for confirmation before creating files. The brief should include:
   - project name,
   - purpose,
   - expected final outputs,
   - default content depth,
   - execution control mode,
   - likely research scope,
   - likely project handling sensitivity,
   - initial material location,
   - additional items the user wants to confirm / assumptions,
   - default setup scope.
4. Use conservative defaults when the user did not specify details:
   - final output: internal review HTML report, unless the user says otherwise,
   - content depth: standard,
   - execution control mode: checkpointed,
   - project handling sensitivity: internal project workspace,
   - initial material location: the new project's `01_자료_넣는_곳/`,
   - additional items to confirm: none,
   - report body: not drafted during setup.
5. Do not treat a vague continuation prompt as approval when the user asked for a proposal first. Accept execution only when the user clearly approves the proposed setup, for example “승인합니다”, “이 안으로 세팅 진행”, or an equivalent direct instruction after seeing the brief.
6. After the user approves the setup brief, create `00_사용자_작업공간/<YYMMDD_project_name_20chars>/`.
7. Create the standard research folders from `_ai_system/governance/00_workspace_overview.md`.
8. Create human-facing project files:
   - `프로젝트_대시보드_실행.vbs`,
   - `project_dashboard/open_project_dashboard.bat`,
   - `01_자료_넣는_곳/`,
   - `project_profile.json`,
   - `brand_assets/`,
   - `reports/report_registry.csv`,
   - `tasks/current_task.md`,
   - `tasks/task_status.html`.
9. Create reference operating files:
   - `references/reference_inventory.csv` if missing.
10. Create or preserve:
   - `README.md`,
   - `questions/question_log.md`,
   - `reports/report_claim_register.md`,
   - `source_index/source_master_index.md`,
   - `assumptions/assumption_register.md`,
   - `project_state/report_stage_manifest.json`.
11. Record the approved setup brief, approval wording, and initialization in a timestamped worklog inside the workspace.
12. Update AI snapshots only for files the AI created or modified.
13. Run workspace validation when possible and report the result separately from any research or report quality status.
14. If `tasks/current_task.md` starts at `interview`, proceed to a short direction interview after setup unless the user asked to stop after folder creation. Do not treat this as report drafting or material intake.

Use `_ai_system/tools/init_project_workspace.py` where possible instead of hand-creating the structure. A user may provide a topic rather than a final project name. In the setup brief, propose the project display name, safe folder name, and likely first artifact title before creation. When the tool receives a bare project title/name, it must route the project directly under `00_사용자_작업공간/` using `YYMMDD_프로젝트명앞20자`, removing Windows-forbidden filename characters. A project-like folder in the workspace root is a setup failure, not a harmless extra folder.

`project_profile.json` is a project logistics file only. It may contain responsible people, approval line, practitioners, external contacts, organization, and CI/logo references. The first row in `responsible_people` is the project owner shown on the dashboard. It must not contain artifact-level default document classification, default confidentiality, or default external-sharing permission. Those are confirmed in the PRD for each artifact. Project-level logo auto-selection is fixed to `brand_assets/project_logo.png`; do not auto-select arbitrary images from the folder.

`reports/report_registry.csv` is the project-level artifact/version index. The filename is retained for compatibility, but it may track reports, handouts, proposals, manuals, briefs, press releases, and other document artifacts. It tracks artifact title, document classification, confidentiality, version, stage, owner, practitioners, reviewers, latest file, PRD path, and next action for each output. The primary editing path is the local dashboard app launched through `프로젝트_대시보드_실행.vbs`, which writes the real CSV and can open allowlisted project-internal artifact files. The PRD remains the source of truth for artifact-level purpose, audience, classification, confidentiality, evidence bar, source lineage, and verification scope; the registry is the dashboard index.

`references/reference_inventory.csv` is the original-file/document ledger and is edited through the project dashboard document-ledger page. Dashboard edits to this ledger are metadata edits only; original preservation, Docling normalization, DuckDB indexing, source-record creation, and quote verification remain AI/tool-assisted intake tasks.

New project initialization should reduce user-facing folder clutter. Do not create separate reference-library app folders or launchers for new projects; the project dashboard owns the document ledger. Hide AI/system folders in Windows Explorer by default where the OS supports it. User-facing navigation should center on `01_자료_넣는_곳/`, `reports/`, `04_공유_패키지/`, `brand_assets/`, and `프로젝트_대시보드_실행.vbs`. AI-only folders such as `tasks/`, `context_packets/`, `drafts/`, `project_state/`, `source_index/`, `evidence/`, `data_sources/`, `references/`, and `worklogs/` remain valid internal paths but should not be the default user browsing surface.

Dashboard save audit logs are unified across the three dashboard-save surfaces: project profile, artifact registry, and reference inventory. Store them at `project_state/dashboard_change_log.jsonl` for machine-readable details and `worklogs/dashboard_change_log.csv` for human-readable summaries. These logs do not track ordinary AI edits to PRD/chapter/source files or manual edits made outside the dashboard, except when the artifact version finalizer explicitly appends a version-preservation event.

The workspace-local `.local_state/device_identity.json` stores a random local device identity used only to make dashboard logs stable across network/VPN changes. It must not use hardware IDs and must be excluded from Git, packaging, delivery outboxes, and cloud/shared folders.

The approval line is ordered from highest to lower authority. Row 1 is the top approver and must appear first. Adding or deleting approval-line rows should renumber them from 1.

`tasks/current_task.md` is the project-level task manifest for AI context control. It is the first file to read when resuming an existing project task. It should contain the stage checklist, current active stage, per-stage `Read Before Work`, `Required Rules`, `Do Not Read By Default`, completion criteria, and next stage. `AGENTS.md` remains a router for missing/ambiguous task manifests or fresh setup, not the default working brief once a project task manifest exists. `tasks/task_status.html` is the static human-facing status panel regenerated by the AI after stage changes. The editable project dashboard uses a local server through `프로젝트_대시보드_실행.vbs`; do not generate a separate static dashboard for new projects.

The project dashboard should be a simple user-facing work-management control panel, not an AI operations manual and not the document-writing workspace itself. Its editable version is the local dashboard app launched through `프로젝트_대시보드_실행.vbs`. The main screen should show the project owner, artifact/document count, recent dashboard save history, simple material/artifact locations, and only the recorded current AI task from `tasks/current_task.md`. The top navigation is the primary entry point for project profile, artifact management, document ledger, and change history; do not duplicate the same actions again as a second button grid unless the design has a clear separate purpose. Do not show fake live progress, analysis depth, artifact quality, or a single project-level artifact stage when multiple artifacts can have different stages and owners. Put AI-only instructions, detailed ledgers, validation doctrine, and task manifests in OJT or `tasks/current_task.md`, not on the main dashboard.

The document-ledger page may provide user-triggered `자료 폴더 스캔` and `파싱/정규화/색인 실행` actions. Folder scan registers new material files in `references/reference_inventory.csv` by hash. Parsing/normalization/indexing may run the local reference-intake pipeline, refresh `project_state/context_index.duckdb`, write a project log under `project_state/`, and update parse/normalization/index fields. These actions are local metadata/derived-artifact operations only; they must not be reported as source truth verification, quote verification, or report-content validation.

Static HTML must not depend on buttons opening Windows Explorer or executing `.vbs/.bat`; browser security makes that unreliable. Static pages should use copy-path buttons for folders and launchers, with short guidance that the copied path can be pasted into Windows Explorer. The local dashboard app may open local folders because it runs from the user's Python process, but it must stay inside the project directory.

The local dashboard app may offer "open in Explorer" buttons only for allowlisted project-internal folders: `01_자료_넣는_곳/`, `brand_assets/`, `reports/`, and `04_공유_패키지/`. It must reject arbitrary path requests and paths outside the project directory.

The document-ledger page may provide an on-demand material-folder scan. The scan detects files under `01_자료_넣는_곳/`, records SHA256, file size, modified time, and relative path, and adds only missing files to `references/reference_inventory.csv`. This scan is not a daemon or always-on watcher. User-editable fields such as title, material origin, visibility, and notes should stay editable; system-generated fields such as hash, parse/OCR/normalization/context-index status, source linkage, and paths should be read-only badges or read-only detail values.

The local dashboard app must handle idle shutdown without closing the browser window. On shutdown it should first show a visible “세션이 종료됩니다” signal, then after the server disconnects disable all buttons and inputs and display “장시간 사용이 없어 서버가 종료되었습니다. 다시 실행 파일을 열어 주세요.” on whatever page is open.

New project initialization scope:

- Included by default:
  - project folder and standard subfolders,
  - server dashboard launcher and dashboard app bridge,
  - project logistics JSON and brand-assets folder,
  - task manifest and static task status panel,
  - drop zone and reference inventory,
  - claim/source/assumption/question ledgers,
  - `project_state/report_stage_manifest.json`,
  - initialization worklog and AI snapshots for changed files,
  - workspace validation.
- Not included by default:
  - substantive report body drafting,
  - treating collected material as verified evidence,
  - report conclusions,
  - final or internally reviewable delivery labels.
- Optional only when the user asks for report work:
  - report PRD,
  - detailed TOC,
  - source collection plan.
- Even when optional report planning is requested, substantive body drafting must wait for the report preflight and research quality gates.

## Reference Intake Flow

1. User places files in `00_사용자_작업공간/<project>/01_자료_넣는_곳/` or tells AI where the files were placed.
2. AI scans the drop zone.
3. AI copies originals into `references/inbox/<batch_id>/` and `references/received_originals/<batch_id>/`, unless a hash-identical original already exists. If a duplicate exists, reuse the canonical preserved original and record the reuse in the inventory/worklog.
4. AI inventories files in `references/reference_inventory.csv`.
5. AI generates hidden `ai_tags` at first recognition/classification/parsing.
6. AI uses Docling through `_ai_system/tools/intake_reference_batch.py` to create local derived files under `references/normalized/<reference_id>/` when the file type is supported.
7. AI runs `_ai_system/tools/build_project_context_db.py --project <project_name>` after intake when report work will use the material.
8. AI parses or marks OCR needs, but does not treat normalized output as original evidence.
9. AI updates the project worklog.
10. User opens `프로젝트_대시보드_실행.vbs` and uses the document-ledger page to review materials.

Reference intake trigger:

- The AI should scan the relevant drop zone when the user says files were added, when starting a project task, or before report work that depends on user-provided files.
- This workspace does not run an always-on folder watcher by default. “Automatic intake” means request-time scanning and processing by the AI or tools.

## Report A-to-Z Flow

1. Confirm project and output objective.
2. Load:
   - `_ai_system/governance/11_gate_based_execution_rules.md`,
   - `_ai_system/governance/06_report_prd_rules.md`,
   - `_ai_system/governance/02_report_workflow_rules.md`,
   - `_ai_system/governance/01_research_evidence_rules.md`,
   - `_ai_system/governance/10_research_quality_gate_rules.md`,
   - `_ai_system/governance/12_report_quality_scoring_rules.md`,
   - `_ai_system/DESIGN_DOCUMENT.md`.
3. Run or manually derive the current gate status:
   - `python _ai_system/tools/report_gate_status.py --project <project_name>`
   - If the tool is unavailable, manually list `allowed_actions`, `blocked_actions`, and `blockers`.
4. Create or update the report PRD under `report_prd/`.
5. Create or update the detailed TOC under `drafts/`.
6. Create or update the major skeleton / 주요 골조 under `drafts/`.
7. Score the major skeleton:
   - `python _ai_system/tools/report_skeleton_score.py --project <project_name>`
   - If the score is below 70, improve the skeleton before full-text drafting.
8. Create or update a source collection plan for broad or substantial reports.
9. Collect sources section-by-section.
10. For external sources, register exact official links before summarizing them. Do not make project progress depend on AI file-download success. If a specific source file is needed and the AI cannot obtain it, add it to `references/user_requested_materials.md` with the official link and user action needed; do not write it as collected.
11. Register sources in source records and source index.
12. Register material claims in the claim register.
13. Run report preflight before drafting beyond a scaffold:
   - `python _ai_system/tools/report_preflight.py --project <project_name> --for-drafting`
14. Apply `_ai_system/governance/10_research_quality_gate_rules.md` before treating claims as report conclusions.
15. Create chapter workpacks under `reports/chapter_workpacks/` before substantial chapter drafting.
16. Draft `.html` chapter fragments under `reports/chapters/` one chapter at a time. A heading is not complete if the subsection ends after one short paragraph; each material subsection should carry the necessary claim, evidence, business implication, counterargument/risk, and next-decision logic or be merged/removed.
17. Maintain `data_sources/visual_plan.csv` so visuals are chosen by chapter purpose and reader decision use, not by quota.
18. Add tables, graphs, figures, and diagrams chapter-by-chapter after prose direction is stable. Each material table and each material graph/figure/chart must have its own `data_sources/` CSV/XLSX or source-record-backed qualitative artifact. A table inside a `<figure>` wrapper is still a table and must not be counted as a graph, chart, diagram, timeline, or flow visual.
19. Assemble the final HTML with `_ai_system/tools/assemble_report.py`. The assembler must concatenate only and must not rewrite chapter prose.
20. Write the final executive summary as `Chapter 0` / `제0장 요약` after body chapters, visuals, appendices, and core citations are stable.
21. Verify citations, source traceability, hidden metadata, research integrity, artifact structure, design, and conversion-readiness.
22. Run workspace validation, research integrity validation, report preflight, gate status, report factory validation, report artifact validation, and closeout validation separately where tools are available. Use quality scoring only as an optional advisory panel, not as a completion gate.
23. Update worklog, PRD revision log, audit notes, and snapshots.

Stage-specific context rule:

- Before a narrow stage run, use `_ai_system/tools/compose_report_context.py --write-packet` to identify the smallest useful read set for the AI and store the derived packet under `context_packets/`.
- After reference intake or material source repair, refresh the local DuckDB context index with `_ai_system/tools/build_project_context_db.py --project <project_name>` before composing chapter or source context.
- For chapter writing, prefer the chapter workpack, named source/claim rows, and matching visual-plan rows over the assembled HTML.
- The purpose is content quality and performance: bounded context should make chapter prose richer and reduce accidental rewrites.

Domain preset rule:

- `_ai_system/workspace_config.json` may define `preset_domain` and `domain_presets`.
- Presets are explicit context hints for report purpose, quality emphasis, design profile, and theme tokens. They do not silently relax validators, change source truth rules, impose fixed length targets, or promote stages.
- Use `_ai_system/tools/resolve_workspace_preset.py` to inspect the resolved preset and CSS variables before auditing preset behavior.
- Report assembly may inject preset CSS variables into the assembled HTML. This is allowed because it changes presentation, not source truth or report stage.
- `report_quality_score.py`, when used, may use preset quality profiles as advisory hints. Depth and visual adequacy are ultimately judged against the PRD, chapter workpacks, evidence, and reader decision needs.
- Use presets to help the AI write in the right mode, not to hide project-specific standards inside hard-coded tools.

Delivery outbox and cloud handoff rule:

- Cloud upload is optional and disabled by default.
- Before any cloud handoff, build a local package with `_ai_system/tools/build_delivery_outbox.py`.
- The local outbox should include report artifacts, source link registers, claim/source indexes, backing CSV/XLSX files, and only the status summaries that are useful for the recipient.
- Preserved source originals are excluded by default. Include them only after explicit user approval.
- Google Drive, Notion, or another cloud destination is a distribution convenience, not proof of report truth or closeout readiness.
- Record cloud upload status separately as `not_uploaded`, `dry_run`, `uploaded`, `blocked`, or `failed`.
- Verified handoff requires an explicit active report. Use `_ai_system/tools/assemble_report.py` or pass `--report` to the outbox builder; do not let the package silently choose a "latest HTML" fallback for verified delivery.
- Use `run_guarded_step.py --project <project_name> --step handoff` for verified handoff. Use `--step unverified-handoff` only for deliberately incomplete review packages and label the result as unverified.
- Use `_ai_system/tools/smoke_delivery_outbox.py` when changing report assembly, active report routing, or outbox packaging.

Gate status rule:

- `project_state/report_stage_manifest.json` is a record, not proof.
- If `report_gate_status.py` or strict preflight indicates the report is blocked, the AI must not describe it as internally reviewable even if the manifest says `review_candidate`.
- Status reports must lead with `allowed_actions`, `blocked_actions`, and `blockers`, not only with pass/fail validation results.

AI service artifact boundary:

- Files created in Codex, Claude, Antigravity, Gemini, or other AI-specific artifact directories do not count as workspace deliverables.
- If a plan, task list, walkthrough, worklog, report, or source pack matters to this project, save or mirror it under the relevant project folder or `_ai_system/`.
- If an AI cannot write the artifact into this workspace, it must say so explicitly and not report the artifact as delivered.
- Do not cite hidden AI-app artifact paths as if the user can inspect them. When using an AI service that auto-saves `implementation_plan.md`, `task.md`, or `walkthrough.md` outside the workspace, create a workspace-visible copy or record the same content in the project worklog before claiming completion.
- A completed project task must leave a workspace-visible trail: worklog entry, changed files, validation outputs or summaries, and snapshot updates for AI-modified files.

Workspace validation and research validation are different:

- Workspace validation checks folder structure, launchers, HTML parsing, path portability, and snapshot consistency.
- Research validation checks source originality, source readiness, claim readiness, citation traceability, estimates, and unsupported certainty.
- Passing one does not imply passing the other.

When available, run:

- workspace validation: `python _ai_system/tools/validate_workspace_setup.py --include-user-flow`
- research integrity validation: `python _ai_system/tools/validate_research_integrity.py`
- report preflight: `python _ai_system/tools/report_preflight.py --project <project_name> --for-drafting`
- strict research preflight for substantial reports: `python _ai_system/tools/report_preflight.py --project <project_name> --for-delivery --strict-research`
- research integrity validation: `python _ai_system/tools/validate_research_integrity.py --project <project_name>`
- report artifact validation: `python _ai_system/tools/validate_report_artifact.py --project <project_name> --strict-delivery`
- optional report quality status: `python _ai_system/tools/report_quality_score.py --project <project_name>`
- closeout validation: `python _ai_system/tools/validate_closeout.py --project <project_name>`
- consolidated closeout gate: `python _ai_system/tools/run_guarded_step.py --project <project_name> --step closeout`

Do not claim closeout or internally reviewable status if the consolidated gate fails. `validate_closeout.py` failures are hard closeout blockers, not cosmetic warnings.

Backups, latest AI snapshots, and project archives are comparison records. They should not be treated as active report artifacts or active rule files during ordinary setup checks unless the user explicitly asks to inspect archived material.

## Migration Rules

- Keep `AGENTS.md` at the workspace root.
- Keep project folders under `00_사용자_작업공간/`.
- Prefer moving AI operating materials into `_ai_system/`.
- Do not move project evidence or reports out of their project unless the user requests archival.
- If paths move, update:
  - `AGENTS.md`,
  - affected governance files,
  - scripts,
  - launchers,
  - project dashboards,
  - OJT HTML.
- After a migration, run path scans for stale references.

## Domain Independence

- The reusable system core should not hard-code a specific client, industry, project, or regulator into validators.
- Put workspace identity, substantial-report markers, legacy project exceptions, and template marker settings in `_ai_system/workspace_config.json`.
- Project-specific examples may remain in active project folders, archives, validation fixtures, or the current workspace overview, but package-level tools should read configurable values where possible.

## Human OJT Rule

Whenever the workspace structure or user-facing flow changes materially, update `START_HERE.html`.

The OJT document should explain the user workflow, not AI internals. It should show:

- how to open the workspace in an AI service,
- what minimal entry point to ask the AI to read only when needed,
- where to place new files,
- how to start a new project,
- how to open the reference library,
- how to request report drafts, file-modification-free review/cross-check, approved enhancement, and revalidation as separate steps,
- what not to edit manually unless necessary.

OJT copy prompts must stay short. Use this routing split:

- Fresh install, workspace repair, new project creation, or ambiguous routing: mention `AGENTS.md`.
- Existing project work such as document writing, reference intake, artifact improvement, review, cross-check, follow-up artifact creation, or outbox preparation: mention `tasks/current_task.md`.
- User-facing OJT prompts should remain generic. Do not make users paste preset-specific instructions for press releases, curricula, manuals, proposals, investor briefs, or analyst reports. Specialized handling is selected by `document_type_preset`, `artifact_workflow_mode`, PRD fields, `tasks/current_task.md`, and the selected preset/style guidance.
- Simple status explanation, screen guidance, or installed-system next steps: do not force either file.

Dashboard implementation details, hidden folder rules, parsing/indexing internals, logo filename rules, change-log paths, and validation doctrine belong in this governance file, `AGENTS.md`, `tasks/current_task.md`, tools, and templates. Do not make the user paste those details as normal OJT prompts.

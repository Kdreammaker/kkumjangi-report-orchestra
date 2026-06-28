# Report Factory Rules

## Purpose

The primary goal of this workspace is to help AI assistants produce high-quality reports, not merely to catch bad behavior after the fact.

Validation, snapshots, source gates, and closeout checks are supporting controls. They exist to make the report production system more reliable. They are not the product goal.

Use this rule when running a substantial report from end to end, designing a new document workflow, or reviewing whether the current workflow helps the AI write better.

## Report Factory Layers

Treat substantial report work as four connected layers:

1. Report Factory.
   - Creates PRD, detailed TOC, major skeleton, chapter workpacks, chapter fragments, visuals, final assembly, Chapter 0, and export artifacts.
2. Evidence Engine.
   - Preserves originals, source links, source records, claim register rows, assumptions, and data files.
3. Quality Coach.
   - Gives constructive score-lift feedback about argument quality, decision usefulness, visuals, counterarguments, and export readiness.
4. Integrity Guard.
   - Runs gates and validators so false completion, fake originals, missing files, and workspace drift are visible.

Do not let the Integrity Guard become the objective. A green gate is only useful when the underlying report is stronger.

## Runtime and Context Standard

The AI should not reread the whole workspace for every stage. Use a stage-specific context set whenever possible:

Before selecting the stage context, read the project's `tasks/current_task.md`. The active row is the immediate task contract: it lists what to read, what not to read by default, the required rules, completion criteria, and the next stage. If the active row conflicts with a computed workflow suggestion, report the conflict and reconcile it instead of silently broadening context.

- `architect`: report PRD, detailed TOC, source plan, major skeleton.
- `source`: source plan, inventory, source records, source index.
- `chapter`: one chapter workpack, its claim/source rows, and its visual-plan rows.
- `visual`: visual plan, chapter workpack, and matching data/source artifacts.
- `assemble`: cover data, chapter fragments, and optional assembly manifest.
- `review`: assembled report, claim register, source index, AI quality review notes, optional quality score, and validator results.

Use `_ai_system/tools/compose_report_context.py --write-packet` to produce the current stage's read list and `context_packets/*.compact.md` packet. The purpose is performance and content quality: smaller context should produce richer chapter writing and fewer accidental rewrites.

The packet is a derived AI-input view. It should contain the stage, read budget, required files, relevant source/claim/visual ids, and user-data harness reminder. It does not replace the PRD, source records, claim register, reference inventory, or final report citations.

After a stage is completed or intentionally blocked, update `tasks/current_task.md` and run:

`python _ai_system/tools/validate_current_task.py --project <project_name> --write-status`

This refreshes the static `tasks/task_status.html` panel for the project dashboard. The panel is an indicator, not a quality or truth validator.

After an assembled artifact is created or materially revised, preserve a versioned copy and update dashboard-facing ledgers before reporting a new draft/review-candidate path:

`python _ai_system/tools/finalize_artifact_version.py --project <project_name> --artifact <project-relative-path> --version v0.1 --status draft --note "..."`

This tool preserves files and updates `report_registry.csv`, `version_history.md`, `version_pointer.json`, and dashboard change logs. It does not decide content quality, source truth, or whether a user has approved the artifact.

After reference intake or material source repair, run `_ai_system/tools/build_project_context_db.py --project <project_name>` so the context composer and AI can use the local DuckDB index. This index is a rebuildable helper over the reference inventory, Docling normalized units, source records, claims, and workpacks. It does not replace original evidence or source verification.

For chapter and chart stages, the context composer should follow the active chapter workpack into the named source records, claim rows, visual-plan rows, and local data/source artifacts. Do not use the assembled report as the chapter writer's main source of truth when the matching workpack and chapter fragment exist.

For report or document improvement, prefer a bounded source-artifact repair loop: identify the affected 대목차/중목차 or content block, read the matching workpack, source fragment, source/claim rows, visual-plan rows, and at most adjacent summaries, then edit that source fragment or data artifact and reassemble. Read the full assembled artifact only for a final smoke review, cross-section contradiction review, or when the user explicitly asks for a broad audit.

When a user asks for a new artifact based on an existing artifact, start by recording lineage in the new PRD/worklog rather than assuming a fixed report-to-handout conversion path. A source artifact can be any saved document. Reused claims and data remain inherited context until the new artifact's source/claim registers or worklog say what was reverified.

The full factory sequence is the default for `artifact_workflow_mode=substantial`. For `brief`, `standard`, or `specialized` artifacts, keep the source/claim/review/style/version boundaries that apply, but allow PRD-recorded stage compression. Use the selected preset's `stage_overlays.md` as the stage overlay before compressing or replacing stages. A press release should not be forced through Chapter 0 and long chapter workpacks; a curriculum handout may use lesson sections and activity blocks; a product manual may use procedure/troubleshooting sections; a business proposal may use scope/assumption/commercial-boundary sections. If a stage is skipped, record the rationale in `tasks/current_task.md` or the worklog rather than silently bypassing it.

Specialized preset overlays change workflow shape, not responsibility boundaries. They can replace chapter workpacks with lesson sections, task blocks, proposal sections, factbook sections, or public-release blocks. They cannot remove language confirmation, source integrity, protected-span style review, approval status, version preservation, or delivery-readiness checks when those checks are relevant to the artifact.

If validators are run during report production, run the narrow validator required by the active stage first. Re-running the same broad validator more than twice without changing the underlying production artifact is wasteful; report the blocker and move to the actual repair action.

Two optional focused stages are available when they improve report quality:

- `interview`: use the `decision_interviewer` skill for a short decision interview before PRD, TOC, skeleton, chapter workpacks, or Chapter 0. `/grill-me` is only a shortcut; trigger the same skill when the user asks in ordinary language to clarify direction first.
- `chart`: use the `chart_builder` skill when creating concrete chart/table/diagram data and report fragments after visual intent is clear.

## Required Production Flow

For broad or substantial internal review reports and other `artifact_workflow_mode=substantial` artifacts, use this production flow:

1. Report PRD.
   - Confirm or safely infer `output_language` in the interview/PRD stage. Do not draft while it is `undecided`.
   - Ask before drafting when the language choice affects external sharing, investors, partners, legal/regulatory, securities, jurisdiction, or distribution-market risk.
   - Confirm the document type preset and style profile in the interview/PRD stage when the document purpose or reader tone is not obvious.
   - Use language guidance as a layer over the chosen preset/profile. Do not create `*_en` preset copies, and do not add automatic translation, automatic rewrite, or autogenerated legal/securities disclaimer behavior.
   - The style profile is a protected writing aid. It must preserve direct quotes, numbers, statute names, proper nouns, citation locators, and source-backed claims.
2. Report design file, normally `reports/report_design.md`.
   - The PRD decides purpose, reader, document classification, confidentiality, evidence bar, and distribution boundary.
   - The PRD also records `document_type_preset`, `output_language`, `language_variant`, `citation_display_language`, `caption_label_profile`, `style_profile`, `target_reader_tone`, and `protected_spans_policy`.
   - The design file decides A4 margins, typography, palette, cover preset, logo priority, table/chart style, and confidentiality warning placement.
   - Do not use project-level defaults for document classification or confidentiality. Confirm them in the PRD for each report.
3. Detailed TOC.
4. TOC self-review and user approval for substantial reports.
5. Source collection plan.
6. Major skeleton.
7. Skeleton score.
8. Chapter workpacks.
9. Chapter-by-chapter full prose fragments.
   - Each 대목차 in the detailed TOC must have one matching source chapter fragment. The chapter fragment is the master prose file for that 대목차.
   - Each 중목차/소목차 written in the detailed TOC must be preserved as visible headings in the matching chapter fragment. Do not collapse them into a summary table or a few paragraphs.
10. Chapter-quality hook and AI review/revision.
   - Run `_ai_system/tools/report_chapter_quality_coach.py --project <project_name> --write-status`.
   - Treat the hook as a router, not a judge: if it reports `needs_attention`, use the `report_reviewer` skill to review the chapter against the PRD, TOC, workpack, evidence, reader decision, and residual risks.
   - Use the `chapter_writer` skill to revise the relevant `reports/chapters/chNN.html` fragment, then rerun the hook.
   - If a workpack requires a table/figure/diagram, the matching chapter fragment must contain it or contain a hidden `visual_deferred` / `visual_retired` marker with a reason. A comment such as `visuals: V001` is not implementation.
   - Do not move to visual production, assembly, review-candidate gates, or closeout while the hook still requires AI review/revision.
11. Visual/data pass after the body chapters exist and chapter quality signals are clear.
   - Create or revise tables, charts, graphs, diagrams, and CSV/XLSX/source-backed artifacts to match the actual chapter content.
   - For report-ready charts and graphs, generate static SVG/PNG or inline SVG artifacts from the project data. ECharts may be used as a local renderer, but the assembled report should not require JavaScript to display material visuals.
   - When the underlying CSV/XLSX changes, regenerate the static chart artifact before assembly.
   - Record the design and data review in `reports/visual_review.md`, using `_ai_system/templates/report_visual_review.md` as the starting checklist.
   - Optionally run `_ai_system/tools/finalize_visual_pass.py` as an audit hook after the review. The hook records hashes; it does not create or judge visual quality.
12. Write Chapter 0 final summary after the body and visuals are stable.
13. Assemble cover + chapter fragments without rewriting prose.
    - Assembly must include reader-facing appendices for the reference list and local data artifacts when the project has registered sources or visual data.
    - The appendix should show accessible official links and Korean access dates. It should not expose internal ids as the primary reader-facing reference format.
14. Run review-candidate gates.
    - These gates include live chapter-quality routing, cover-render validation, strict factory validation, reference-register consistency, strict artifact validation, and the quality score contradiction check.
15. Optional DOCX/PDF export and render verification.
16. Closeout gates.

The flow is intentionally production-oriented: each stage should give the AI a smaller and clearer writing task.

For ambiguous or high-stakes reports, insert a short `interview` stage before PRD, design, source planning, or final synthesis. This should clarify decisions; it should not become a long intake form or replace evidence collection.

## Source of Truth by Stage

Use these source-of-truth artifacts:

| Stage | Source of truth |
|---|---|
| Scope | `report_prd/*.md` |
| Document type, language, and style profile | `report_prd/*.md`, `_ai_system/document_presets/INDEX.json`, selected `language_guidance.md`, and `_ai_system/style_profiles/INDEX.json` |
| Report-specific design | `reports/report_design.md` |
| Structure | `drafts/*toc*.md` |
| Argument plan | `drafts/*skeleton*.md` or `reports/major_skeleton.md` |
| Decision interview | `questions/question_log.md`, PRD revision notes, and assumption register |
| Current task | `tasks/current_task.md`, rendered for humans as `tasks/task_status.html` |
| Chapter input | `reports/chapter_workpacks/ch*_workpack.md` |
| Chapter prose | `reports/chapters/ch*.html` |
| Chapter quality hook | `reports/chapter_quality/chapter_quality.json`, plus AI review/revision actions when required |
| Visual intent | `data_sources/visual_plan.csv` |
| Chart/table data | `data_sources/*.csv` or `data_sources/*.xlsx` plus source-backed qualitative artifacts |
| Visual review | `reports/visual_review.md`, optionally supported by `reports/visual_pass_manifest.json` |
| Cover values | `reports/cover.data.json` |
| Final HTML | rendered reading copy assembled by `_ai_system/tools/assemble_report.py` |
| Versioned artifacts | `reports/versions/`, `reports/current/version_pointer.json`, `reports/version_history.md`, and `reports/report_registry.csv` |
| Export evidence | `reports/export_checks/` or equivalent render proof |

Cover values must use the reusable preset component. Choose `public_release`, `team_review`, `executive_decision`, or `partner_proposal` in `cover_preset` according to document purpose. Use the report-specific logo first, then `project_profile.json` / `brand_assets/`, then common CI, then blank. Do not recreate cover markup inside a report chapter. A cover preset is a document/audience format, not a report-stage promotion or external-sharing approval.

If `confidentiality_status` is `대외비`, the cover must include the reusable confidential tag and a sentence-form confidentiality notice. For now the notice is cover-only unless the user asks for a footer across all pages.

Do not make the assembled HTML the drafting source of truth for substantial reports. Edit the relevant chapter fragment, then reassemble. The assembled HTML is an indicator/rendered copy that proves which chapter fragments were concatenated; it is not the master writing surface.

Do not leave versioning only inside `cover.data.json`. Cover version text is reader-facing metadata; durable version control belongs in `reports/versions/`, `reports/current/version_pointer.json`, `reports/version_history.md`, and `reports/report_registry.csv`.

## TOC Coverage Gate

Strict factory validation should compare the detailed TOC against `reports/chapters/`:

- `## 제N장` 대목차 requires a matching `reports/chapters/chNN*.html` source fragment.
- `### N.M` 중목차 requires a matching visible heading prefix in that chapter fragment.
- `#### N.M.K` 소목차 requires a matching visible heading prefix when the TOC defines it.
- Missing TOC coverage blocks review-candidate and closeout claims even if the assembled report exists and file counts look complete.

This gate is structural. It does not claim the analysis is deep, but it prevents the AI from creating a rich TOC and then writing a compressed one-file or shallow chapter summary.

## TOC Approval Gate

For substantial reports, the detailed TOC is a human decision point. Before evidence collection or chapter drafting, the AI should:

- run a self-review of 대목차/중목차/소목차 coverage against the PRD;
- check missing policy/legal domains, players, business options, counterarguments, risks, evidence needs, and visual candidates;
- record the review in the worklog, PRD review gate, or a short `drafts/*toc_review*.md` file;
- ask the user to approve, revise, or explicitly waive TOC approval.

Do not use this gate as a recurring approval request for every internal step. It exists because TOC shape determines report scope and prevents shallow chapter production.

## Legacy Compatibility

Projects created before the Report Factory flow may have a complete HTML report but lack chapter workpacks, `reports/cover.data.json`, `data_sources/visual_plan.csv`, or assembled-report markers.

For those projects, strict factory validation should report `legacy migration required` rather than pretending the old report never existed. Use `_ai_system/workspace_config.json` to list such legacy projects.

When intentionally migrating a legacy report to the new process, use the stricter mode:

`python _ai_system/tools/validate_report_factory.py --project <project_name> --strict --enforce-modern`

Migration should regenerate factory artifacts from PRD, TOC, skeleton, workpacks, chapter fragments, visual plan, cover data, and assembly. Do not retrofit only enough files to silence the validator.

Quality smoke:

`python _ai_system/tools/smoke_report_quality_constraints.py`

This smoke test verifies that a long, data-backed report cannot become a Level 4 internal-review candidate without chapter workpacks, chapter fragments, reusable cover/assembly markers, and a role-complete visual plan.

## Assemble-Only Rule

The report assembler must concatenate approved components. It must not:

- rewrite prose,
- summarize chapters,
- merge duplicate claims by rewriting content,
- add new conclusions,
- create new source claims,
- silently remove warnings or residual risks.

If a chapter needs improvement, edit the chapter fragment and rerun assembly.

The assembler records each chapter fragment hash in `reports/report_assembly_manifest.json`. Review gates compare each source chapter fragment hash and exact text inclusion against the assembled report. They do not compare the whole assembled HTML hash to a chapter hash, because the assembled report necessarily contains cover, wrapper markup, and multiple fragments.

The visual pass hook follows the same principle: it can record the hashes of body chapter fragments and data artifacts after visual review. It is useful for catching stale or falsely claimed review records, but it is not a substitute for the `chart_builder` skill, `reports/visual_review.md`, or design judgment.

## Hook and Skill Boundary

Local hooks do not decide whether analysis is deep, persuasive, or business-ready. Their job is to route the AI to the skill-based action that must happen before the next gate.

- A local Python hook cannot directly invoke a Codex/AI skill. It can only output `required_ai_action`, set `skill_action_required`, and fail the guarded step so the AI must perform the named skill-guided work before continuing.
- A chapter-quality hook may detect missing signals, stale reviews, short fragments, weak workpack alignment, or missing data captions. It should then require `report_reviewer` and `chapter_writer` action; it should not pretend to be the final writing judge.
- A visual hook may detect a missing checklist, stale visual pass, unfinished `visual_plan.csv` rows, or missing data artifacts. It should then require `chart_builder` action; it should not pretend to be a design critic.
- A reference consistency hook may detect that `reference_inventory.csv`, `source_link_register.csv`, `source_master_index.md`, and `source_records/*.md` disagree. It should block review/closeout until the AI repairs the ledgers; it still does not prove source truth.
- A closeout hook may run mechanical validators. It should report mechanical pass separately from content-quality readiness.
- A quality-score hook may cap a report when strict blockers exist. It still cannot declare that strategy, legal interpretation, or writing depth is excellent; that remains AI/human review work.
- A style profile can guide tone and reader fit, but it is not a hook, validator, or automatic rewriting authority. It cannot override protected spans or substitute for AI judgment, source verification, claim-readiness review, artifact validation, or closeout gates.

Use these states distinctly:

- `mechanical_ready`: files, links, records, structure, and validator checks are present enough to continue.
- `chapter_quality_review_required`: chapter fragments exist, but the hook requires AI review/revision.
- `content_review_ready`: chapter-quality and visual-review hooks are clear, and AI review has resolved required actions.
- `delivery_ready`: export/render/handoff requirements are also satisfied.

## Chapter 0 Rule

Chapter 0 / `제0장 요약` is the final synthesis. It is written after:

- body chapters are drafted,
- key claims are registered,
- visuals and data files exist,
- the visual review has been recorded,
- residual risks are visible,
- appendices and citations are stable.

An early executive-summary placeholder may exist in the skeleton, but it must be clearly labeled as a placeholder and must not be delivered as final Chapter 0.

## Quality Coach Standard

When a report is not strong enough, the AI should report the next improvement as a production action, not only a validation failure.

Examples:

- weak: "strict delivery failed because there is no chart"
- better: "Chapter 4 needs a decision matrix and a process diagram because the reader must compare Track A, Track B, and Plan B."

- weak: "visible characters are below target"
- better: "Chapter 5 lacks counterarguments, regulatory residual risk, and implementation implications; expand those sections before treating the report as internally reviewable."

## Status Reporting

For substantial report work, status reports should separate:

- production progress,
- evidence readiness,
- AI quality review and optional score-lift,
- integrity gate results,
- not tested,
- residual risk.

Never describe workspace validation as report quality validation.

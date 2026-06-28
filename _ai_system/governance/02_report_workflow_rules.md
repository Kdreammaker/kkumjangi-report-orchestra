# Report Workflow Rules

## Report Language and Format

- Decide `output_language` during the new-project, direction-confirmation, or PRD stage together with document purpose, target reader, distribution boundary, and evidence standard.
- If the user's launch instruction, source material, and target output are clearly Korean, use `output_language=ko` without asking again.
- If the launch instruction is English or the user clearly asks for an English report, English version, or English readers, use `output_language=en` without asking again.
- If the instruction language and desired output language may differ, or if external sharing, investors, partners, legal/regulatory, securities, jurisdiction, or distribution-market risk is present, ask before drafting and record the decision in the PRD or current task.
- Do not proceed to substantive drafting when `output_language` is `undecided`. Resolve it first through inference when safe, or through a short user question when risk requires confirmation.
- Do not create separate English document presets such as `*_en`. Use the selected document preset and style profile, then layer language, region, notation, caption, citation, and disclaimer guidance on top.
- Language guidance does not translate, humanize, rewrite, verify source truth, create jurisdiction-specific legal/securities disclaimers, or replace approval review.
- For substantial reports, create or update the report PRD before creating a detailed TOC or drafting.
- Before a final delivery format is explicitly chosen, draft reports as `.html`.
- Report HTML must be written with future `.docx` and `.pdf` conversion in mind.
- Add difficult legal, financial, technical, or foreign terms to the relevant report appendix glossary.
- Follow `_ai_system/governance/06_report_prd_rules.md` for report PRD creation, reader-facing metadata boundaries, update triggers, and revision logs.
- Follow `_ai_system/governance/10_research_quality_gate_rules.md` before converting scaffold text, source summaries, or claim-register rows into report conclusions.
- Follow `_ai_system/governance/11_gate_based_execution_rules.md` before moving from planning to evidence collection, evidence collection to drafting, or drafting to review-candidate.
- Follow `_ai_system/governance/12_report_quality_scoring_rules.md` after drafting or reviewing a report so the AI reports hard blockers, improvement opportunities, and optional level/score status when useful.
- Follow `_ai_system/governance/13_report_factory_rules.md` when running a substantial report from PRD through closeout. The primary goal is high-quality report production; validators are supporting controls.
- Follow `_ai_system/governance/14_chapter_workpack_rules.md` before writing chapter fragments.
- Follow `_ai_system/governance/15_export_conversion_rules.md` before creating or claiming DOCX/PDF readiness.
- Follow `_ai_system/DESIGN_DOCUMENT.md` for report design, document hierarchy, color, table, chart, data-file, and writing-style rules.

## Document Preset And Style Profile Standard

- Use `_ai_system/document_presets/INDEX.json` when the requested document type is unclear or when the PRD/interview stage must choose a `document_type_preset`.
- Use `_ai_system/document_presets/CODEMAP.md` only when the compact index is not enough to choose the selected preset files. After selecting a preset, read only the selected module's current-stage files.
- Use the selected preset's `default_artifact_workflow_mode` and `read_for_workflow` entries in `_ai_system/document_presets/INDEX.json` before deciding whether to run full report stages or a compressed/specialized artifact sequence.
- Read the selected preset's `stage_overlays.md` when setting `artifact_workflow_mode`, planning stage compression, or reviewing whether the artifact drifted into the wrong document genre. Do not ask the user to paste document-specific OJT prompts for this.
- When `output_language` is `en` or `mixed`, read the selected preset's `language_guidance.md` when it exists. This is a guidance layer over the same preset, not a separate English preset or an automatic translation step.
- Confirm the document type preset during the interview or PRD stage before detailed TOC, source planning, or drafting. A preset changes emphasis for PRD questions, TOC review, visuals, layout, and quality review; it does not bypass source integrity, review, approval, or versioning boundaries.
- Use `_ai_system/style_profiles/INDEX.json` when the user asks for a specific reader tone, when the document purpose implies a tone choice, or when the PRD needs a `style_profile`.
- Use `_ai_system/style_profiles/CODEMAP.md` only when the compact index is not enough to choose the selected style profile files. After selecting a profile, read only the selected module's current-stage files.
- When `output_language` is `en` or `mixed`, read the selected style profile's `language_guidance.md` when it exists so sentence length, directness, caveats, and conclusion placement fit the reader language without changing protected spans.
- Confirm `style_profile`, `target_reader_tone`, and `protected_spans_policy` in the PRD before applying broad tone changes.
- A style profile is a protected writing aid, not an automatic polish/rewrite tool. It must preserve direct quotes, numbers, statute names, proper nouns, citation locations, and source-backed claims unless a deliberate source or claim correction is recorded.
- Style profile guidance never replaces source verification, claim-readiness gates, citation checks, legal review, chart/data support, or closeout validation.
- Treat style profile and register overlay as separate decisions. The style profile sets the reader/purpose-based writing standard; a register overlay sets the Korean delivery mode layered on top of that profile, such as written report, oral briefing, public written copy, educational explanation, or adult user instruction.
- Register, honorific, and user-instructional overlays are guidance-only assets for AI review during style pass. They do not translate, humanize, rewrite automatically, change workflow stage, validate evidence, or override protected spans.
- During decision interview or PRD work, confirm or safely infer `output_language`, target reader, `document_type_preset`, `artifact_workflow_mode`, `style_profile`, `register_overlay` need, `honorific_policy` need, and `user_instructional_overlay` need before substantive drafting.
- Use `_ai_system/style_profiles/register_overlays/README.md` only when a Korean register/honorific/user-instructional layer may be needed. Read `korean_register_overlay.md`, `honorific_policy.md`, or `user_instructional_overlay.md` only for the selected or plausible overlay. Do not open every overlay file by default.
- 압존법 is not a default Korean style rule. Consider it only for special Korean spoken or dialogue-like situations where the speaker, listener, and referenced person are in a known same-organization hierarchy and the text is not public, legal, approval-sensitive, quote-sensitive, or partner/customer-facing. If hierarchy or approval impact is unclear, hold the span for human review.
- When Korean tone/style review is requested, read `_ai_system/style_profiles/korean_tone_workflow_design_v1.md` plus the selected profile files. Use the style-pass sequence: style-risk findings, protected-span map, limited rewrite diff only when allowed, fidelity review, naturalness review, then rollback or human review if needed.
- Store style-pass artifacts under the active project, normally `reports/style_pass/`, using `_ai_system/style_profiles/templates/style_risk_findings.json`, `protected_spans.json`, `style_rewrite_diff.md`, `style_fidelity_review.md`, and `style_naturalness_review.md` as guidance-only templates.
- Style-pass findings must label risks as `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, or `reader-fit`. When a register or honorific layer is selected, connect the review trace to the same artifact set: mark register/honorific risks in `style_risk_findings`, keep protected honorific/title/name/quote spans in `protected_spans`, record limited changes or held changes in `style_rewrite_diff`, and confirm fidelity/naturalness in the two review files. Do not use style pass to run automatic whole-document rewrite, AI-detection evasion, protected-span rewriting, jurisdiction-specific legal/securities disclaimer generation, or score-based pass gates.
- Expression review must check TPO, not just typo or translationese. For education artifacts, look for learner level, activity wording, examples, instructor/learner separation, and whether report-like analysis leaked into handouts. For manuals, look for procedural clarity, warnings, prerequisites, and troubleshooting. For press releases, look for public wording, approved quotes, boilerplate, contact, and embargo/release status. For executive/internal reports, look for scanability, conclusion placement, caveat discipline, and concise decision language. Record mismatches as `genre-drift` or `reader-fit` and fix only source fragments/captions that can be changed without harming protected spans.
- Investor brief, sector analysis, and company analysis should use document presets such as `investor_brief` or `equity_research` for structure, evidence expectations, visuals, and review checklist. Tone and manner for those documents should come from the selected style profile plus the common Korean style workflow, without duplicating a preset-specific rewrite engine.

## Artifact Workflow Mode

User-facing OJT prompts must stay generic. The AI decides document-type specialization inside the PRD/TASK flow, not by asking the user to paste longer specialized prompts. Use the selected preset's `stage_overlays.md` as the main workflow overlay for this decision.

During interview or PRD work, set `artifact_workflow_mode`:

- `brief`: short artifact such as press release, announcement, memo, compact handout, or one-page brief. Keep source integrity, approval boundary, review, style pass, versioning, and delivery checks, but do not force major skeleton, Chapter 0, or chapter workpacks unless the PRD needs them.
- `standard`: structured artifact such as proposal, product manual, education handout, PRD, investor brief, or partner-facing brief. Use PRD, outline/TOC, section-level source and claim mapping where needed, section drafting, file-edit-free review, style pass, assembly/versioning.
- `substantial`: long evidence-backed report or analysis. Use the full production order with detailed TOC, skeleton, chapter workpacks, chapter fragments, visual/data pass, Chapter 0, pre-assembly style pass, assembly, validation, and versioning.
- `specialized`: selected preset requires mandatory blocks or boundaries that differ from the ordinary sequence. Read only the selected preset module and record which standard stages are skipped, compressed, or replaced.

Mode selection principle:

- Start from the preset's `default_artifact_workflow_mode`.
- Upgrade to `substantial` when the user asks for deep analysis, broad evidence, detailed source/claim mapping, many visuals, or high-risk decision support.
- Downgrade or keep compressed only when the requested artifact is naturally short or section-based, such as a press release, compact handout, product task guide, or concise proposal.
- If the chosen mode differs from the preset default, record the reason in the PRD, `tasks/current_task.md`, or worklog.
- Python helpers may check that preset workflow assets exist and that the selected mode is recorded. They must not decide whether the writing is strategically persuasive, pedagogically effective, legally sufficient, or investment-grade.

Examples of specialized handling:

- `press_release`: prioritize dateline, release status, approved quotes, boilerplate, media contact, embargo/approval boundary, and public wording discipline. Do not force Chapter 0 or long report workpacks.
- `education_curriculum`: prioritize learner level, learning objectives, time blocks, activities, handout structure, exercises, and evaluation/assignment notes. Use a lesson/section plan rather than a report chapter plan when appropriate.
- `product_manual`: prioritize target user, prerequisites, environment, step-by-step procedures, warnings, troubleshooting, FAQ, and version/platform scope.
- `business_proposal`: prioritize buyer problem, scope, assumptions, exclusions, implementation plan, responsibilities, commercial boundary, and proposal/quote/SOW/contract separation.
- `investor_brief` and `equity_research`: prioritize approved metrics, basis date, source/citation discipline, forward-looking statement boundary, not-offer/not-investment-advice boundary, and no unauthorized rating/target-price generation.

If stages are skipped or compressed, mark them as `skipped` in `tasks/current_task.md` with a reason and keep the review/style/version gates that apply to the artifact.

## Content Depth And Execution Control

Set `content_depth` during interview or PRD work:

- `standard`: the default baseline for the selected preset, reader, and workflow mode.
- `concise`: keeps the same decision structure but targets roughly 30-60% of standard volume by reducing examples, repeated explanation, and secondary detail. Do not remove required claims, citations, warnings, approval boundaries, or review traces.
- `expanded`: targets roughly 180-250% of standard volume only when evidence, reader need, and artifact purpose justify more examples, alternatives, caveats, appendix detail, or teaching/procedure support. Do not pad prose to hit a number.

Set `execution_control_mode` when the user indicates how much stopping they want:

- `checkpointed`: stop at explicit approval gates such as setup brief, TOC approval, sensitive language/distribution decisions, external sharing, or high-risk legal/regulatory/securities boundaries.
- `delegated`: proceed to the requested target point when the task path is clear, then report assumptions made, skipped or compressed stages, unresolved issues, failed validators, items needing user confirmation, and residual risk. Delegated mode is useful for “초안까지 진행”, “검수 후보까지 진행”, or “가능한 데까지 진행” requests.

Delegated mode is not autonomous quality control. It must not skip source truth, output-language resolution, confidentiality/distribution decisions, protected-span preservation, external sharing approval, legal/securities approval, version preservation, or the requirement to label drafts honestly.

## Follow-Up Artifact And Project Lineage

- A follow-up request can start from any existing artifact: report, handout, proposal, manual, brief, press release, curriculum, or another saved document. Do not hard-code a report-to-handout path.
- When the user asks to make a new artifact from an existing one, treat it as a derived artifact or derived project and record:
  - `source_project_id`,
  - `source_artifact_path`,
  - `source_artifact_version` if known,
  - `source_artifact_type`,
  - the new artifact goal,
  - the new target reader and use context,
  - the expected output type,
  - `reuse_scope`,
  - `new_verification_scope`.
- Existing source artifacts are context and reusable structure. They do not automatically make the new artifact's claims, captions, or teaching examples newly verified.
- If the derived artifact has a different reader, purpose, document type, or distribution boundary, create or update the PRD before drafting and rerun the relevant preset/style decisions.
- Avoid source anchoring. The previous artifact can provide verified context, structure candidates, and reusable source lists, but the derived artifact must choose its own preset, style profile, content depth, layout blocks, examples, visuals, and review standard. Do not copy a report-like structure into a handout, proposal, manual, press release, or brief when the selected preset says another structure fits better.
- The derived project must still use `tasks/current_task.md`; do not create a separate `task.md` as the main task authority.

## HTML Report Standard

- Default report working format is `.html` unless the user explicitly asks for another format.
- HTML reports must remain suitable for later `.docx` and `.pdf` conversion.
- Use semantic, document-like HTML:
  - `article`, `section`, `header`, `footer`, `h1`-`h4`, `p`, `table`, `figure`, `figcaption`, `ol`, `ul`, and `aside`.
- Avoid app-like or browser-only layouts that do not convert cleanly to DOCX/PDF.
- Avoid external scripts, interactive-only charts, remote fonts, remote images, and CSS that depends on viewport-only behavior.
- Material charts should be rendered as static SVG/PNG or inline SVG before final assembly. A local chart library may help generate them, but the final report must not require JavaScript to display them.
- Keep CSS either embedded in a `<style>` block or stored as a local companion stylesheet if a converter supports it.
- For substantial reports, prefer the reusable template assets in `_ai_system/templates/report_html/` or follow their class and structure conventions. One-off styling may be acceptable for a brief, but lowers reproducibility for repeatable reports.
- Substantial reports should use the reusable cover component in `_ai_system/templates/report_html/cover/`. Populate `reports/cover.data.json`; do not ask the AI to recreate a cover design from scratch for each report.
- Cover layout should be selected as a module package. Start from the reusable cover component and choose only the required modules for the artifact: classification badge, report type, title/subtitle, metadata table, approval cells, purpose note, confidentiality tag/notice, contact/release status, or version marker. Education handouts, product manuals, press releases, and compact briefs may use lighter covers than substantial reports. Do not render confidentiality warning modules when the PRD/cover data says `대외비 아님` or `not_confidential`.
- Use local image paths and keep chart images in the relevant `figures/` folder.
- Use page-friendly styling:
  - A4-oriented width,
  - print CSS where useful,
  - no fixed-position overlays,
  - no text over images unless tested for PDF readability,
  - tables that can split or be simplified for print.
- Every table or figure in HTML must cite original sources in the report's confirmed display language and name the underlying dataset or qualitative evidence. Korean reports use `자료:` and `근거 데이터:`. English reports may use `Source:`, `Underlying data:`, or `Data basis:` only when `html[lang="en"]` or an explicit output-language marker is present.
- For delivery-stage work, each material table, chart, figure, graph, or process diagram must have its own source and data-basis note in the confirmed display language. Exact `data_sources/` or source-record paths belong in HTML comments, data indexes, or appendix artifact tables, not as the visible reader-facing label.
- A material table and a material graph are separate artifacts. If both appear, create separate corresponding data files unless they intentionally share the same named dataset and the caption explains the shared dataset section.
- HTML must not hard-code material quantitative values without a companion `.csv` or `.xlsx` file. If a value appears in a chart, scenario, timeline, market-size estimate, or quantitative table, the local dataset must exist before delivery.
- Do not expose internal source ids such as `[source: ...]` in rendered report body text. Use numbered footnotes or endnotes for readers and preserve source ids in HTML comments, source records, and claim registers.
- Do not include a reader-facing body section named `Evidence Table`, `증거 자료 및 클레임 대장`, or similar internal ledger title. Evidence and claim registers are internal audit artifacts. Reader-facing reports should use numbered footnotes/endnotes and appendices.
- Substantial reports must include an appendix section unless the report PRD explicitly explains why an appendix is unnecessary.
- When a chart is complex, data-heavy, or mainly methodological, summarize the insight in the main body and place the full chart, source screenshot, detailed table, or sensitivity view in the appendix.
- If final DOCX/PDF is later requested, render and visually inspect the output before treating it as final.
- A generated `.docx` or `.pdf` is not delivery-ready until its structure and rendered output have been checked. File creation alone proves only that a conversion artifact exists.
- DOCX/PDF readiness should not flatten the report design into a plain document. Use the reusable report template/style system and conversion-friendly components so the HTML remains polished and the converted document remains usable.

## Language, Style Pass, And Assembly Placement

Use this placement to avoid repeated rewriting and excessive context use:

1. Decide or confirm `output_language` during interview/PRD before substantive drafting. Language determines the preset language guidance, style-profile language guidance, citation labels, caption labels, access-date wording, and disclaimer boundary.
2. Select `style_profile` during interview/PRD as a reader-fit writing target. This can guide drafting, but it is not the editing pass.
3. Decide whether a register overlay, honorific policy review, or user-instructional overlay is needed. These sit on top of the selected style profile and are normally relevant only for Korean delivery mode, oral briefing, public wording, education explanation, or adult procedural guidance.
4. Draft body chapter fragments from chapter workpacks and evidence records. Do not perform whole-report polish while chapter structure, claims, and visuals are still moving.
5. Add visual/data artifacts after body chapter direction is stable.
6. Write Chapter 0 only after body chapters, visuals, risks, and appendix direction are stable.
7. Run the style pass after body chapters, Chapter 0, and visual captions are stable, but before assembly. The style pass works on chapter fragments and relevant captions, not on the assembled HTML as the source of truth.
8. Assemble the report only after the style pass has either applied limited approved changes or recorded a no-change/held-change result with fidelity and naturalness review. The assembly manifest should record the current `reports/style_pass/` artifact hashes so workflow routing can detect a stale pre-style assembly.
9. Review the assembled report as a reading copy. If review finds content problems, fix the relevant chapter/data/visual source and rerun style pass only for affected fragments before reassembly.
10. Preserve the assembled artifact as a versioned copy before reporting it as a new draft, review candidate, or approved baseline.

The style pass is a late production step, not a standing drafting loop. It should leave artifacts under `reports/style_pass/`: `style_risk_findings`, `protected_spans`, `style_rewrite_diff`, `style_fidelity_review`, and `style_naturalness_review`. If no rewrite is appropriate, record a no-change or held-change decision in the same artifact set. When register, honorific, or user-instructional guidance applies, record its review trail inside those same artifacts rather than creating an automatic rewrite lane.

The style pass may improve expression, but it is not an automatic Korean rewrite engine. It should identify what the AI changed, what it deliberately held, and what needs human review. If the artifact still reads like the wrong genre after style pass, keep it as a review issue instead of declaring the document complete.

## Artifact Versioning Standard

- Do not rely on one mutable `internal_review_report.html` or `assembled_handout.html` as the only record after review or enhancement.
- Use `v0.x` for drafts and enhancement rounds before user sharing/submission/baseline approval.
- Use `v1.0` only when the user indicates the artifact should be a sharing, submission, or baseline candidate. Natural-language phrases such as "계속 진행" or "초안까지" are not approval.
- Use `v1.x` for revisions that keep the same purpose, reader, artifact type, and main structure.
- Use `v2.0` when purpose, reader, artifact type, core conclusion, or structure materially changes.
- Include `YYMMDDHHMM` in saved artifact file names and version folders.
- Preserve versioned artifacts under `reports/versions/`, keep the current pointer under `reports/current/version_pointer.json`, and update `reports/version_history.md`, `reports/report_registry.csv`, and dashboard change logs.
- Python tools may preserve files and update ledgers, but the AI must explain the version choice and approval status in the worklog.

## Detailed TOC First Standard

- Natural-language requests such as “보고서 시작해줘”, “초안 만들어줘”, or “자료 모아서 정리해줘” should still follow the PRD, detailed TOC, source collection, claim registration, and preflight sequence when the output is a substantial report.
- If a report is requested as part of a short new-project request, first confirm the full project setup brief, initialize the project, then create the report PRD and detailed TOC. Do not treat the setup brief itself as a report PRD unless the user confirms it should become one.
- For any report, memo, research packet, or loosely scoped analysis request, create a detailed table of contents before substantive source collection or drafting.
- The detailed TOC should derive from the current report PRD.
- The detailed TOC must map report sections to the evidence, data, assumptions, glossary entries, and charts/tables that need to be produced.
- When the user gives a rough or broad report/research task, do not start collecting large amounts of material or drafting conclusions before creating a detailed TOC.
- The TOC should include large, middle, and small sections where useful.
- Each TOC should identify what must be researched, what evidence type is needed, and what output artifact may be produced.
- For each substantial section, the TOC should identify whether the output expects a table, chart, appendix item, source capture, legal matrix, benchmark card, glossary entry, or only prose.
- The TOC should be stored under the relevant project's `drafts/` folder.
- For substantial reports, perform a TOC self-review before evidence collection or drafting. Check topic coverage, policy/legal scope, player coverage, counterarguments, risks, source needs, and visual candidates.
- Ask the user to approve the detailed TOC before moving to evidence collection or chapter drafting unless the user explicitly waives TOC approval.
- If the report scope changes, update the TOC or create a revised TOC before continuing.
- Source collection should then proceed section-by-section against the TOC.
- For broad or substantial reports, create or update a source collection plan before large-scale collection. The plan should identify source type, official/original target, collection method, OCR/translation needs, and status by report section.
- For external sources, collection means preserving a user-provided original file, registering an exact official URL, or using an explicitly requested capture. Do not treat AI summaries, memory, or internal-slide summaries as collected external evidence.
- Do not make report workflow depend on AI file downloads. Record exact official links in `references/source_link_register.csv`; if the report needs a file, add it to `references/user_requested_materials.md` and continue only within the verified link/quote boundary.
- Foreign benchmark cases named in the report require case-specific original evidence. Internal slides or domestic policy documents can justify why the benchmark should be investigated, but cannot verify that benchmark's facts without the foreign/company/regulator source.
- Exceptions:
  - tiny one-off answers,
  - user explicitly asks to skip planning,
  - urgent fact lookup with no report artifact.

## Major Skeleton and Chapter Expansion Standard

Substantial reports should use this build order:

1. PRD.
2. Detailed TOC.
3. Major skeleton / 주요 골조.
4. Skeleton score.
5. Chapter-by-chapter full text version.
6. Chapter-by-chapter graph/table/figure addition.
7. Chapter 0 final summary.

The major skeleton is not the final report body. It should state the chapter thesis, evidence needed, likely claims, unresolved issues, counterarguments, data needs, visual candidates, appendix candidates, and DOCX/design considerations. It should not include reader-facing final tables, graphs, or decorative visuals.

After creating the major skeleton, apply the skeleton scoring rules manually or with `_ai_system/tools/report_skeleton_score.py --project <project_name>`. Treat the number as a checklist signal, not a substitute for AI judgment. If the skeleton lacks thesis, evidence, counterarguments, data/visual intent, or decision use, improve it before full-text expansion even if a tool appears green.

Before writing full chapter prose, create a chapter workpack under `reports/chapter_workpacks/chNN_workpack.md`. Use `_ai_system/templates/chapter_workpack_template.md` as the starting point. The workpack should narrow the AI task to one chapter's question, decision use, evidence, claim rows, counterarguments, visual needs, appendix needs, and forbidden overclaims.

Full text expansion should proceed one chapter at a time. For each chapter:

- confirm the chapter's evidence and claims,
- write the full prose,
- keep estimates and assumptions explicit,
- leave visual placeholders only where data is still missing,
- update source/claim/data registers as needed.

Tables, graphs, figures, and diagrams are added after the chapter prose direction is stable. Each material table and each material graph/figure/chart needs a corresponding `.csv` or `.xlsx` file under `data_sources/`, or a source-record-backed qualitative artifact for non-quantitative diagrams.

The final summary must be `Chapter 0` / `제0장 요약`. It is written after all body chapters, visuals, footnotes, appendices, and risk notes are stable. Do not write Chapter 0 first.

For substantial reports, the chapter files are the prose source of truth:

- write body chapters as HTML fragments under `reports/chapters/ch*.html`;
- keep matching chapter workpacks under `reports/chapter_workpacks/ch*_workpack.md`;
- do not place full `<html>`, `<head>`, or `<body>` wrappers inside chapter fragments;
- write `reports/chapters/ch00_summary.html` after the body chapters are stable;
- assemble the final report with `_ai_system/tools/assemble_report.py`;
- the assembler concatenates cover and chapters only. It must not rewrite the chapter prose.

## Report Claim Register Standard

- Each project report must maintain `reports/report_claim_register.md`.
- The Phase 01 comparative memo must maintain `reports/phase_01_claim_register.md`.
- Every material report claim must have a claim-register row before it appears as a report conclusion.
- A claim may enter the report body as a conclusion only when its status is `report_citable` or it has passed the equivalent research quality gate.
- Legacy statuses such as `source_backed` or `cited` mean only that a source or citation link exists. They do not prove original verification unless the claim also has quality-gate evidence.
- Use these claim classifications:
  - `confirmed_fact`
  - `summary`
  - `interpretation`
  - `estimate`
  - `unresolved_issue`
- Use these citation types separately from claim classification:
  - `direct_quote`: exact source wording copied into the report.
  - `paraphrase`: source content restated in our words.
  - `data_based`: dataset, calculation, or local reproducibility artifact supports the claim.
  - `inference`: analyst/AI reasoning based on one or more sources.
- `interpretation` claims require source ids plus reasoning notes.
- `estimate` claims require source ids plus data file ids or assumption ids.
- `unresolved_issue` claims may appear in risk/open-question sections only when the uncertainty is explicit.
- `confirmed_fact` claims require an original source, original verification, and a quote/page/section/URL location when available.
- For delivery-stage reports, `Fact` claims must include a quote/page/section/URL/capture location either in the claim register or in the linked source record.
- `estimate` claims require data file ids and assumption ids; local CSV/XLSX files are reproducibility artifacts, not external source evidence.
- AI-created summaries or translations cannot support `confirmed_fact` unless they point back to a verified original.
- In HTML reports, claim type and source ids should usually be stored as HTML comments near the paragraph rather than repeated as visible tags in every paragraph.
- Visible labels such as `확인된 사실`, `해석`, `추정`, and `미확인 쟁점` should be used sparingly in executive matrices, risk tables, or appendices where they improve readability.

## Citation Display Standard

- Rendered Korean reports should use reader-facing citation marks:
  - numbered footnotes/endnotes such as `1)`, `2)`,
  - a `주석` or `참고문헌` section with full source details,
  - `주:` and `자료:` below tables and figures.
- Use `자료:` only for original source institutions, authors, reports, statutes, datasets, or publications.
- Use `근거 데이터:` for local `.csv` or `.xlsx` files created in the workspace.
- Rendered English reports may use `Source:`, `Underlying data:`, `Data basis:`, and `Accessed YYYY-MM-DD` when the PRD confirms `output_language=en` or `citation_display_language=en` and the HTML carries `lang="en"` or an equivalent explicit language marker.
- Do not allow English caption labels in a Korean report merely because they appear in the HTML. If the PRD or HTML does not explicitly mark English output, use Korean labels and Korean access-date display.
- In the visible report, describe local datasets with a Korean label instead of a raw relative path. Preserve the exact path in HTML comments, the data index, or appendix artifact table.
- For Korean reports, show web access dates as `접근일: YYYY.MM.DD`; do not use English `accessed YYYY-MM-DD` in reader-facing references unless the report itself is in English.
- Direct quotes should use quotation marks or block quote styling and cite the exact location. Paraphrases should cite the source without quotation marks. Inferences should be written as analysis, not as if the source itself stated the conclusion.
- A local file in `data_sources/` is a reproducibility artifact, not the external source itself.
- Internal identifiers such as `source_id`, `claim_id`, `assumption_id`, and `data_file_id` should remain available in source index, claim register, data files, or HTML comments. Do not explain this metadata system in reader-facing report prose unless the report is specifically about methodology.
- A report must not substitute a visible evidence ledger for citations. If the report needs a source overview, use a reader-facing `참고문헌` or appendix source list, not internal IDs.

## Automated Gate Standard

- Project setup is not report drafting. A newly created project may have folders and ledgers but still be at `planning` stage.
- Before material report work, check the gate status with `_ai_system/tools/report_gate_status.py --project <project_name>` or manually report equivalent `allowed_actions`, `blocked_actions`, and `blockers`.
- `project_state/report_stage_manifest.json` records the AI's last known state; it does not prove that the state is correct. If gate status and manifest disagree, treat the manifest as stale.
- Before substantive drafting beyond a scaffold, run `_ai_system/tools/report_preflight.py --project <project_name> --for-drafting`.
- Before describing a report as internally reviewable, run:
  - `_ai_system/tools/validate_research_integrity.py --project <project_name>`
  - `_ai_system/tools/validate_report_artifact.py --project <project_name> --strict-delivery`
  - `_ai_system/tools/validate_closeout.py --project <project_name>`
  - `_ai_system/tools/validate_workspace_setup.py --include-user-flow`
- Prefer the consolidated closeout gate: `_ai_system/tools/run_guarded_step.py --project <project_name> --step closeout`.
- Keep these checks separate in the worklog and user-facing status report. Workspace validation does not prove source truth or report quality.
- If any gate fails, keep the report stage at `scaffold`, `evidence_mapping_draft`, or `unverified_draft`, and describe the failed gate instead of saying the report is complete.
- If AI review or optional scoring shows the report is below the intended use, report the concrete improvement opportunities as the next work plan instead of declaring completion.
- Do not change report labels such as `내부 검토용`, `자체 분석용`, `brief`, or `scaffold` merely to bypass a validation threshold. If the PRD/TOC describes a substantial internal review report, the work must satisfy substantial-report gates or be reported as blocked/incomplete.
- Do not use AI-written evidence text, dummy PDFs, placeholder PDFs, shell PDFs, or generic homepage URLs as originals. `report_citable` source records must point to an exact official URL or user-provided/preserved original, plus a verifiable quote, page, article, section, URL, or capture location.
- Do not add validator keywords, source ids, claim ids, or benchmark terms to exact quotes, publisher fields, or metadata to satisfy a gate. This is evidence contamination and should fail the research integrity gate.
- Comparison copies and failed-run files belong under a named `archive/` folder. Active `reports/` should contain deliverables and registers, not `.bak` files.
- Project work should not create ad-hoc Python helpers in the workspace root or system-core folders. If a temporary helper is unavoidable, record its purpose, path, cleanup, and impact in the worklog. Leaving unexpected `.py` files in the root or active project should be treated as a hygiene issue, not as report progress.

## Section-by-Section Drafting Standard

- Substantial reports should be drafted in bounded sections, not generated in one burst.
- Start with scope and methodology, then develop body sections against the TOC and source collection plan.
- Draft legal/regulatory, market, benchmark, structure, risk, and data sections separately when they require different evidence pools.
- Write the executive summary and final recommendations only after the body sections, risk map, appendix plan, and core citations are stable.
- A short brief or scaffold may summarize planned sections, but it must not be represented as a completed internal review report.

## Minimum Research Depth for Substantial Internal Review Reports

For a substantial internal review report, do not treat a thin HTML memo as a completed report. Unless the report PRD explicitly says the output is a short brief, scaffold, or one-page memo, use these minimum targets before calling it internally reviewable:

- at least 8 source records, with exact official URLs, quote/page/section locators, or user-provided/preserved originals,
- at least 6 external/public inventoried originals for market, legal, competitor, or benchmark claims,
- at least 3 domestic official/regulatory/legal sources,
- at least 3 overseas official/company/regulatory benchmark sources when overseas cases are discussed,
- at least 4 substantive tables, figures, charts, matrices, or diagrams,
- a `data_sources/visual_plan.csv` that explains which chapter-level decision each required visual supports,
- at least 1 local `.csv` or `.xlsx` data file, and more when multiple charts or scenarios are used,
- visible report body depth proportionate to the PRD, TOC, and chapter workpacks. Judge depth by answered chapter questions, counterarguments, evidence use, decision usefulness, and visual/data support rather than a fixed character target.

Do not pad prose to cross any numeric length target. If the PRD calls for a shorter brief, use the appropriate label and judge quality by claim coverage, decision usefulness, visual/data support, and source integrity.

If these thresholds are not met, label the artifact as `scaffold`, `brief`, `source collection memo`, or `unverified draft`, not as a completed internal review report.

## Report Stage and Delivery Labels

- Use `scaffold` when only structure or initial prose exists.
- Use `evidence_mapping_draft` when source and claim mapping is in progress.
- Use `unverified_draft` when prose exists but research integrity has not passed.
- Use `internally_reviewable_draft` when major claims are citable but business/legal review remains.
- Use `final_candidate` only after source traceability, claim readiness, citation display, tone, charts, and assumptions have been checked.
- Do not call a report final, fully verified, or ready for submission because workspace validation passed.

## Table, Graph, and Data File Standard

- Every material chart, graph, or quantitative table must be backed by a `.xlsx` or `.csv` file, or by source-record-backed qualitative evidence for non-quantitative diagrams.
- The `.csv` or `.xlsx` must be physically present before a report is described as internally reviewable or complete.
- Store raw and cleaned data under the relevant project `data_sources/` folder.
- Store generated charts under `figures/` and report-ready tables under `tables/`.
- Captions must state the original sources in reader-facing form, whether the data is reported/adjusted/estimated, and which local dataset supports reproduction as `근거 데이터`.
- If a chart or table uses assumptions, link to the relevant rows in `assumptions/assumption_register.md`.
- Do not include decorative charts that do not answer a report question.
- Do not satisfy the visual standard by adding tables only. Use `data_sources/visual_plan.csv` to decide when the report needs a flow diagram, timeline, heatmap, scenario chart, or architecture map.
- If manually compiling a table, create a companion CSV with row-level source ids and confidence labels.
- If a chart is intentionally illustrative and not data-backed, label it as a conceptual diagram rather than a graph, and do not use numeric bars, axes, or market-size labels.
- Follow `_ai_system/governance/05_chart_visualization_rules.md` for chart type selection, color, legend, label contrast, pattern fills, and appendix chart packs.

## Appendix Material Standard

- Use appendices for materials that are too detailed for the main body but important for verification or later reuse.
- A substantial internal review report should normally include:
  - Appendix A: source list or citation details,
  - Appendix B: legal/regulatory issue matrix,
  - Appendix C: benchmark case cards,
  - Appendix D: data tables, chart method notes, or sensitivity tables,
  - Appendix E: glossary.
- Appendix materials may include:
  - source screenshots or captured images,
  - detailed source tables,
  - large market-data tables,
  - full benchmark matrices,
  - legal issue matrices,
  - chart methodology notes,
  - sensitivity tables,
  - alternate charts or scenario views.
- The main body should include the executive version of a chart or table; the appendix may include the full evidence view.
- Appendix images and tables still require `자료:` and, where applicable, `근거 데이터:`.
- Do not use the appendix to hide uncertainty that affects the report conclusion. Important uncertainty must also appear in the main risk/open-question section.

## Appendix Glossary Standard

- Each final report must include an appendix glossary for legal, regulatory, market, technical, financial, domain-specific, and foreign-language terms.
- Glossary entries must include:
  - Korean working term,
  - original term,
  - definition,
  - report context,
  - source id if definition is source-backed,
  - translation or legal-interpretation risk.
- Do not hide important definitional uncertainty in footnotes only; put it in the glossary or legal issue matrix too.

## Report Standard

The first report should be an internal review report. It should include:

- Executive summary.
- Decision questions.
- Business thesis.
- Market and competitor landscape.
- Regulatory landscape.
- Benchmark cases.
- Candidate business structures.
- Risk map.
- Required sandbox special treatments.
- Non-waivable compliance obligations.
- Data gaps.
- Recommended next research.

The report must distinguish:

- `Confirmed evidence`.
- `Reasoned interpretation`.
- `Estimate`.
- `Unresolved issue`.

Before delivery, separately report:

- workspace validation status,
- research integrity status,
- citation/source traceability status,
- remaining legal/business review requirements.

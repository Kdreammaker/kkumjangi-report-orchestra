# Document Adaptation Rules

## Purpose

Use this rule when the user asks to refine, reformat, restructure, convert, or derive a document from an existing file.

Document adaptation is broader than report writing. It covers requests such as:

- polish this existing document,
- make this document fit a target template or document type,
- convert this document into another file type,
- turn this document into a proposal, handout, press release, manual, lesson plan, brief, or report,
- prepare the document for Word, Google Docs, Hancom/HWPX, PDF, HTML, or report factory use.

This rule does not replace report factory rules. It is the intake and decision layer before choosing whether the adapted output should remain an independent document or enter the report factory.

## Supported Input Tiers

Tier 1 inputs are the first supported adaptation targets:

- Markdown (`.md`),
- Word (`.docx`),
- HTML (`.html`, `.htm`),
- plain text (`.txt`).

Tier 2 inputs are supported with explicit limitations:

- PDF (`.pdf`): text extraction, reading order, tables, headers, footers, footnotes, and scanned pages may need render/OCR review.
- PowerPoint (`.pptx`): slide-to-document adaptation is supported, but exact slide layout preservation is a separate presentation task.
- Excel (`.xlsx`, `.xls`, `.csv`): table/data-to-document adaptation is supported, but formulas, sheet intent, and data meaning need review.
- HWPX (`.hwpx`): treat as structured document intake with explicit extraction/render limitations. Do not claim visual parity unless opened/rendered and reviewed.

Unsupported or risky file types require a short plan before editing. HWP (`.hwp`) requires the configured owned converter or a manual preservation plan before editing; do not silently claim HWP-to-HWPX fidelity. Do not silently claim fidelity for formats that have not been inspected.

## Adaptation Modes

Before editing, classify the requested work into one of these modes. Ask only when the user has not already made the mode clear.

| mode | Use when | Default risk |
|---|---|---|
| `light_polish` | The same document should keep its structure and meaning while improving wording, spelling, flow, or consistency. | Low, but protected spans still apply. |
| `format_adaptation` | The document should fit a target template, section structure, style guide, file type, or visual format. | Medium; layout and section movement can change emphasis. |
| `substantive_rewrite` | The document needs stronger logic, sequence, missing context, clearer claims, or reader-fit changes. | High; record what is added, removed, or inferred. |
| `derived_artifact` | The source document becomes a different artifact, such as a report, proposal, manual, lesson, handout, press release, or briefing note. | High; choose the new artifact's preset/style/workflow independently. |

If the user explicitly requests a mode or target, follow it and record the decision. If not, ask a short clarification question covering mode, output file type, target format, reader/use case, and verification level.

## Source Preservation Contract

Default behavior is always:

1. preserve the original input,
2. create a new adaptation plan or manifest,
3. write adapted output as a new file,
4. keep a trace of what changed and what was not verified.

Do not overwrite the user's original file unless the user explicitly asks for in-place editing and the source has been snapshotted or copied first.

Recommended project folders:

- `documents/intake/` for preserved source copies used by adaptation,
- `documents/adaptation_plans/` for plan and manifest files,
- `documents/adapted/` for new adapted outputs,
- `documents/versions/` for preserved versions of adapted outputs.

The `reports/` folder is used only after the user or workflow chooses a report factory route.

## Routing

Start from `tasks/current_task.md` when the source belongs to an existing project. Use `AGENTS.md` only when the project task manifest is missing, ambiguous, or the user asks for routing.

Use `_ai_system/tools/init_document_adaptation.py` when you need a durable starting record. The tool preserves the source copy and writes a plan/manifest; it does not rewrite content.

After intake:

- For independent document refinement, use this rule, the adaptation plan, the selected style profile/register guidance when relevant, and the target format guidance.
- For a new artifact type, choose a document preset from `_ai_system/document_presets/INDEX.json` and record source lineage before drafting.
- For report-style output, route into report factory only after the adaptation plan says the target is a report factory artifact.
- For DOCX delivery from report factory sources, use `_ai_system/tools/export_report_docx.py`; do not assume arbitrary source files can directly use that exporter.
- For HWPX/HWP delivery, first decide whether the target is HWPX-compatible HTML for Hancom import, direct controlled `hwpx-authoring-html.v1` conversion, Report Factory native HWPX export, or HWP-to-HWPX conversion. HWP-to-HWPX and controlled HTML/HWPX conversion use separate entrypoints to the embedded owned engine. `export_report_hwpx.py` automatically adapts Report Factory cover/chapter sources through `report_export_ir.v1`; the user does not need to rewrite those system-authored sources. Only arbitrary external HTML supplied directly to the low-level converter must first be explicitly adapted to the controlled contract. All native delivery claims require recorded open/render evidence.
- For cloud handoff, build a local outbox first and ask for explicit approval before uploading or sharing.

## Protected Spans

Protected spans survive adaptation unless the user explicitly authorizes a correction and the correction is recorded:

- direct quotes,
- numbers, dates, prices, percentages, formulas, and units,
- laws, contract clauses, official titles, names, and proper nouns,
- citations, source locators, URLs, and reference identifiers,
- approval, legal, securities, compliance, or external-public wording,
- user-marked passages that must remain unchanged.

Do not add new factual claims, legal conclusions, investment recommendations, technical promises, or source-backed assertions just to make the document sound more professional. Mark unsupported additions as assumptions, suggestions, or placeholders.

## Output Targets

The target output can be one or more of:

- same file type refined copy,
- DOCX,
- HTML,
- inline-first HTML for Word/Google Docs import testing,
- HWPX-compatible HTML for Hancom import/open testing,
- native HWPX through the embedded owned converter when the controlled authoring contract or Report Export IR path is used and open/render evidence is recorded,
- report factory chapter fragments,
- PDF-ready source,
- a preset-shaped document such as proposal, manual, curriculum, press release, investor brief, research note, or report,
- a summary, handout, checklist, briefing memo, or other derived artifact.

When target file type matters, record the exact target and verification method. File creation is not proof of fidelity.

## Verification

Report verification separately:

- original preserved,
- adaptation plan/manifest created,
- requested mode and target recorded,
- protected spans preserved or intentionally changed with rationale,
- output file opens,
- target format/template/preset followed,
- meaning changes or unsupported additions reviewed,
- Word/Google Docs/Hancom/PDF/import fidelity checked when relevant.

For Tier 2 inputs, also record extraction/render limitations. For DOCX/PDF/Google Docs/HWPX/Hancom targets, say "compatibility-first" or "verified in this environment" rather than "fully compatible" unless a human review or renderer/open evidence supports the claim.

## Public/Private Boundary

Document adaptation records may contain user file names, source paths, document content, or private goals. They belong inside the local user project and must not be included in system-core packages or public release seeds.

The generic rules, templates, and tools can be public. User-specific adaptation plans, preserved source copies, adapted outputs, render evidence, and worklogs are project artifacts and stay local unless the user explicitly approves sharing.

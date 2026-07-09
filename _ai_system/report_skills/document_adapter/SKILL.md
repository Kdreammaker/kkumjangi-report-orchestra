---
name: document_adapter
description: Adapt an existing document to a requested format, file type, reader, or derived artifact while preserving the original.
triggers:
  - document adaptation
  - existing document
  - polish document
  - reformat document
  - convert document
  - derived artifact
---

# Document Adapter

## Mission

Turn an existing user document into a safer, better-shaped output for a requested purpose without treating the original as disposable.

Use this skill for existing `.md`, `.docx`, `.html`, `.txt`, `.pdf`, `.pptx`, `.xlsx`, `.xls`, or `.csv` files when the user asks for polishing, restructuring, format matching, file-type conversion, or a derived artifact.

## Required First Steps

1. Read `tasks/current_task.md` when the source belongs to a project.
2. Read `_ai_system/governance/17_document_adaptation_rules.md`.
3. If no adaptation plan exists, use `_ai_system/tools/init_document_adaptation.py` or manually create equivalent plan and manifest records.
4. Preserve the original before editing or converting.

## Mode Selection

Use one mode:

- `light_polish`: improve wording while keeping meaning and structure.
- `format_adaptation`: fit a target template, section structure, file type, or style guide.
- `substantive_rewrite`: improve logic, ordering, missing context, or reader fit.
- `derived_artifact`: create a different artifact type from the source.

Ask the user when the mode, target output, reader/use case, or verification standard is unclear. If the user explicitly states the target, proceed and record unresolved assumptions.

## Output Contract

- Do not overwrite the source unless the user explicitly asked for in-place editing and the source copy is preserved.
- Write new outputs under `documents/adapted/` or `documents/versions/` unless the chosen workflow routes into `reports/`.
- Keep adaptation plans and manifests under `documents/adaptation_plans/`.
- If the output becomes a report factory artifact, create or update the relevant PRD/worklog and route through report factory rules.
- If the output is DOCX/PDF/HTML, report whether the file was rendered/opened or only structurally generated.

## Protected Span Rules

Preserve direct quotes, numbers, dates, formulas, units, statutes, contracts, names, citations, source locators, approval wording, and user-marked fixed text.

Do not add unsupported facts or claims while making the document sound better. Mark suggested additions as assumptions, placeholders, or review-needed text.

## Completion Report

Report:

- source file and preserved copy,
- adaptation mode and target output,
- files created,
- what was changed at a high level,
- what was not verified,
- remaining import/render/fidelity limitations.

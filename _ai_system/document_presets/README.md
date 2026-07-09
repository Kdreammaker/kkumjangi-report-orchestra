# Document Presets

This folder contains modular document-type presets for the report production
system. A preset is not only a visual theme. It is a routing bundle that tells
AI which PRD questions, stage overlays, quality checks, and cover defaults are
relevant for a document type.

The initial modules mirror the existing `domain_presets` in
`_ai_system/workspace_config.json`. Extension modules add more document-type
guidance assets without changing workflow or tool behavior yet.

## Files

- `INDEX.json`: compact routing index for AI and tools.
- `CODEMAP.md`: human-readable map of preset modules and read boundaries.
- `LIST_STYLE_PRESETS.md`: human-readable multi-level list marker guidance.
- `list_style_presets.json`: machine-readable list marker contract for HTML/DOCX/HWPX-compatible export paths.
- `<preset_id>/preset.json`: preset metadata and stage overlay paths.
- `<preset_id>/prd_questions.md`: questions to ask before PRD drafting.
- `<preset_id>/stage_overlays.md`: TOC, workpack, visual/data, and review notes.
- `<preset_id>/design_patterns.md`: concrete document layout patterns for extension presets.
- `<preset_id>/validation_checklist.md`: preset-specific review checklist.

## Read Budget

AI should read `INDEX.json` first, then only the selected preset's
`preset.json` and the stage-specific files listed there. Do not read every
preset folder by default.

When a document relies on nested numbered or bulleted lists, read
`LIST_STYLE_PRESETS.md` and select a declared list preset during PRD/design.
The default formal hierarchy is `I -> A -> 1 -> a`; guide documents usually
start from `guide_outline`, procedure/manual documents from `procedure_steps`,
administrative/review documents may use `administrative_outline`, and compact
symbol-only notes from `symbol_bullets`. HWPX/Hancom-specific Korean markers
are recorded as target overrides and verified separately rather than treated as
cross-target defaults.

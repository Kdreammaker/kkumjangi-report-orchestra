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
- `<preset_id>/preset.json`: preset metadata and stage overlay paths.
- `<preset_id>/prd_questions.md`: questions to ask before PRD drafting.
- `<preset_id>/stage_overlays.md`: TOC, workpack, visual/data, and review notes.
- `<preset_id>/design_patterns.md`: concrete document layout patterns for extension presets.
- `<preset_id>/validation_checklist.md`: preset-specific review checklist.

## Read Budget

AI should read `INDEX.json` first, then only the selected preset's
`preset.json` and the stage-specific files listed there. Do not read every
preset folder by default.

# Product Manual Stage Overlays

## Workflow Mode And Stage Depth

- Default mode: `standard`, with specialized task/procedure structure.
- Use PRD, user/environment/version scope, task outline, procedure drafting, troubleshooting review, style pass, versioning, and delivery readiness.
- Replace report chapter workpacks with task blocks, setup paths, troubleshooting cases, FAQ entries, and version notes.
- Chapter 0, thesis-style skeleton, and broad market analysis are optional and usually unnecessary for a manual.
- If the manual is derived from a report, proposal, or PRD, reuse only stable product facts and revalidate procedures, screenshots, warnings, compatibility notes, and support boundaries.

## TOC

- Organize by user task, setup path, configuration area, operation workflow, troubleshooting case, FAQ, and version notes.
- Put prerequisites and caution notes before steps that depend on them.
- Lead each task with purpose, prerequisites, expected result, and then the procedure.

## Authoring Structure

- Default paragraph mode: bullet-first and step-first.
- Use prose only for short context, caution rationale, recovery explanation, or concept clarification that prevents user error.
- Use `procedure_steps` for procedures, setup paths, and troubleshooting branches; use `symbol_bullets` for notes, examples, and quick checks.
- For DOCX targets, default to Malgun Gothic. For HWPX-compatible manuals, record Hancom font fallback and verify warnings, command/path wrapping, and nested steps in Hancom.

## Workpack

- Require numbered procedures, expected results, error states, prerequisites, permissions, and rollback or recovery notes where relevant.
- Avoid mixing marketing claims with user instructions.

## Visual/Data

- Prefer annotated screenshots, flow diagrams, configuration tables, decision trees, error-code tables, and quick-reference checklists.
- Every visual should map to a concrete task or troubleshooting need.

## Layout/Export

- Use manual-style hierarchy: numbered procedures, caution/warning boxes, screenshot captions, FAQ tables, troubleshooting tables, and version notes.
- Keep procedure tables, error-code tables, and configuration tables within Word page width; split long workflows into smaller task blocks.
- Use static screenshots/images with captions and alternative descriptions; avoid interactive HTML, viewport-dependent layouts, and complex absolute positioning.
- Make long commands, file paths, URLs, and error messages wrap without breaking the page.
- DOCX/PDF/HWPX-compatible conversion requires separate export validation; this preset does not guarantee conversion success.

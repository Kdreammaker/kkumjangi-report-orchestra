# Guide Document Stage Overlays

## Workflow Mode And Stage Depth

- Default mode: `standard`, with guide-specific structure and source-preserving adaptation.
- Use PRD, source preservation plan, guide outline, section drafting/adaptation, visual/table cleanup, review, export validation, and versioning.
- Replace report chapter workpacks with guide sections, rule groups, examples, procedures, locked notes, glossary entries, and appendix references.
- Chapter 0, thesis-style argument skeleton, and broad market analysis are optional and usually unnecessary unless the guide itself is report-shaped.
- If the guide is derived from existing documents, preserve original wording unless the PRD explicitly allows rewrite. Record what was normalized, moved, merged, or marked as locked/internal.

## TOC

- Organize by reader task, rule domain, reference theme, sequence of use, or authority level.
- Keep title hierarchy conservative: part, chapter, section, subsection, appendix.
- Use `guide_outline` for nested guide rules by default; use `formal_outline` when the document needs formal legal, academic, or book-like outline discipline.
- Use `symbol_bullets` for examples, options, notes, and compact scan lists.
- Lead each guide section with rule/status or user task first, then scope, examples, exceptions, and owner/review notes.

## Authoring Structure

- Default paragraph mode: bullet-first for rules, examples, exceptions, and checklists; prose for source background, rationale, and transition notes.
- Use `guide_outline` for rule hierarchy, `procedure_steps` for task sequences, and `administrative_outline` when the guide is an institutional review/approval guide with Hancom-oriented delivery.
- Keep locked/internal/approval-required material in explicit slots; do not hide it in prose.
- For HWPX-compatible guides, record Hancom font fallback and any Korean marker overrides in `reports/report_design.md` and verify in Hancom.

## Workpack

- Each guide section should state purpose, scope, source basis, rule/guidance status, examples, exceptions, and review owner when relevant.
- Mark producer-only, locked, internal-only, approval-required, or non-public material visibly.
- Do not collapse source material into a summary unless the user asked for summarization.
- Track protected spans such as names, terminology, proper nouns, version labels, approved copy, quotes, and source-backed claims.

## Visual/Data

- Prefer semantic tables, definition lists, checklists, decision tables, simple flow diagrams, and callouts.
- Use inline-first HTML for headings, lists, tables, captions, and locked/internal notices when Word import is expected.
- Keep complex CSS grid/flex, CSS-only markers, and background-heavy effects out of export-oriented guide content.

## Layout/Export

- Use a clean reference-document layout: metadata block, table of contents when useful, guide sections, examples, locked notes, glossary, and appendices.
- For Word-import HTML, keep page background white and put core styles inline on headings, paragraphs, lists, tables, callouts, and badges.
- For native DOCX, use the selected list preset so nested hierarchy is not flattened.
- DOCX/PDF/Google Docs/HWPX-compatible conversion requires separate export validation; this preset improves compatibility but does not guarantee conversion success.

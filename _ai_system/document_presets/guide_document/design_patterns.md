# Guide Document Design Patterns

## Document Purpose And Reader

- Purpose: Create a guide, playbook, producer bible, style guide, operating guide, rulebook, or durable reference from new or existing material.
- Primary readers: producers, editors, operators, writers, reviewers, internal teams, partners, or approved external readers.
- The document should preserve core content while making structure, status, and reuse rules easier to scan.

## Recommended Document Structure

- Metadata block: title, guide type, version, owner, source basis, update date, confidentiality, and approval status.
- Scope and authority: what this guide governs, what it does not govern, and who may interpret or update it.
- Core principles or canon/rules: stable rules, approved terminology, definitions, and non-negotiable constraints.
- Working guidance: procedures, usage examples, exception handling, decision rules, and review checkpoints.
- Locked/internal material: producer-only notes, unresolved issues, spoiler-sensitive notes, or approval-required sections.
- Reference sections: glossary, table index, source list, appendices, and change log.

## Recommended Layout Blocks

- Metadata table with inline borders and plain labels.
- Table of contents for long guides, generated conservatively from headings.
- Rule cards or callouts only when they remain semantic HTML and inline-first.
- Decision tables for allowed/prohibited usage, status, and exception handling.
- Locked or producer-only blocks with strong visual treatment, but no background-heavy page effects.
- Appendix tables for source mapping, terminology, and version history.

## Design Application Priorities

- Preserve source wording unless the PRD explicitly permits rewrite, compression, or synthesis.
- Make producer-only, locked, internal-only, and approval-required material visibly distinct.
- Use `guide_outline` for nested guide hierarchy and `symbol_bullets` for examples/options unless the PRD selects another preset.
- Keep headings and list hierarchy readable after Word/Google Docs import; avoid marker schemes that depend only on CSS counters.
- Use tables for rules, terminology, and status comparisons when paragraph prose would hide important distinctions.
- Use captions or notes to distinguish source-backed rule, editorial interpretation, and open issue.

## Tables, Figures, And Captions

- Metadata, rule, and glossary tables should fit within Word page width.
- Long names, terminology, and local path/source labels must wrap without breaking table layout.
- Figures should be static images or simple diagrams with captions, not JavaScript-only visuals.
- Captions should identify whether a table/figure is source material, interpretation, or production guidance.

## AI Judgment Needed

- Decide whether a section should be preserved verbatim, lightly normalized, restructured, summarized, or marked for human review.
- Decide whether material is public-facing, internal, producer-only, locked, draft, obsolete, or unresolved.
- Decide whether a rule belongs in the main guide, glossary, appendix, example block, or change log.
- Decide whether the selected list preset still serves the reader after import/export checks.

## Deferred Export-Native Features

- Do not claim automatic Word TOC, cross-references, page fields, index generation, tracked changes, or protected/locked Word sections.
- Do not claim perfect Google Docs or Word import fidelity for custom markers, callouts, or table layouts.
- Treat native DOCX templates, automatic index creation, and permission/protection settings as separate follow-up work.

## Word/DOCX Compatibility

- Keep the page background white and put core heading, table, callout, list, caption, and badge styling inline for HTML import targets.
- Prefer standard nested lists, simple tables, static images, and conservative page widths.
- Avoid complex grid/flex-only layouts, CSS counters as the only marker source, CSS variables as the only color source, and background-heavy effects.
- Use native DOCX export for stronger list and table fidelity when DOCX is the target.
- Export validation is required before claiming delivery readiness.

## Patterns To Avoid

- Replacing the source with an AI summary when the user asked for format cleanup.
- Hiding producer-only or locked content in weak text labels.
- Turning unresolved notes into final rules.
- Mixing source-backed canon/rules with speculation without visible status labels.
- Creating a worldbuilding-only core template instead of using this broader guide preset with a subtype.

## Reviewer Checkpoints

- Is the guide subtype, reader, authority level, and confidentiality clear?
- Are original wording and protected spans preserved at the required strength?
- Are locked/internal/producer-only sections visually strong and clearly labeled?
- Are nested lists using a declared list style preset?
- Are tables, callouts, and captions inline-first and Word-import friendly?
- Are export-native features described as deferred unless actually verified?

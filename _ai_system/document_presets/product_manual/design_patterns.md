# Product Manual Design Patterns

## Document Purpose And Reader

- Purpose: Create a product manual, user guide, setup guide, administrator guide, or support reference.
- Primary readers: end users, installers, administrators, operators, trainers, or support teams.
- The document should help users complete tasks safely and troubleshoot issues without promotional language.

## Recommended Document Structure

- Product/version scope: product name, edition, platform, supported version, and update date.
- Before you begin: prerequisites, permissions, supported environments, and required materials.
- Numbered procedures: task purpose, steps, expected result, and recovery notes.
- Warning/caution/note system: safety, irreversible changes, compatibility limits, and tips.
- Screenshots and examples: annotated images with captions and alternative descriptions.
- FAQ: common questions grouped by user task.
- Troubleshooting table: symptom, likely cause, check, resolution, and escalation path.
- Version notes: changes, deprecated features, unsupported cases, and known limitations.

## Recommended Layout Blocks

- Numbered procedure blocks with consistent step labels.
- Warning, caution, and note boxes with distinct wording and severity.
- Screenshot blocks with caption, alt text, and related step number.
- Troubleshooting table with short rows and actionable resolution text.
- Quick-reference tables for commands, settings, or environment requirements.

## Design Application Priorities

- Use warning boxes for safety, irreversible action, data loss, security, or compliance risk.
- Use caution boxes for compatibility, configuration, performance, or recoverable-but-costly error risk.
- Use note boxes for tips, optional context, shortcuts, or non-risk background.
- Place warning or caution blocks before the risky action and add recovery or expected-result text after the action.
- Use troubleshooting tables when users need to compare symptom, likely cause, check, resolution, and escalation path.
- Use FAQ blocks for recurring conceptual questions that do not belong inside numbered procedures.
- Split or wrap long commands, paths, version names, and compatibility tables before they force narrow columns or horizontal scrolling.

## Tables, Figures, And Captions

- Screenshots must have captions that explain the user action, not just the screen name.
- Troubleshooting tables should avoid dense paragraphs in each cell.
- Configuration tables need field name, allowed value, default, required/optional status, and notes.
- Flow diagrams should show decisions or recovery paths that text alone makes hard to follow.

## AI Judgment Needed

- Decide whether a risk deserves warning, caution, note, prerequisite, or unsupported-case treatment.
- Decide whether a procedure needs screenshots, troubleshooting rows, FAQ entries, or recovery notes.
- Decide whether command, path, version, or compatibility details belong in the step body, quick-reference table, or appendix-style reference.
- Decide whether a table should be split by platform, version, role, or task to keep export layout readable.

## Deferred Export-Native Features

- Do not claim Word-native cross-references, field codes, generated DOCX captions, page fields, running headers, or automatic index support.
- Do not claim automated screenshot capture, interactive demos, or platform-specific installer automation.
- Treat native help-center publishing, searchable manual packaging, and versioned DOCX template automation as separate work outside this module.

## Word/DOCX Compatibility

- Keep procedure, configuration, FAQ, and troubleshooting tables within Word page width.
- Long commands, file paths, URLs, and error messages must wrap without breaking layout.
- Use static screenshots/images; avoid interactive demos, viewport-dependent layouts, and complex absolute positioning.
- Use fixed-width text only for short commands or code snippets, not full paragraphs or wide tables.
- DOCX/PDF conversion still requires separate export validation; this pattern does not guarantee conversion success.

## Patterns To Avoid

- Marketing copy inside procedures.
- Missing expected results after numbered steps.
- Screenshots without captions or relation to a step.
- Warning/caution boxes placed after the risky action.

## Reviewer Checkpoints

- Are numbered procedures complete with prerequisites, steps, expected results, and recovery notes?
- Are warning/caution/note boxes used consistently and before risky actions?
- Are screenshot captions and troubleshooting tables useful for real user tasks?
- Are long commands, paths, and error messages export-safe?
- Is the covered product/version/platform unambiguous?
- Are compatibility, version, and command references split or wrapped before they create Word table-width risk?

# Product Manual Validation Checklist

- The covered product, version, platform, and audience are explicit.
- Procedures include prerequisites, steps, expected results, and error/recovery guidance.
- Installation, setup, configuration, FAQ, troubleshooting, and version notes are covered when in scope.
- Warnings, limitations, and unsupported cases are visible before risky actions.
- Screenshots, diagrams, and tables support actual user tasks.
- The document avoids promotional language where instructions are needed.
- Numbered procedures, warning boxes, screenshot captions, FAQ tables, and troubleshooting tables are formatted consistently.
- Warning, caution, and note blocks use distinct severity rules and appear before the risky or irreversible action.
- Troubleshooting table, FAQ, procedure steps, and compatibility references are placed where users naturally need them.
- Long commands, paths, version names, error messages, and compatibility tables are checked for wrapping before export.

## Prohibited Style and Judgment Patterns

- Do not mix marketing copy with procedure text; keep benefits, positioning, and release messaging separate from prerequisites, steps, expected results, and recovery guidance.
- Do not turn instructions into promises about performance, ease, safety, or compatibility unless the claim is verified for the stated product version and platform.
- Do not skip error cases or unsupported paths because the product story sounds cleaner without them.

## Design And Export-Safe Checkpoints

- AI judgment records why a risk is a warning, caution, note, prerequisite, or unsupported case.
- AI judgment decides whether platform, version, command, or compatibility detail belongs in the body, quick reference, or appendix-style reference.
- Appendix or split-table candidates are marked as export review needs, not as guaranteed DOCX/PDF behavior.
- Deferred export-native features remain deferred: Word field codes, generated captions, page fields, cross-references, running headers, automated screenshot capture, and help-center packaging are not claimed.

## Export Readiness Checks

- Tables remain readable within Word page width, and long commands, paths, URLs, and error messages can wrap.
- Screenshots, images, and charts are static assets with captions and alternative descriptions.
- Interactive HTML, viewport-dependent layouts, and complex absolute positioning are avoided for exportable outputs.
- DOCX/PDF export success is not assumed until export validation is run separately.

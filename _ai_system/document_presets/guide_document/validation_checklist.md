# Guide Document Validation Checklist

- The guide subtype, audience, owner, source basis, version, confidentiality, and approval status are explicit.
- The adaptation preserves original wording unless the PRD authorized rewrite, compression, or synthesis.
- Producer-only, locked, internal-only, approval-required, unresolved, and obsolete material is visibly labeled.
- Headings, sections, examples, glossary entries, and appendices use a consistent guide hierarchy.
- The selected list preset is recorded, and nested lists do not flatten important structure.
- Tables, callouts, captions, and metadata blocks are readable within Word page width.
- Source-backed rules, editorial interpretation, examples, and open issues are visibly distinct.
- No public-ready claim is made without confidentiality and export checks.

## Prohibited Style and Judgment Patterns

- Do not remove content because it is awkward, repetitive, or hard to classify unless the user explicitly approves removal.
- Do not convert a guide into a short summary when the user requested format cleanup.
- Do not relabel speculation or unresolved notes as authoritative rules.
- Do not hide producer-only or locked content in plain body text.

## Design And Export-Safe Checkpoints

- AI judgment records whether sections were preserved, moved, lightly normalized, summarized, or marked for human review.
- AI judgment records why any material is treated as public-facing, internal, producer-only, locked, draft, obsolete, or unresolved.
- `guide_outline`, `formal_outline`, `procedure_steps`, or `symbol_bullets` is selected where nested lists matter.
- Deferred export-native features remain deferred: automatic Word TOC, index generation, protected Word sections, tracked changes, page fields, and cross-references are not claimed.

## Export Readiness Checks

- Inline-first HTML is used for headings, paragraphs, lists, tables, captions, callouts, metadata, and locked/internal badges when Word import is expected.
- Native DOCX export uses multi-level list numbering where supported.
- Static images or simple table/diagram structures are used instead of JavaScript-only visuals.
- DOCX/PDF/Google Docs export success is not assumed until export validation is run separately.

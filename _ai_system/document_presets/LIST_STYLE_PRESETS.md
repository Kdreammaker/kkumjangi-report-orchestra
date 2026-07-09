# List Style Presets

Use this contract when a document needs multi-level numbered or bulleted
lists that should survive HTML preview, Word import, Google Docs import,
Hancom/HWPX-oriented import, and native DOCX export as consistently as
practical.

The machine-readable source is `list_style_presets.json`.

## Presets

| Preset | Use When | Level Order |
|---|---|---|
| `formal_outline` | Formal reports, academic/professional documents, book outlines, and long hierarchy. | `I -> A -> 1 -> a` |
| `guide_outline` | Guide documents, rulebooks, producer notes, examples, and nested guidance. | `A -> A) -> a) -> (a)` |
| `procedure_steps` | Manuals, procedures, setup paths, troubleshooting, and task checklists. | `1 -> 1) -> a) -> (a)` |
| `administrative_outline` | Decision-first administrative reviews, proposals, regulatory opinions, meeting notes, and institutional memos. | `1. -> 1) -> A. -> a)` with HWPX marker overrides |
| `symbol_bullets` | Symbol-only notes, options, examples, and compact scan lists. | `• -> ◦ -> ▪ -> -` |

## Authoring Rules

- Pick a list preset during PRD/design when the document relies on nested
  lists. If the user explicitly requests a different marker set, record that
  exception in the PRD or design file.
- The default formal outline order is fixed as `I -> A -> 1 -> a`.
- Cross-target letter markers use the English alphabet. Do not use Korean
  alphabetic sequence markers as the default marker sample because Word/Google
  Docs import behavior is less predictable.
- For HWPX/Hancom targets, record Korean marker overrides such as `가.` or
  `가)` in the report design file and verify them in Hancom before
  delivery-ready claims. `administrative_outline` carries HWPX marker samples
  for this purpose while keeping DOCX/Google Docs defaults stable.
- Allowed parenthesis forms are suffix `)` and wrapped `()`.
- Symbol-only lists should use common Word/Google Docs friendly symbols first:
  `•`, `◦`, `▪`, and `-`.
- In HTML, keep `data-list-preset="<preset_id>"` on the root list and write
  list intent inline where practical, such as `list-style-type`, margins, and
  spacing. For marker forms like `A)` and `(a)`, native DOCX export may preserve
  the marker more accurately than HTML import.
- In DOCX export, use native multi-level numbering where available. Do not
  flatten nested lists into one-level bullets or plain text.
- HWPX-compatible HTML is an authoring/import target, not proof of native HWPX
  file creation. Record the HWPX conversion or open-check evidence separately.
- This contract improves compatibility; it does not guarantee perfect visual
  parity across Word, Google Docs, LibreOffice, Hancom, and browser HTML.
  Record export verification before delivery-ready claims.

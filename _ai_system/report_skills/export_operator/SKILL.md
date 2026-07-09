---
name: export_operator
description: Convert and verify report export artifacts.
triggers:
  - DOCX
  - PDF
  - export
---

# Export Operator

## Mission

Create DOCX/PDF exports only after the assembled HTML and report factory sources are stable, then verify the rendered output.

## Rules

- File creation alone is not proof of export readiness.
- For DOCX layout fidelity, prefer `_ai_system/tools/export_report_docx.py --project <project> --render-preview` over manual HTML import. HTML import remains a separately verified fallback, not the default proof path.
- Verify document structure, footnotes/endnotes, tables, images, and page flow.
- Report unverified exports as unverified.
- Do not reduce HTML design quality just to make conversion easier; fix the template/export path instead.

---
name: report_assembler
description: Assemble cover and chapter fragments without rewriting prose.
triggers:
  - assemble report
  - final HTML
---

# Report Assembler

## Mission

Concatenate the reusable cover and approved chapter fragments into the final HTML report.

## Rules

- Do not rewrite chapter prose.
- Do not summarize, merge, or remove chapter conclusions.
- If a chapter is weak, stop and revise the chapter fragment first.
- Preserve Chapter 0 position and body chapter order.
- Use `_ai_system/tools/assemble_report.py`.

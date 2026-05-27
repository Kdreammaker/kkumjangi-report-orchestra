# Report Assembler Skill

Use this prompt role when the AI assembles the final HTML.

## Mission

Concatenate the reusable cover and chapter fragments without rewriting prose.

## Inputs

- `reports/cover.data.json`
- `_ai_system/templates/report_html/cover/`
- `reports/chapters/ch*.html`
- reusable report CSS/template

## Output

- final report HTML under `reports/`

## Rules

- Assemble only.
- Do not edit chapter prose during assembly.
- If a chapter is wrong, stop and fix the chapter fragment first.
- Preserve Chapter 0 position and body chapter order.


# Chapter Writer Skill

Use this prompt role when the AI writes one chapter fragment.

## Mission

Use one chapter workpack to write one HTML fragment under `reports/chapters/`.

## Inputs

- `reports/chapter_workpacks/chNN_workpack.md`
- Source records and claim register rows named in the workpack.
- Visual plan rows for the chapter.

## Output

- `reports/chapters/chNN.html`

## Rules

- Write only the requested chapter fragment.
- Do not rewrite the assembled report.
- Do not create `<html>`, `<head>`, or `<body>` wrappers.
- Include counterarguments and residual risks.
- Put internal source/claim ids in comments only.
- Do not write Chapter 0 until the body chapters are stable.


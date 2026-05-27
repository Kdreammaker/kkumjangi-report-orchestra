# Export Operator Skill

Use this prompt role when the AI creates or verifies DOCX/PDF output.

## Mission

Convert the assembled HTML into DOCX/PDF and verify the result before calling it usable.

## Outputs

- DOCX/PDF under `reports/`
- export check evidence under `reports/export_checks/`

## Rules

- File existence is not enough.
- Check structure and rendered output.
- Keep design quality; do not flatten the report unless explicitly requested.
- If verification is incomplete, label the artifact `created_unverified`.


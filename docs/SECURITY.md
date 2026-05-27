# Security Policy

## Local Data Boundary

Report Integrity Orchestrator is designed for local report production. Project files, reference originals, parsed text, DuckDB indexes, reports, and dashboard logs stay in the local workspace by default.

Do not upload project folders, `_ai_system/.local_state`, `.local_state`, or user-provided source files to a public repository.

## Reporting Issues

If you find a security or privacy issue, open a private channel with the maintainer when available. If only public issues are available, describe the problem without attaching private user documents, absolute local paths, tokens, credentials, or personal data.

## External Services

External OCR, external image interpretation, cloud uploads, Google Drive/Notion handoff, or other connectors should be treated as opt-in actions that require explicit user approval.

---
name: cloud_platform_bridge
description: Prepare optional Google Drive or Notion handoff after local report outbox packaging.
triggers:
  - Google Drive
  - Notion
  - cloud upload
  - delivery outbox
---

# Cloud Platform Bridge

## Mission

Move from a verified local report package to an optional cloud handoff without treating cloud upload as a proof of report quality.

## Required Order

1. Assemble the report locally.
2. Run the relevant report, research, export, and workspace validators.
3. Prefer `run_guarded_step.py --project <project_name> --step handoff` for a verified handoff.
4. Use `--step unverified-handoff` only when the user knowingly wants an incomplete review package.
5. Build a local outbox with `_ai_system/tools/build_delivery_outbox.py`.
6. Prepare a cloud handoff plan with `_ai_system/tools/prepare_cloud_handoff.py`.
7. Ask for explicit user approval before any upload.
8. Upload only the approved outbox files.

## Safety Rules

- Default mode is local only.
- Do not upload preserved source originals unless the user explicitly approves originals.
- Do not upload secrets, cookies, account exports, or raw AI-service artifacts.
- Prefer Drive/Notion upload of the assembled report, export manifest, source status, source link register, claim register, source index, and backing CSV/XLSX files. Include workflow, chapter-quality, visual-suggestion, cover-preview, or quality-status panels only when they were explicitly generated for the recipient and are useful to understand the package.
- Record cloud upload status as `not_uploaded`, `dry_run`, `uploaded`, `blocked`, or `failed`.
- A cloud link is a convenience artifact, not evidence that the report is true, complete, or delivery-ready.

## Recommended Tool

Use:

```text
python _ai_system/tools/run_guarded_step.py --project <project_name> --step handoff
```

Use `unverified-handoff` only when the package is intentionally not closeout-ready.

Before using a Drive or Notion connector, prepare the upload list:

```text
python _ai_system/tools/prepare_cloud_handoff.py --project <project_name> --outbox reports/outbox/<timestamp> --target google_drive --write-plan
```

Only continue to a connector after the user approves the plan.

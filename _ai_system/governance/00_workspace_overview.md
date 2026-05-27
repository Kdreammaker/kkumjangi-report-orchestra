# Workspace Overview

## Purpose

This workspace is a local report-production operating system. It helps AI assistants create stronger reports by breaking work into planning, evidence collection, chapter writing, visual/data support, assembly, export, and validation.

The system core is domain-independent. Client, industry, regulator, and project-specific context belongs in:

- project folders under `00_사용자_작업공간/`,
- project PRDs and source plans,
- `_ai_system/workspace_config.local.json` for local-only exceptions,
- optional design systems under `_ai_system/design_systems/`.

## Root Layout

The root folder should stay simple:

- `README.md`
- `INSTALL.md`
- `START_HERE.html`
- `AGENTS.md`
- `VERSION.json`
- `CHANGELOG.md`
- `LICENSE`
- `docs/`
- `00_사용자_작업공간/`
- `_ai_system/`

GitHub/ZIP system-core packages should not include active user projects or private source material.

## User Workspace

Projects live under:

`00_사용자_작업공간/`

Each project should contain:

- dashboard,
- source drop zone,
- reference library launcher,
- references and preserved originals,
- source index,
- claim register,
- assumption register,
- report PRD,
- drafts,
- reports,
- data sources,
- context packets,
- worklogs.

## Report Production Tracks

Typical tracks include:

- business or market strategy review,
- legal or policy analysis,
- investment or partnership decision memo,
- product/operations feasibility report,
- regulatory or institutional risk report,
- benchmark-heavy comparison report,
- technical implementation review.

The exact domain is supplied by the user and the project PRD, not by the system core.

## Status Lookup

Do not infer report status from file names alone. Use:

- `python _ai_system/tools/report_gate_status.py --project <project_name>`
- `python _ai_system/tools/validate_report_factory.py --project <project_name> --strict`
- `python _ai_system/tools/run_guarded_step.py --project <project_name> --step closeout`

Optional advisory status:

- `python _ai_system/tools/report_quality_score.py --project <project_name>`

Workspace validation proves the workspace is runnable. It does not prove report content, source truth, or legal/business accuracy.

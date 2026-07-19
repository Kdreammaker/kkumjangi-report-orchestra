# Environment and Runtime Guide

## Purpose

This folder records the minimum local setup needed for the workspace. It is not tied to one AI service. Codex, Claude, Antigravity, or another AI assistant should use these notes when setting up the workspace on a new PC, installing packages, or deciding where runtime artifacts belong.

## Required Baseline

- Windows PC with access to the workspace folder.
- Python 3.11 or later.
- Ability to open local `.html`, `.vbs`, and `.bat` files.
- Browser capable of opening `http://127.0.0.1:<port>` for the project dashboard app.

## Python Packages

Install packages from:

```text
_ai_system/environment/requirements.txt
```

Current required packages:

- `pypdf`: PDF text extraction for reference intake.
- `docling`: local normalization for supported reference files such as PDF, PPTX, DOCX, XLSX, PNG, and JPG.
- `duckdb`: local project context indexing and focused lookup over inventories, normalized units, claims, and workpacks.
- `python-docx`: native DOCX package generation for report exports.

Local runtime assets installed by the same installer:

- Apache ECharts: local chart rendering asset under `_ai_system/runtime/vendor/echarts/`.
- Pretendard: local Korean UI/report font under `_ai_system/runtime/fonts/pretendard/`.

Install and verify them with:

```text
python _ai_system/tools/install_runtime_dependencies.py
```

If packages are already installed and only verification is needed:

```text
python _ai_system/tools/validate_local_runtime.py
```

Do not install undocumented packages as a hidden dependency.

## Optional Owned HWP/HWPX Engine

HWP-to-HWPX conversion uses the separately distributed project-owned Python/rule engine. Report Orchestra calls the canonical engine CLI and does not copy its parsing or writer rules.

Set `OWNED_HWP_HWPX_CLI` to `convert_owned_hwp_to_hwpx.py`, then verify it with:

```text
python _ai_system/tools/convert_hwp_to_hwpx.py --probe
```

The engine is optional for ordinary report authoring and DOCX export. A requested HWP-to-HWPX conversion must stop with `owned_hwp_hwpx_engine_not_configured` when this companion runtime is unavailable.

## Local Processing Boundary

Docling, DuckDB, python-docx, Apache ECharts, and Pretendard are used as local tools/assets. Reference originals stay in the project folder, Docling writes derived normalized files under `references/normalized/`, DuckDB writes a local index under `project_state/context_index.duckdb`, python-docx writes local DOCX packages during export, ECharts renders charts without a CDN call, and Pretendard is served from the local runtime folder.

These derived files help the AI read less context, but they do not replace the original-file ledger in `references/reference_inventory.csv`. External OCR, cloud upload, or external VLM/image-description workflows are outside the default boundary and require explicit user approval.

## Runtime Artifact Policy

Tool-created folders are not user workspaces. If a browser or AI tool creates a runtime folder in the root, move it after use into `_ai_system/runtime/`.

Examples:

- Root `.playwright-mcp/` should be moved to `_ai_system/runtime/playwright-mcp/`.
- Temporary screenshots or logs created only for AI verification may be stored under `_ai_system/runtime/` unless they become report evidence.
- Evidence used in a report must be copied into the relevant project `evidence/` folder and cited through the source/index workflow.

## New PC Setup

1. Open the workspace root in the chosen AI service.
2. Ask the AI to read `AGENTS.md`.
3. Ask the AI to read `_ai_system/governance/09_workspace_setup_and_migration_rules.md`.
4. Ask the AI to verify Python and install/verify the packages listed in `requirements.txt`.
5. Ask the AI to run `_ai_system/tools/validate_workspace_setup.py --include-user-flow` or perform the equivalent checks in `_ai_system/governance/09_workspace_setup_and_migration_rules.md`.
6. Ask the AI to report `passed`, `fixed during check`, `warning / residual risk`, and `not tested` separately.
7. For dashboard setup, ask the AI to check all three levels where possible: local API, VBS/BAT launcher execution, and browser UI rendering.

Do not rely on absolute paths from another PC. Use workspace-root-relative paths.

## Optional Future Tooling

These are not required for the current baseline check, but may be needed for heavier research work:

- PDF rendering for visual page verification.
- Browser automation for user-facing UI evidence.
- Spreadsheet libraries for `.xlsx` generation and chart-source files.

Add any new required package or executable to this folder before making it part of the standard workflow.

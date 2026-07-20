# System Core Packaging Rules

## Purpose

Use this rule when preparing the AI system core for GitHub, a zip package, a new PC, or a third-party tester.

The system core is not the same thing as the active user workspace.

## Core Package Boundary

A clean system-core package should include:

- `AGENTS.md`,
- `START_HERE.html`,
- `_ai_system/governance/`,
- `_ai_system/environment/`,
- `_ai_system/document_presets/`,
- `_ai_system/style_profiles/`,
- `_ai_system/templates/`,
- `_ai_system/tools/`,
- `_ai_system/engines/owned_hwp_hwpx/` in every distributed channel package,
- `_ai_system/validation_fixtures/` when needed,
- generic system documentation only when it contains no project-specific, client-specific, or historical worklog material.

Private maintainer-only release files should live outside the public package area. In the private source repository, use the dedicated internal maintainer folder for public seed builders, package-boundary validators, release smoke tests, and packaging strategy notes.

A clean system-core package should not include:

- `00_사용자_작업공간/`,
- active project reports,
- user-provided source originals,
- AI-service brain artifacts outside the workspace,
- scratch inspection scripts,
- private maintainer files in public release packages,
- decoded report dumps,
- temporary logs,
- `.bak`, `.tmp`, `.log`, `__pycache__`, or local runtime outputs.

## GitHub Repository Standard

If the system core is pushed to GitHub:

- repository should be private unless intentionally open-sourced,
- collaborators should default to read-only,
- `main` should be protected by branch protection or rulesets,
- owner changes should go through reviewed commits or PRs when possible,
- `.gitignore` must correctly exclude `00_사용자_작업공간/` using the real UTF-8 path,
- user-visible system changes should update `CHANGELOG.md`, the recent-improvements block in `README.md`, and `VERSION.json` when a release version should change,
- packaging validation should run before push.

Maintainer release builders and package-boundary validators are not ordinary user/OJT tools and should not be exposed as report-production helpers.

Do not claim a GitHub repo is clean because `.gitignore` exists. Confirm the tracked file list.

## Release Note Rule

Every push that changes system behavior, install/setup flow, report-production flow, validation rules, OJT guidance, or public user docs must leave a release trail:

- `CHANGELOG.md` records what changed, why it matters, and any compatibility note.
- `README.md` shows the current version and the latest three user-visible improvements.
- `VERSION.json` is updated when the change should be treated as a new user-visible release.

Tiny typo fixes or internal-only comments may keep the same version, but the commit message should still make the scope clear.

## Scratch File Policy

Scratch files should not live in `_ai_system/tools/`.

Allowed tool files are durable scripts with stable names and user-facing/system-facing purpose. Temporary files such as `inspect_*.py`, `decoded_report.txt`, `ch*_inspect.txt`, and one-off repair scripts should be moved to a named archive or removed before packaging.

If a one-off script becomes useful, rename it and document it as a real tool.

## Packaging Validation

Before saying a package is ready for a third party or GitHub:

- run workspace validation in the source workspace,
- run system-core packaging validation,
- confirm no user workspace files are tracked or packaged,
- confirm no scratch files are in active tool folders,
- confirm `.gitignore` is readable and contains the correct Korean workspace path,
- confirm README or START_HERE explains how a new user should begin.

If a public release seed is built, verify that private maintainer folders are absent from the generated package and that public README/INSTALL do not link to private maintainer memos.

All channel package validation must require the embedded engine metadata, import provenance, package entrypoint, conversion entrypoints, and Report Factory native HWPX exporter. The source `ppt-test` checkout is never a runtime or package dependency.

## Private/Public Install Source Guard

Private install tests must validate that `VERSION.json` has `channel: main`, Git `origin` points to `Kdreammaker/kkumjangi-report-orchestra`, and `README.md` / `INSTALL.md` do not point to the public repository. Use:

```powershell
python _ai_system/tools/validate_workspace_setup.py --include-user-flow --expect-channel main
```

When preparing a public seed or pushing to the public repository, do not copy this private-only expectation blindly. Public packages should have `channel: public`, public README/INSTALL clone instructions, and should run workspace validation without `--expect-channel main` or with the public-appropriate expectation. Re-check generated public README/INSTALL after `build_system_core_package.py --public-release-version ...` so the public seed is intentionally public and not a stale private package.

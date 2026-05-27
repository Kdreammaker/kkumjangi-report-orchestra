# AI Snapshot and Change Detection Rules

## Purpose

These rules detect direct human edits without Git and without relying on humans to update logs.

This is a workspace-wide background safety rule, not a report PRD. A report PRD defines a report. This rule protects files before and after AI work.

## Core Principle

AI keeps only the latest AI-completed copy of files it actually modified.

At the next work session, compare the current original file against that latest AI snapshot:

- same hash: no content change since the last AI completion,
- different hash: the original file changed after the last AI completion and must be reviewed before editing.

Do not snapshot every file on every task. Snapshot only files the AI actually created or modified during that task.

## Snapshot Location

Each project may keep snapshots under:

`00_사용자_작업공간/<project>/project_state/latest_ai_snapshot/`

Recommended companion manifest:

`00_사용자_작업공간/<project>/project_state/latest_ai_snapshot_manifest.csv`

For workspace-level files such as `AGENTS.md`, `_ai_system/DESIGN_DOCUMENT.md`, or `_ai_system/governance/*.md`, keep the snapshot under:

`_ai_system/project_state/latest_ai_snapshot/`

Recommended workspace-level manifest:

`_ai_system/project_state/latest_ai_snapshot_manifest.csv`

## Manifest Fields

The manifest should track only AI-touched files.

Required fields:

- `path`: original file path,
- `snapshot_path`: latest AI-completed copy path,
- `sha256`: hash of the original at AI completion,
- `snapshot_sha256`: hash of the copied snapshot,
- `updated_at_kst`: AI completion time,
- `worklog`: related worklog path or id,
- `change_reason`: short reason for the AI edit.

Optional fields:

- `project`,
- `artifact_type`,
- `report_id`,
- `prd_version`,
- `notes`.

At AI completion, `sha256` and `snapshot_sha256` must match. If they do not match, the snapshot is not valid.

## Before Editing

Before editing a file that has a latest AI snapshot:

1. Calculate the current original file hash.
2. Compare it with the snapshot hash in the manifest.
3. If the hash matches, proceed normally.
4. If the hash differs, compare the current original with the snapshot before editing.
5. Treat differences as possible human edits.
6. Preserve the changed content unless the user explicitly asks to remove it.

If no snapshot exists:

- read the current file before editing,
- proceed carefully,
- create a snapshot after the AI modifies the file.

## After Editing

After the AI finishes a task:

1. Identify only files the AI actually created or modified.
2. Copy those files to the latest AI snapshot folder.
3. Update the manifest rows for those files.
4. Confirm original hash equals snapshot hash.
5. Record the snapshot update in the active worklog when the task is material.

Do not snapshot:

- untouched files,
- downloaded source originals unless the AI modified them,
- archived files unless the AI changed them,
- transient browser screenshots unless they are part of the delivered evidence.
- snapshot manifest files themselves by default. They are operational ledgers; snapshotting them creates recursive updates. Record manifest creation or updates in the active worklog instead.

## When Hashes Differ

If the current original and snapshot hash differ:

- for text files (`.md`, `.html`, `.csv`, `.svg`, `.txt`, `.json`, `.css`), run or prepare a text diff,
- for `.xlsx`, `.docx`, `.pdf`, or images, use an appropriate extraction, render, metadata, or visual comparison if the difference matters,
- summarize the difference before overwriting,
- log the detected external change if it affects the task.

Use labels:

- `unchanged`: current original equals latest AI snapshot,
- `changed_after_ai`: current original differs from latest AI snapshot,
- `new_file`: file has no snapshot and was not previously tracked,
- `snapshot_missing`: manifest exists but snapshot file is missing,
- `snapshot_invalid`: original and snapshot did not match at AI completion,
- `needs_review`: difference must be reviewed before editing.

## Relationship to Logs

This rule does not replace worklogs, PRD revision logs, source indexes, or claim registers.

- Snapshot/manifest detects whether a file changed.
- Diff review explains what changed.
- Worklog records what AI did and what external changes were detected.
- PRD revision log records report-design changes.
- Question log records user decisions.

## Minimum Operating Rule

For every material AI edit:

- before editing: compare current file to latest AI snapshot when one exists,
- after editing: update latest AI snapshot only for files the AI changed.

This minimum rule is mandatory for report, PRD, governance, source-index, claim-register, data, chart, and final-output files.

When local script execution is available, prefer:

`python _ai_system/tools/update_ai_snapshots.py <workspace-relative-file> [more files...]`

Only pass explicit files the AI actually created or modified. Do not use broad folder globs for snapshot updates.

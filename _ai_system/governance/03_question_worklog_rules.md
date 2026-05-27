# Question and Worklog Rules

## Question and Answer Log Standard

- Each project must maintain `questions/question_log.md`.
- When a report decision requires user confirmation or scope alignment, ask the question and record the reason, answer, and impact in the relevant `questions/question_log.md`.
- Use the question log for user decisions or clarifications that affect:
  - report scope,
  - target audience,
  - methodology,
  - output format,
  - assumptions,
  - legal or regulatory framing,
  - design choices,
  - source-selection boundaries,
  - interpretation of ambiguous user instructions.
- Each logged question must record:
  - `question_id`,
  - project,
  - asked time in KST,
  - exact question,
  - why it was asked,
  - answer time in KST,
  - answer summary,
  - answer verbatim where useful,
  - decision impact,
  - affected files,
  - status.
- Do not overwrite earlier answers. If the user's answer changes, add a new row and mark the old row `superseded`.
- Before finalizing a report, review the question log and reconcile the report scope, assumptions, and recommendations with recorded answers.
- If a user answer conflicts with later evidence, preserve both and mark the issue as an unresolved or updated interpretation rather than silently replacing it.

## Worklog Rules

Create one worklog per project and per major working session. Use a timestamped filename:

`worklogs/YYMMDDHHMM_worklog.md`

Example:

`00_사용자_작업공간/<project>/worklogs/2605192302_worklog.md`

The standard project worklog folder is:

`00_사용자_작업공간/<project>/worklogs/`

Keep `project_state/` for machine-readable state such as `report_stage_manifest.json`, snapshot manifests, and other operational records. Do not place new human-readable session worklogs under `project_state/`. Historical worklogs already stored there may remain for audit continuity, but new worklogs should use `worklogs/`.

Each worklog must include:

```markdown
# YYMMDDHHMM Worklog - Project Name

## Scope
- What this session is trying to accomplish.

## Inputs
- Local files, user instructions, URLs, official sources, or datasets used.

## Actions
- Timestamped bullets in KST.
- Include searches performed, files created, sources captured, and decisions made.

## Evidence Added
- Source ids, local evidence paths, screenshots, downloaded files, or crawl outputs.

## Findings
- Confirmed facts only.

## Interpretations / Estimates
- Clearly marked analysis, hypotheses, and calculations.

## Open Questions
- Items requiring more research, legal review, partner confirmation, or regulator confirmation.

## Next Steps
- Concrete next actions.
```

Rules:

- Update the active project worklog whenever research scope changes, evidence is added, or a conclusion is formed.
- Update the active project worklog whenever a report, PRD, governance file, chart, table, source index, claim register, assumption register, or data file is materially created or changed.
- Do not overwrite old conclusions silently. Add a correction note with date/time and reason.
- If a source is rejected as unreliable or stale, log that decision.
- If a claim comes from an image/PDF extraction, note whether it was visually verified.
- If a foreign-language source is used, log whether original text, translation, or interpretation was added.
- If a report conclusion changes because of new evidence, log the old conclusion, new conclusion, source ids, and reason for change.
- Worklogs, task lists, implementation plans, and walkthroughs count only when they are saved inside this workspace. AI-service artifact folders outside the workspace may be useful scratch space, but they are not durable project records unless mirrored into the project or `_ai_system/`.
- If an AI cannot save a planning or walkthrough artifact into this workspace, it must state that limitation and avoid reporting it as a project deliverable.

## Document and PRD Change Logging Matrix

Use this matrix to decide where to record a change.

| Change type | Worklog | PRD revision log | Question log | Other artifact |
|---|---|---|---|---|
| Minor typo or wording polish | optional | no | no | no |
| Report section added, removed, or materially reordered | yes | yes if scope/structure changes | if user decided | detailed TOC |
| Report conclusion changed | yes | yes if decision context/scope changes | if user decided | claim register |
| Citation style, chart standard, appendix policy changed | yes | yes for affected report | if user decided | governance or design docs |
| Table/chart/image added or materially revised | yes | yes if planned output changes | if user decided | data file, figure/table folder |
| Data file changed | yes | only if report plan changes | no | data index/source index |
| Source added, rejected, or reclassified | yes | only if evidence standard changes | no | source record/source index |
| Claim register changed | yes | only if claim-handling policy changes | no | claim register |
| Report PRD field changed | yes | yes | if user decided | report PRD |
| Report output format changed | yes | yes | if user decided | report PRD |
| Governance rule changed | yes | no unless it changes an active report PRD | if user decided | governance file |
| User clarifies scope, audience, assumption, or design preference | yes | yes if it changes report PRD | yes | report PRD or design doc |

Rules:

- Worklog entries describe what was actually done during the session.
- PRD revision logs describe how the report design changed.
- Question logs preserve user decisions and their impact.
- If one change belongs in multiple places, write one concise entry in each rather than trying to make a single artifact do all jobs.
- When changing a PRD because of user feedback, record:
  - the user decision in `questions/question_log.md`,
  - the PRD field and revision log row in the report PRD,
  - the files changed and follow-up actions in the active worklog.

## Pre-Edit Change Check

Before substantial edits, check whether the target files appear to have changed since the latest AI-completed snapshot or the last relevant worklog/PRD revision entry.

Minimum check:

- inspect the target file's current contents before editing,
- if the file has a latest AI snapshot, compare the current file hash with the snapshot hash before editing,
- compare against active worklog or PRD revision notes when the change affects scope, evidence, or report structure,
- preserve any human edits and work with them instead of overwriting them.

If unexpected changes are found:

- do not revert them silently,
- log the discovery in the active worklog if it affects the task,
- ask the user only when the change creates a real ambiguity or conflict.

For the mandatory no-Git snapshot workflow, follow `_ai_system/governance/07_ai_snapshot_change_detection_rules.md`.

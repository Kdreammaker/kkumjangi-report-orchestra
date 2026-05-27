# Runtime Notes

## Browser Tool Artifacts

Some AI/browser tools may create a root folder such as `.playwright-mcp`. This folder is an implementation detail, not a user-facing workspace.

Rule:

1. Let the tool use the folder if it requires that path during execution.
2. After the browser task finishes, move the folder into `_ai_system/runtime/playwright-mcp/`.
3. Record the move in the active worklog if it occurred during a material task.

## Package Drift

If a task needs a new package:

1. Record why the package is needed.
2. Add it to `_ai_system/environment/requirements.txt`.
3. Update `_ai_system/environment/README.md` if the package changes user setup.
4. Verify the command or script that depends on it.


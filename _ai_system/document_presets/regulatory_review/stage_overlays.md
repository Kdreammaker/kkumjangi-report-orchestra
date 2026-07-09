# Regulatory Review Stage Overlays

## Workflow Mode And Stage Depth

- Default mode: `substantial` for high-risk regulatory opinions, or `standard` when the user only needs a short review memo.
- Use PRD, jurisdiction/source confirmation, issue framing, opinion drafting, risk/action review, style pass, and delivery readiness.
- Do not turn legal/regulatory review into generic persuasive prose. Separate source-backed facts, interpretation, business implication, options, and unresolved uncertainty.

## TOC

- Separate legal/regulatory facts, interpretation, business implication, and action options.
- Include approval path, blocker, dependency, and review-needed sections where relevant.
- Lead with the review opinion or current conclusion before detailed background when the document supports a decision.

## Authoring Structure

- Default paragraph mode: bullet-first for findings/options/actions, prose for legal/regulatory context and interpretation rationale.
- Use `administrative_outline` when the artifact needs administrative review hierarchy or Hancom/HWPX-oriented markers; otherwise use `formal_outline`.
- Keep issue, conclusion, basis, implication, action owner, deadline, and residual uncertainty distinct.
- For HWPX-compatible HTML, record Hancom font fallback and any Korean marker overrides such as `가.` or `가)` in `reports/report_design.md` and verify by opening in Hancom before delivery claims.

## Workpack

- Require exact official source links, access dates, and location markers for direct quotes.
- Mark counsel-review and unresolved-interpretation items clearly.

## Visual/Data

- Prefer approval-path flow diagrams, obligation matrices, risk heatmaps, and timeline views.
- Do not visualize approval probability unless assumptions and limits are explicit.

## Layout/Export

- Keep tables narrow and semantic; split oversized obligation matrices by issue, actor, or deadline.
- Use static diagrams/images and inline table/callout styles for DOCX/HWPX-compatible targets.
- DOCX/PDF/HWPX-compatible conversion requires separate export validation; this preset does not guarantee legal correctness or conversion success.

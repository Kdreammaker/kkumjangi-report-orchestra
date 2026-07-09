# Business Proposal Stage Overlays

## Workflow Mode And Stage Depth

- Default mode: `standard`, with specialized proposal and commercial-boundary checks.
- Use PRD, recipient/context confirmation, proposal outline, section drafting, assumption/exclusion review, style pass, versioning, and delivery readiness.
- Replace report chapter workpacks with proposal sections such as recipient need, value, scope, deliverables, roles, schedule, conditions, risks, and next decision.
- Chapter 0, full evidence appendix, and long report skeleton are optional; use them only for a substantial proposal dossier.
- If the proposal is derived from another artifact, reconfirm which claims, numbers, dates, scope items, pricing hints, and partner references are approved for the proposal recipient.

## TOC

- Lead with recipient need, proposed value, scope, execution plan, responsibilities, terms, risks, and next decision.
- Keep proposal commitments separate from assumptions, options, and negotiation items.
- Use conclusion-first section leads. Put the proposal ask, expected value, and requested next action before detailed background.

## Authoring Structure

- Default paragraph mode: mixed, with bullet-first scope/role/schedule/terms sections.
- Use prose for recipient context, value rationale, and relationship-sensitive transitions.
- Use bullets or narrow tables for deliverables, responsibilities, milestones, assumptions, exclusions, risks, and decision requests.
- For DOCX targets, default to Malgun Gothic and stable numbered hierarchy. For HWPX-compatible HTML, record Hancom font fallback and any marker overrides in `reports/report_design.md`.

## Workpack

- Require recipient-specific relevance, measurable value, deliverable definitions, schedule assumptions, and owner responsibilities.
- Flag legal, pricing, tax, procurement, and contract language that needs specialist approval.

## Visual/Data

- Prefer value maps, scope tables, implementation timelines, responsibility matrices, pricing option summaries, and risk/mitigation tables.
- Use `partner_proposal` cover preset when a partner/customer-facing proposal cover is needed.

## Layout/Export

- Use a partner/customer delivery hierarchy: proposal cover, recipient context, value, scope table, role split table, schedule, terms/exclusions box, and next decision.
- Keep scope, responsibility, schedule, and condition tables narrow enough for Word page width; split large matrices into smaller tables when needed.
- Use static diagrams or charts with captions and alternative descriptions; avoid interactive HTML, viewport-dependent layouts, and complex absolute positioning.
- Make long deliverable names, terms, exceptions, and URLs wrap cleanly.
- DOCX/PDF/HWPX-compatible conversion requires separate export validation; this preset does not guarantee conversion success.

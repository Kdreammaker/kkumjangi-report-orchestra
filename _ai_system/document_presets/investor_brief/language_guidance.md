# Investor Brief Language Guidance

Use this file only when the selected preset is `investor_brief` and the PRD/current task needs language or notation guidance. Do not create `investor_brief_en`.

## Korean Default Guidance

- Korean investor briefs should be concise, evidence-backed, and cautious about projections, growth claims, valuation references, and market sizing.
- Keep confidential metrics, approved KPIs, and externally shareable claims separated.

## English Guidance

- English investor briefs should be conclusion-first and scan-friendly, with section names such as `Executive Summary`, `Investment Context`, `Business Model`, `Market`, `Traction`, `Financial Highlights`, `Risks`, and `Appendix`.
- Forward-looking language should use bounded phrasing such as `expects`, `plans`, `may`, `could`, or `subject to`.
- Avoid hype or certainty when discussing forecasts, growth, margins, pipeline, fundraising, valuation, or exit scenarios.
- State `data as of`, currency, unit, source date, and access date near financial or market claims. If those fields are unknown, mark the gap instead of smoothing it over.
- Keep jurisdiction and distribution-market uncertainty visible. If the target investor geography, securities-law context, or sharing channel is unclear, do not draft as if the brief is approved for external distribution.
- Use `Source:`, `Underlying data:`, and `Accessed YYYY-MM-DD` only when English or mixed output is explicitly marked.

## Ask Before Drafting

Ask before drafting when:

- the brief may be sent to external investors, lenders, analysts, or strategic partners,
- the jurisdiction, fundraising market, or securities-law boundary is unclear,
- the distribution market or recipient status is unclear,
- metrics are not approved for external use,
- the user asks for an English version of a Korean internal draft and protected metrics/claims may change.

## Forbidden Or Caution Expressions

- Do not write full `not an offer`, `forward-looking statements`, securities legends, or jurisdiction-specific disclaimer text automatically. You may mark the need for owner/counsel review.
- Do not imply an investment recommendation, investment advice, guaranteed return, approved valuation, committed financing, or suitability for a specific investor.
- Do not add `buy`, `sell`, `hold`, analyst ratings, target prices, fair-value calls, or investment-advice language unless the user explicitly authorizes that report type and review boundary.
- Do not present forward-looking statements as settled facts; keep forecast assumptions, approval status, and review ownership visible.
- Do not use `best`, `dominant`, `guaranteed`, `de-risked`, or `certain` unless exact approved evidence supports the wording.

## Genre Boundary

This preset supports an investor brief or factbook. It is not an offering memorandum, securities prospectus, legal opinion, valuation opinion, or investment recommendation unless separately authorized.

## Tone Workflow Boundary

- This preset owns investor-brief structure, evidence expectations, visuals, source labels, and approval/disclosure cautions.
- Korean tone/style review should use `_ai_system/style_profiles/korean_tone_workflow_design_v1.md` plus the selected style profile.
- Do not create a separate investor-only rewrite engine or use tone adjustment to turn evidence-backed diligence material into fundraising persuasion.

## Caption, Source, Accessed, Disclaimer

- Korean output: `자료:`, `근거 데이터:`, `접근일: YYYY.MM.DD`.
- English output: `Source:`, `Underlying data:` or `Data basis:`, `Accessed YYYY-MM-DD`.
- English financial tables should show `Data as of`, currency, unit, source date, and access date in the caption, table note, or adjacent metadata.
- `disclaimer_profile` is guidance only and must be reviewed by the appropriate owner before external sharing. It must not invent jurisdiction-specific legal or securities disclaimer text.

## Protected Spans

Preserve direct quotes, numbers, dates, percentages, financial metrics, valuation terms, approved KPIs, proper nouns, source-backed market claims, and approved public/confidential wording.

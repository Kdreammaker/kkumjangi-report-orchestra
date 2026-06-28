# Equity Research Language Guidance

Use this file only when the selected preset is `equity_research` and the PRD/current task needs language or notation guidance. Do not create `equity_research_en`.

## Korean Default Guidance

- Korean analysis should distinguish confirmed data, analyst interpretation, estimates, unresolved issues, and data as-of dates.
- Do not add buy/sell/hold ratings, target prices, or investment-advice language unless the user has authorized that report type and review boundary.

## English Guidance

- English equity or sector analysis should state `as of` dates, data vintage, coverage universe, currency, units, and estimate boundaries.
- Use cautious headers such as `Sector Context`, `Company Snapshot`, `Financial Trend`, `Valuation Context`, `Key Risks`, and `Data Appendix`.
- Keep jurisdiction and distribution-market uncertainty visible. If the report audience, geography, securities-regulation context, or permitted sharing channel is unclear, do not imply that the note is approved research distribution.
- Forward-looking statement boundaries must distinguish actuals, estimates, scenarios, and analyst interpretation. Use `may`, `could`, `subject to`, `estimate`, or `scenario` when the evidence is not settled.
- Use `Source:`, `Data basis:`, and `Accessed YYYY-MM-DD` only when English or mixed output is explicitly marked.

## Ask Before Drafting

Ask before drafting when:

- jurisdiction, distribution market, audience status, or securities-regulation context is unclear,
- the user asks for ratings, target price, investment advice, suitability language, or trading recommendation,
- the report may be shared externally with investors, partners, or the public,
- source data dates, currency, adjustment basis, or issuer coverage are unclear.

## Forbidden Or Caution Expressions

- Do not write `buy`, `sell`, `hold`, `outperform`, `underperform`, `target price`, `fair value`, or `investment advice` unless explicitly authorized.
- Do not add a target price, valuation rating, coverage rating, or buy/sell/hold call unless it is explicitly approved and the required review boundary is documented.
- Do not generate `not an offer`, investment-advice, research-distribution, or jurisdiction-specific securities disclaimer text automatically. You may flag that review is required.
- Do not imply guaranteed returns, regulatory approval, complete coverage, or suitability for a reader.
- Do not present forward-looking statements, management guidance, consensus estimates, or scenario outputs as source facts.

## Genre Boundary

This preset supports sector/company analysis and research-style reports. It is not licensed investment advice, an analyst rating note, a securities offering document, or a personalized recommendation by default.

## Tone Workflow Boundary

- This preset owns sector/company analysis structure, evidence expectations, financial/valuation data treatment, visuals, and review cautions.
- Korean tone/style review should use `_ai_system/style_profiles/korean_tone_workflow_design_v1.md` plus the selected style profile.
- Do not create a separate equity-research rewrite engine or use tone adjustment to add buy/sell/hold, target-price, suitability, or guaranteed-return language.

## Caption, Source, Accessed, Disclaimer

- Korean output: `자료:`, `근거 데이터:`, `접근일: YYYY.MM.DD`.
- English output: `Source:`, `Underlying data:` or `Data basis:`, `Accessed YYYY-MM-DD`.
- English tables/charts should show `Data as of`, currency, unit, source date, and access date where relevant.
- `disclaimer_profile` can name the needed review boundary but must not invent legal, securities, or jurisdiction-specific disclaimer text.

## Protected Spans

Preserve issuer names, ticker symbols, dates, prices, currency, units, financial metrics, formulas, direct quotes, source titles, access dates, and data-as-of labels.

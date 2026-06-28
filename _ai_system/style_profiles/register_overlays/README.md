# Korean Register Overlay Guide

Register overlays are guidance-only style modifiers that sit on top of an existing style profile. They do not create a new reader profile, do not perform automatic rewrite, and do not change report workflow gates.

Use a style profile to decide reader fit, disclosure sensitivity, confidence level, and protected-span handling. Use a register overlay to decide Korean expression mode for the delivery scene: written report, oral briefing, public written copy, educational explanation, or adult user instructions.

## Overlay List

| Overlay ID | Korean label | Use when | Do not use when |
|---|---|---|---|
| `written_report` | 문어체 보고문 | The output is a report, memo, review, proposal, analysis, or formal written deliverable. | The final output is a meeting script, live briefing, FAQ, or step-by-step user guide. |
| `oral_briefing` | 구어체 브리핑 | The output will be spoken in a meeting, briefing, interview, presentation note, or executive verbal update. | A casual tone would weaken authority, approvals, citations, or public/disclosure wording. |
| `public_written` | 외부 공개문 | The output is public-facing, press-facing, website-facing, partner-distributable, or externally quotable. | Internal assumptions, unapproved claims, or confidential details remain unresolved. |
| `educational_explanation` | 교육 설명체 | The output explains concepts, processes, risks, evidence, or decisions to a learner or non-specialist audience. | Simplification would distort source-backed claims, legal meaning, metrics, or responsibility boundaries. |
| `user_instructional` | 사용자 안내/매뉴얼체 | The output is an adult-facing product manual, guide, FAQ, onboarding note, support article, or procedural instruction. | The goal is child education, marketing persuasion, legal notice drafting, or source-heavy research argument. |

## Combination Rule

Select only one primary style profile and at most one primary register overlay for a specific artifact. If a document contains different sections, assign overlays by section, not by rewriting the whole document into a blended tone.

Examples:

- `child_education` + `educational_explanation`: child or beginner learning material that still preserves facts, numbers, names, and source-backed claims.
- `press_public` + `public_written`: public announcement, press release, quote-sensitive external statement, or website copy with approved wording.
- `internal_executive_summary` + `oral_briefing`: executive spoken briefing notes, meeting opening remarks, or verbal update script.
- `partner_business` + `written_report`: partner-facing proposal, collaboration report, or customer-facing written analysis.
- `partner_business` + `user_instructional`: adult product guide, implementation manual, FAQ, onboarding procedure, or support explanation for business users.

## Protected Span Boundary

Register overlays cannot change protected spans. Hold, quote, or request review instead of smoothing these items:

- numbers, units, dates, percentages, prices, metrics, and formulas;
- direct quotes, quoted translations, press-release quotes, and approved quote blocks;
- law names, article numbers, regulation names, official program names, and official guidance wording;
- proper nouns, company names, product names, service names, institution names, people names, and job titles;
- approved public statements, approval wording, boilerplate, disclaimers, contact details, embargo text, and official notices;
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, safety warning, confidentiality, or release wording.

If a register choice conflicts with protected content, keep the protected wording and adjust only unprotected connective or framing text.

## Design Status

- `automation_status`: `guidance_only`
- `query_style_profile.py`: not connected
- PRD/current task/workflow fields: documented as guidance-only selection and style-pass trace fields; no automatic rewrite or workflow automation is connected
- validators/smoke tests: not connected

Future tooling integration may add structured validation for fields such as `speech_context`, `recipient_relationship`, `section_overlay_map`, and `human_review_required_when_ambiguous`.

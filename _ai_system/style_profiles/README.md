# Style Profile System

Style profiles help AI choose tone and manner for a document's reader, purpose, and disclosure context. They are not an "AI disguise" layer and they are not an automatic rewrite engine.

Use a style profile after the document preset, PRD, evidence status, and audience are known. A profile may guide PRD questions and drafting review early, but the actual expression-correction style pass normally runs after body chapters, visual captions, and Chapter 0 are stable, and before assembly. It must not weaken evidence, citation, approval, confidentiality, or export rules.

## Core Contract

1. Detect tone/style risks first.
2. Mark protected spans before rewriting.
3. Rewrite only the minimum span needed for reader fit.
4. Run fidelity review before accepting the change; naturalness cannot override fidelity.
5. Run naturalness review as a reader-fit check, not as permission to broaden the rewrite.
6. Roll back or request human review when meaning, evidence strength, approval wording, or genre fit is at risk.

The system borrows the safety idea of span-based, meaning-preserving style revision from Korean AI-tell rewriting projects such as `epoko77-ai/im-not-ai`, but it does not copy their taxonomy, scoring, agents, or automation. This workspace uses style profiles as guidance modules for report production.

## Korean Tone Workflow

`_ai_system/style_profiles/korean_tone_workflow_design_v1.md` is the common Korean tone and style-pass procedure. It is guidance-only and should be used when a Korean report, chapter, brief, public statement, investor brief, sector analysis, or company analysis needs tone adjustment after the document preset, style profile, reader, classification, and output language are known.

The workflow uses these risk types:

- `style-only`: localized wording, rhythm, connector, or stock-phrase issue.
- `evidence-related`: the proposed wording may change claim type, evidence strength, uncertainty, source relationship, or citation meaning.
- `approval-sensitive`: the span may involve public, legal, contractual, confidentiality, disclosure, disclaimer, quote, or owner-approved wording.
- `genre-drift`: the document may drift from its selected preset, such as a report becoming an essay, a press release becoming sales copy, or investor analysis becoming investment advice.
- `reader-fit`: the tone, order, emphasis, or explanation level does not fit the selected reader.

Required style-pass artifacts should be stored under the active project, normally `reports/style_pass/` or the relevant chapter work area. A no-change or held-change result is valid when protected spans, fidelity risk, or already-acceptable reader fit make rewriting unnecessary:

- `style_risk_findings.json`: detected risks, severity, risk type, protected-span status, and suggested action.
- `protected_spans.json`: protected span map before any limited rewrite.
- `style_rewrite_diff.md`: only changed spans, before/after wording, and rationale.
- `style_fidelity_review.md`: pass/partial/blocked/rollback/human-review result.
- `style_naturalness_review.md`: reader-fit naturalness, residual style risk, and over-polish review after fidelity.

Reusable templates live in `_ai_system/style_profiles/templates/`. Do not store raw prompts, hidden instructions, or unrelated source text in shared style-pass artifacts.

## Protected Spans

Never change these spans during style-profile revision unless the user explicitly approves a source-checked correction:

- direct quotes and quoted translations,
- numbers, units, dates, percentages, prices, financial metrics, and formulas,
- law names, article numbers, regulation names, official program names, and court/regulator wording,
- proper nouns, company names, product names, partner names, people names, and jurisdiction names,
- source-backed claims in claim registers or reader-facing citations,
- approved public statements, quotes, boilerplate, disclaimers, contact information, embargo text, and approval wording,
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording.

If a sentence mixes protected content with style risk, split the sentence or revise only unprotected connective wording. Do not paraphrase protected content to make the prose sound smoother.

## When To Use

- PRD: choose a profile after confirming reader, purpose, classification, confidentiality, and distribution scope.
- Drafting review: check whether prose matches the reader and document genre.
- Korean style pass: after body chapters, visual captions, and Chapter 0 are stable, produce style-risk findings, protected spans, limited/no-change rewrite diff, fidelity review, and naturalness review before assembly.
- Limited rewrite: adjust only finding-linked wording that is not protected and not source-critical.
- Closeout review: confirm the selected profile did not introduce unsupported claims, hidden uncertainty, or genre drift.

## When Not To Use

- Do not use a style profile to bypass research-quality gates.
- Do not use it to make weak evidence sound confident.
- Do not use it to turn internal drafts into public copy.
- Do not use it to rewrite quotations, legal language, numbers, or approved statements.
- Do not add validators, score gates, workflow automation, or background rewrite behavior unless a separate implementation task explicitly asks for it.

## Preset/Profile Boundary

Document presets decide document genre, structure, expected sections, visual/data emphasis, and review checklist. Style profiles decide reader-fit tone, certainty, sentence shape, protected-span handling, and limited style-pass procedure.

Investor brief, sector analysis, and company analysis belong primarily in document presets such as `investor_brief` and `equity_research` for structure and evidence expectations. Their Korean tone pass should use this common workflow plus the selected style profile, without adding a duplicate investor-only rewrite engine or an investment-advice style profile.

## Register Overlays

Register overlays are a separate guidance-only axis layered over an existing style profile. They decide Korean delivery mode, such as written report, oral briefing, public written copy, educational explanation, or adult user instructions. They do not create new style profiles, run automatic rewriting, or connect to `query_style_profile.py`, PRD/current-task workflow fields, validators, or smoke tests unless a later implementation task explicitly adds that behavior.

Use `_ai_system/style_profiles/register_overlays/README.md` first when a Korean artifact needs a register choice. Use `korean_register_overlay.md` for overlay definitions, `honorific_policy.md` for 압존법/경어법 decisions, and `user_instructional_overlay.md` for adult-facing manuals, guides, and FAQs.

## Profile Modules

Each profile folder contains:

- `profile.json`: routing metadata and recommended document presets.
- `tone_rules.md`: reader-fit writing guidance.
- `forbidden_patterns.md`: AI-tell, overclaim, and genre-drift patterns to avoid.
- `rewrite_protocol.md`: protected-span and limited-rewrite procedure.
- `examples.md`: bad/good examples and why the change is acceptable.

Read `_ai_system/style_profiles/INDEX.json` first. It keeps executable aliases separate from descriptive `routing_cues` so future query logic can route high-confidence natural-language requests without forcing ambiguous cases. Use `_ai_system/style_profiles/CODEMAP.md` when the compact index is not enough to choose a profile, and `_ai_system/style_profiles/ROUTE_EXAMPLES.md` when phrases such as "일반 사용자 절차 안내", "공식 외부용", or "엄밀한 문서" may overlap document presets or multiple profiles. Then read only the selected profile files.

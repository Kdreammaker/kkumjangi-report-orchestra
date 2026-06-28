# Rewrite Protocol

## 1. Detect

- Identify hype, vague scope, hidden assumptions, passive responsibility, and terms that sound binding.
- Flag commercial, legal, pricing, tax, procurement, and delivery wording as high-risk.
- Mark each issue as `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, or `reader-fit`.
- Record findings in `style_risk_findings.json` when a style pass is a distinct work unit.

## 2. Protect

Protect:

- direct quotes and quoted translations,
- numbers, units, dates, percentages, prices, financial metrics, formulas, commercial terms, figures, deliverables, scope, and exclusions,
- law names, article numbers, regulation names, official program names, and court/regulator wording,
- proper nouns, company names, product names, partner names, customer names, people names, and jurisdiction names,
- source-backed capability claims in claim registers or reader-facing citations,
- approved public statements, approved wording, quotes, boilerplate, disclaimers, contact information, embargo text, and approval wording,
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording.

## 3. Limited Rewrite

- Replace hype with concrete value and condition language.
- Separate `proposal`, `assumption`, `approval needed`, and `confirmed commitment`.
- Make unresolved items visible without sounding defensive.
- Keep the reader-facing tone respectful and practical.
- Rewrite only finding-linked, unprotected spans.

## 4. Fidelity Review

Check:

- no draft term became binding,
- no approved wording changed,
- no value claim gained certainty,
- scope, role, schedule, and exclusions remain visible.

## 5. Decision

- Accept only if fidelity review passes and reader-fit improves.
- Roll back the affected span if meaning, evidence strength, approval wording, or genre boundary changed.
- Request human review for legal, pricing, tax, procurement, contract, confidentiality, public, disclaimer, or approved partner wording.

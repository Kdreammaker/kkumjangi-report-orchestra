# Rewrite Protocol

## 1. Detect

- Find abstract terms, long sentences, unexplained jargon, fear-heavy wording, and examples that may distort facts.
- Mark each issue as `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, or `reader-fit`.
- Record findings in `style_risk_findings.json` when a style pass is a distinct work unit.

## 2. Protect

Protect:

- direct quotes, quoted translations, and exact definitions from sources,
- numbers, units, dates, percentages, prices, financial metrics, formulas, names, and labels,
- law names, article numbers, regulation names, official program names, court/regulator wording, safety warnings, and official instructions,
- proper nouns, company names, product names, partner names, people names, and jurisdiction names,
- source-backed claims in claim registers or reader-facing citations,
- approved public statements, quotes, boilerplate, disclaimers, contact information, embargo text, and approval wording,
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording.

## 3. Limited Rewrite

- Split one long explanation into smaller steps.
- Add a simple example only when it does not change the claim.
- Define necessary terms in plain Korean.
- Keep warnings calm and concrete.
- Rewrite only finding-linked, unprotected spans.

## 4. Fidelity Review

Check:

- no fact became false through simplification,
- examples do not replace evidence,
- the learner can follow the sequence,
- protected spans are unchanged.

## 5. Decision

- Accept only if fidelity review passes and learner reader-fit improves.
- Roll back the affected span if meaning, evidence strength, safety warning, approval wording, or genre boundary changed.
- Request human review for safety, legal, official instruction, public, disclaimer, or owner-approved wording.

# Rewrite Protocol

## 1. Detect

- Find mixed claim types, unsupported causal wording, vague method language, and excessive rhetorical formality.
- Mark each issue as `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, or `reader-fit`.
- Record findings in `style_risk_findings.json` when a style pass is a distinct work unit.

## 2. Protect

Protect:

- direct quotes and translated source passages,
- numbers, units, dates, percentages, prices, financial metrics, formulas, and numerical/statistical values,
- citation data, page/section locators, law names, article numbers, regulation names, official program names, and court/regulator wording,
- proper nouns, company names, product names, partner names, people names, and jurisdiction names,
- method terms,
- source-backed paraphrases, source-backed claims, claim register wording, and reader-facing citations,
- approved public statements, quotes, boilerplate, disclaimers, contact information, embargo text, and approval wording,
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording.

## 3. Limited Rewrite

- Clarify whether a sentence is definition, literature summary, finding, interpretation, or limitation.
- Replace unsupported certainty with method-appropriate wording.
- Split source paraphrase from author inference.
- Preserve citation style and source meaning.
- Rewrite only finding-linked, unprotected spans.

## 4. Fidelity Review

Check:

- no source paraphrase gained new analysis,
- no inference reads as a source fact,
- limitations remain visible,
- citations and protected spans are unchanged.

## 5. Decision

- Accept only if fidelity review passes and expert reader-fit improves.
- Roll back the affected span if meaning, method, evidence strength, citation meaning, approval wording, or genre boundary changed.
- Request human review for method interpretation, legal/public/disclosure wording, citation uncertainty, or owner-approved wording.

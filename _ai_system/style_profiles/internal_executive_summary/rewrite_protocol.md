# Rewrite Protocol

Use this profile only as a limited style pass after evidence and claim status are known.

## 1. Detect

- Find long sentences, vague subjects, repeated mechanical transitions, hidden owners, and unsupported confidence.
- Mark each issue as `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, or `reader-fit`.
- Record findings in `style_risk_findings.json` when a style pass is a distinct work unit.

## 2. Protect

Before rewriting, mark protected spans:

- direct quotes,
- numbers, units, dates, prices, percentages, formulas,
- law/regulation names and article numbers,
- proper nouns,
- source-backed claims,
- approved public statements, approved quotes, boilerplate, disclaimers, contact information, embargo text, approval wording, contract, confidentiality, and public-release wording.

If the sentence cannot be revised without touching a protected span, leave it unchanged and add a review note.

## 3. Limited Rewrite

- Move the conclusion or decision need to the front.
- Split overloaded sentences.
- Replace vague transitions with concrete owner/action/risk wording.
- Keep claim meaning, confidence, and caveats unchanged.
- Do not add a new recommendation, source, or mitigation.
- Rewrite only finding-linked, unprotected spans.

## 4. Fidelity Review

Check:

- protected spans are unchanged,
- source-backed claims still match the source/claim register,
- risk and uncertainty remain visible,
- the summary is shorter or clearer without becoming more confident than the evidence.

## 5. Decision

- Accept only if fidelity review passes and reader-fit improves.
- Roll back the affected span if meaning, evidence strength, approval wording, or genre boundary changed.
- Request human review for legal, securities, public, contract, confidentiality, or owner-approved wording.

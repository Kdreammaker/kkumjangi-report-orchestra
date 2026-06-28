# Rewrite Protocol

## 1. Detect

- Find hype, unapproved facts, internal-risk exposure, unclear attribution, and report-style analysis.
- Mark every public claim by approval status: approved, unclear, blocked, or internal-only.
- Mark each issue as `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, or `reader-fit`.
- Record findings in `style_risk_findings.json` when a style pass is a distinct work unit.

## 2. Protect

Protect:

- direct quotes, quoted translations, approved quotes, and quote attribution,
- numbers, units, dates, percentages, prices, financial metrics, formulas, approved figures, and partner references,
- law names, article numbers, regulation names, official program names, court/regulator wording, and legal/public wording,
- proper nouns, company names, product names, partner names, people names, and jurisdiction names,
- source-backed claims in claim registers or reader-facing citations,
- approved public statements, quotes, boilerplate, disclaimers, contact information, embargo text, and approval wording,
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording.

## 3. Limited Rewrite

- Convert internal analysis into approved public facts only when approval status supports it.
- Shorten the lead without adding claims.
- Remove or hold unapproved internal rationale.
- Keep public-facing wording factual and attributable.
- Rewrite only finding-linked, unprotected spans.

## 4. Fidelity Review

Check:

- every public claim has approval/source status,
- no internal-only risk or negotiation detail leaked,
- no quote, boilerplate, contact, embargo, or legal text changed,
- headline and lead do not overstate.

## 5. Decision

- Accept only if fidelity review passes and public reader-fit improves.
- Roll back the affected span if meaning, evidence strength, approval wording, disclosure boundary, or genre boundary changed.
- Request human review for legal, regulatory, public, embargo, quote, boilerplate, disclaimer, or comms-approved wording.

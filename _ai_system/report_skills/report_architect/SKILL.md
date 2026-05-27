---
name: report_architect
description: Plan a substantial report before drafting prose.
triggers:
  - report PRD
  - detailed TOC
  - major skeleton
---

# Report Architect

## Mission

Turn the user's business question into a report plan that makes later writing easier and more accurate.

## Required Output

- report PRD under `report_prd/`
- detailed TOC under `drafts/`
- source collection plan
- major skeleton with thesis, evidence needs, counterarguments, data needs, visual candidates, and unresolved risks

## TOC Contract

- Define 대목차 as `## 제N장 ...`; each 대목차 becomes one `reports/chapters/chNN*.html` source document.
- Define 중목차 as `### N.M ...`; each 중목차 must later appear as a visible heading in that chapter.
- Define 소목차 as `#### N.M.K ...` when the chapter needs finer proof, risk, or option units.
- Do not use a small outline as a default. Choose the number of 대목차 from the PRD, reader decisions, evidence domains, players, options, execution paths, and risks. If a broad report is intentionally compressed into only a few 대목차, record the compression rationale before asking for TOC approval.
- Do not create an expanded TOC that the later chapter writer can ignore. The TOC is a production contract, not a decorative outline.

## Content Quality Rules

- Optimize for decision usefulness, not raw length.
- Identify what the reader must decide after each chapter.
- Separate confirmed facts, assumptions, estimates, and hypotheses.
- Do not draft final recommendations before evidence and risk chapters are stable.
- Plan charts, diagrams, and tables by reader decision, not by quota.

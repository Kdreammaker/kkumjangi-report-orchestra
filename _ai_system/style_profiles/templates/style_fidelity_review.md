# Style Fidelity Review

- artifact_type: style_fidelity_review
- schema_version: 1
- automation_status: guidance_only
- project:
- report_or_chapter:
- style_profile:
- document_preset:
- output_language:
- reviewed_at_kst:
- status: partial

## Review Result

- status must be one of: pass, partial, blocked, rollback_required, human_review_required
- A natural Korean sentence does not pass if fidelity fails.
- This review is not a score gate and does not prove source truth, legal correctness, approval readiness, or delivery readiness.
- A broad polish pass fails even if the revised prose reads more naturally.

## Fidelity Checks

| check | result | notes |
|---|---|---|
| protected spans unchanged | not_run |  |
| facts, numbers, dates, names, citations, and locators preserved | not_run |  |
| claim type preserved: direct_quote / paraphrase / data_based / inference / recommendation | not_run |  |
| evidence strength, uncertainty, caveats, and assumptions preserved | not_run |  |
| approval, confidentiality, contract, public wording, disclaimer, or disclosure text preserved | not_run |  |
| document preset and style profile genre boundary preserved | not_run |  |
| change scope stayed limited to finding-linked spans | not_run |  |
| changed span count, touched paragraph count, held changes, and rollback decisions recorded | not_run |  |
| no unsupported concretization added owner, metric, example, cause, recommendation, risk, benefit, disclaimer, or commitment | not_run |  |
| no whole-document polish, over-rewrite, or genre-changing style improvement | not_run |  |
| reader-fit issue improved without over-polish or new stock phrases | not_run |  |

## Change Scope Record

- changed_span_count:
- touched_paragraph_count:
- held_change_count:
- rolled_back_span_count:
- scope_status: not_run
- held_changes_summary:

## Decision

- accepted_spans:
- rolled_back_spans:
- second_pass_allowed:
- human_review_needed:
- source_or_approval_follow_up:

## Residual Risk

-

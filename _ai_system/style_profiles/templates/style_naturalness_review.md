# Style Naturalness Review

- artifact_type: style_naturalness_review
- schema_version: 1
- automation_status: guidance_only
- project:
- report_or_chapter:
- style_profile:
- document_preset:
- output_language:
- reviewed_at_kst:
- status: partial

## Review Boundary

- Naturalness review runs after fidelity review.
- Naturalness cannot override fidelity. If fidelity fails, keep or restore the faithful version and record the naturalness limitation.
- This is not an AI-detection-evasion review, a score gate, or a whole-document polish pass.

## Naturalness Checks

| check | result | notes |
|---|---|---|
| detected Korean style risks reduced in the changed spans | not_run |  |
| selected reader and distribution boundary still fit | not_run |  |
| selected document preset and style profile still visible | not_run |  |
| no new stock phrases or generic report conclusions introduced | not_run |  |
| over-certain wording and impressive-sounding jargon are absent or held for review | not_run |  |
| facts, data-based claims, interpretations, estimates, and arguments are not blurred by style edits | not_run |  |
| rhythm improved without rhetorical flourish or essay drift | not_run |  |
| bullets, headings, bold, quotation marks, parenthesis, and visual emphasis are not overused | not_run |  |
| direct quotes, numbers, legal/public/contract/disclosure wording, and source-backed claims were not naturalized | not_run |  |
| over-polish signals are absent or held | not_run |  |

## Residual Style Risks

| finding_id | location | residual_risk | action |
|---|---|---|---|
|  |  |  | leave / second_pass / rollback / human_review |

## Over-Polish And Held Changes

- changed_span_count:
- touched_paragraph_count:
- held_change_count:
- over_polish_status: not_run
- held_for_fidelity:
- held_for_genre_or_reader:

## Decision

- accepted_as_natural:
- second_pass_allowed:
- rollback_needed:
- human_review_needed:
- fidelity_limitation:

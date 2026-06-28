# Style Rewrite Diff

- artifact_type: style_rewrite_diff
- schema_version: 1
- automation_status: guidance_only
- project:
- report_or_chapter:
- style_profile:
- document_preset:
- output_language:
- reviewed_at_kst:

## Boundary

- This is a limited rewrite record, not an automatic whole-document rewrite.
- Rewrite only finding-linked, unprotected spans.
- Do not change direct quotes, numbers, dates, law names, proper nouns, source-backed claims, approved wording, confidentiality labels, contract-like wording, citations, or disclosure text.
- Fail the rewrite if it becomes whole-document polish, broad sentence rewriting only because it sounds better, unsupported concretization, genre-changing style improvement, protected-span paraphrase, or evidence/approval/confidentiality weakening.

## Change Scope

- changed_span_count:
- touched_paragraph_count:
- held_change_count:
- rolled_back_span_count:
- scope_review_result: not_run
- scope_notes:

## Changed Spans

| diff_id | finding_id | location | risk_type | before | after | rationale | protected_span_check |
|---|---|---|---|---|---|---|---|
| SRD-001 | SRF-001 |  | style-only |  |  |  | unchanged |

## Held Or Rejected Changes

| diff_id | finding_id | location | reason_held | required_next_step |
|---|---|---|---|---|
|  |  |  |  | rollback / source check / human review |

## Scope Failure Conditions

Mark `scope_review_result` as `blocked` or `rollback_required` if any of these occurred:

- 전체 문서 윤문.
- 좋아 보이게 하기 위한 과도한 문장 재작성.
- 근거 없는 구체화: owner, metric, example, cause, recommendation, risk, benefit, disclaimer, or commitment added without source/approval basis.
- 장르를 바꾸는 문체 개선: internal report to public copy, partner proposal to contract promise, investor analysis to advice, academic text to opinion essay, or education material to inaccurate simplification.
- Protected span paraphrase for smoothness.

## Notes

- Do not include unrelated source text or raw prompts.
- If the change touches evidence strength, approval wording, securities boundary, legal/regulatory meaning, or genre structure, reject the rewrite and record rollback or human review.

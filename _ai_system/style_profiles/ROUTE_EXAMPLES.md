# Style Profile Route Examples

Use this file when a user describes the desired reader tone without naming a
style profile. These examples are routing aids only. They do not enable
automatic rewrite, automatic polish, legal review, investment judgment, source
verification, or document preset selection.

## Descriptive Requests

| User says | Route | Why | Recommended preset pairing | Ask before routing when |
|---|---|---|---|---|
| "선행연구와 방법론을 갖춘 엄밀한 문서" | `academic_formal` | The strongest cues are literature review, methodology, rigor, citations, and research-reader expectations. | `academic_paper` or `academic_research`; use `regulatory_review` only when the task is policy/regulatory rather than academic. | "엄밀한" only means stronger evidence or legal/regulatory caution without a research/method structure. |
| "아이들이 이해할 수 있도록 쉬운 예시와 활동 중심" | `child_education` | The reader is children/beginner learners and the desired tone is concrete, example-centered, and activity-based. | `education_curriculum`; `product_manual` for learner-facing step-by-step use. | The text contains source-critical, legal, contract, approval, or public wording that simplification could distort. |
| "언론에 배포할 수 있는 공식 발표문" | `press_public` | The distribution channel is media/public and the tone needs approved-fact public statement discipline. | `press_release`; selected public-facing support preset only when approval and disclosure boundaries are known. | Approval status, quote/boilerplate/contact/embargo wording, legal review, or securities disclosure status is unknown. |
| "경영진이 빠르게 판단할 수 있는 요약" | `internal_executive_summary` | The reader is internal decision owners and the tone should foreground conclusion, options, trade-offs, risk, and next action. | `business_strategy`, `general_report`, `investor_brief`, or `equity_research` depending on document structure. | The summary is meant for public release, partner/customer negotiation, or investor-facing external distribution. |
| "파트너에게 제안 범위와 책임을 명확히 전달" | `partner_business` | The reader is an external partner/customer and the style problem is scope, responsibility, condition, and follow-up clarity. | `business_proposal`, `service_planning`, `technical_design`, or `product_manual` when instructions also carry support/responsibility boundaries. | The document is legally binding, a public announcement, or a general beginner procedure without partner/customer obligations. |
| "일반 사용자가 따라할 수 있는 절차 안내" | Ask or route to `child_education` only when beginner/low-prior-knowledge cues are clear. | "Procedure" is primarily a document preset/structure cue. The style profile depends on reader knowledge and risk. | Usually `product_manual`; pair with `child_education` for beginner-friendly examples/steps, or `partner_business` only when customer/partner responsibility and support boundaries are central. | "일반 사용자" simply means ordinary customers, the audience knowledge level is unknown, or the text includes liability/support/contract-like terms. |

## Collision Notes

- `요약` alone is not enough for `internal_executive_summary`; confirm the reader is internal executives or decision owners.
- `외부용` alone is not enough for `press_public`; confirm whether the document is public/media-facing or partner/customer-facing.
- `공식` alone is not enough for `press_public`; approval, disclosure, legal, investor, and contact/boilerplate status must be known.
- `쉬운 설명` alone is not enough for `child_education`; confirm children, beginners, or low-prior-knowledge readers.
- `절차 안내` alone is not enough for a style profile; first choose the document preset, usually `product_manual`.
- `전문가용` alone is not enough for `academic_formal`; confirm research/method/citation expectations instead of business, regulatory, or technical decision context.

## Router Implementation Notes

Future `query_style_profile.py` improvements can read `INDEX.json` in this
order:

1. Exact `profile_id` or executable `aliases`.
2. High-confidence `routing_cues.description_examples`.
3. Weighted `routing_cues.positive_cues` minus `routing_cues.negative_cues`.
4. If two profiles match or any `routing_cues.ambiguous_cues.cue` is present
   without enough positive context, return an ask-needed payload rather than a
   forced match.
5. Include `recommended_document_preset_combinations` as advisory pairing data,
   not as automatic document preset selection.

Keep `automation_status=guidance_only` and `rewrite_automation=not_enabled` in
all query outputs.

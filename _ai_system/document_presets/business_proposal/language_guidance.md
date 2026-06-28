# Business Proposal Language Guidance

Use this file only when the selected preset is `business_proposal` and the PRD/current task needs language or notation guidance. Do not create `business_proposal_en`.

## Korean Default Guidance

- Korean proposals should use clear business prose, conservative benefit claims, and reader-facing labels such as `자료:` and `근거 데이터:`.
- Keep scope, responsibilities, pricing, schedule, acceptance, exclusions, confidentiality, and liability wording precise. Do not turn a proposal into a contract unless the user asks for a contract workflow.

## English Guidance

- English proposals should be direct, specific, and benefit-oriented, but not promotional beyond approved evidence.
- Prefer concrete section names such as `Objective`, `Scope`, `Proposed Approach`, `Deliverables`, `Timeline`, `Commercial Assumptions`, `Risks`, and `Next Steps`.
- Use `Source:`, `Underlying data:`, or `Data basis:` only when the PRD or HTML explicitly marks English or mixed output.
- Keep region spelling and terminology aligned with `language_variant` such as `en-US` or `en-GB`.

## Ask Before Drafting

Ask before drafting when:

- the user instruction is Korean but the recipient is an overseas customer, partner, investor, or procurement team,
- the document may be used as a quotation, SOW, MSA, contract, bid response, or legally binding offer,
- pricing, taxes, delivery obligations, warranties, liability, exclusivity, or confidentiality are material,
- jurisdiction or distribution market is unclear.

## Forbidden Or Caution Expressions

- Do not imply guaranteed outcomes: `guaranteed`, `risk-free`, `best-in-class`, `unmatched`, `fully compliant`, or `legally approved` unless approved evidence supports that exact wording.
- Do not write contract-like commitments such as `shall`, `binding`, `warranty`, `indemnify`, or `liable for` unless the task is explicitly contract drafting with legal review.
- Do not automatically generate jurisdiction-specific disclaimers or legal terms.

## Genre Boundary

This preset supports a proposal. It is not a quotation, SOW, contract, legal opinion, procurement bid, or invoice. If the requested output crosses that boundary, record the issue and route to a separate approved workflow.

## Caption, Source, Accessed, Disclaimer

- Korean output: `자료:`, `근거 데이터:`, `접근일: YYYY.MM.DD`.
- English output: `Source:`, `Underlying data:` or `Data basis:`, `Accessed YYYY-MM-DD`.
- `disclaimer_profile` is guidance only. Do not invent legal disclaimer text.

## Protected Spans

Preserve direct quotes, numbers, dates, prices, delivery terms, company/product names, source-backed claims, approved client language, and contract-like wording unless the source or approval record is deliberately corrected.

# Style Profile Codemap

Use this codemap to route reader-tone work without opening every style profile
folder. The compact machine-readable source is `INDEX.json`; detailed
natural-language cue examples live in `ROUTE_EXAMPLES.md`.

Style profiles are guidance-only modules. They do not perform automatic rewrite,
AI-detection evasion, source verification, legal review, investment judgment, or
score-based gating.

## Fast Human Route

| Description cue | Likely style profile | Good preset pairings | Ask first when |
|---|---|---|---|
| 선행연구와 방법론을 갖춘 엄밀한 문서 | `academic_formal` | `academic_paper`, `academic_research`, `regulatory_review` | "엄밀한" means general evidence discipline rather than research/method/citation form. |
| 아이들이 이해할 수 있도록 쉬운 예시와 활동 중심 | `child_education` | `education_curriculum`, `product_manual`, `general_report` | The reader is not a child/beginner/low-prior-knowledge learner. |
| 언론에 배포할 수 있는 공식 발표문 | `press_public` | `press_release`, selected public-facing support preset only when approved | Public wording, quote, boilerplate, contact, embargo, legal, or investor disclosure approval is not confirmed. |
| 경영진이 빠르게 판단할 수 있는 요약 | `internal_executive_summary` | `business_strategy`, `investor_brief`, `equity_research`, `general_report` | The summary is for external readers, public release, or partner negotiation. |
| 파트너에게 제안 범위와 책임을 명확히 전달 | `partner_business` | `business_proposal`, `service_planning`, `technical_design`, `product_manual` | It is a public announcement, legal/contract finalization, or general beginner procedure. |
| 일반 사용자가 따라할 수 있는 절차 안내 | Usually `child_education` when "general user" means beginner/low-prior-knowledge; otherwise choose `product_manual` preset and ask before selecting a profile. | `product_manual`, `education_curriculum`, `service_planning` | The text includes partner/customer responsibility, support terms, liability, or contract-like scope. |

## Profile Map

| Profile | Route when | Avoid / ask when | Read first |
|---|---|---|---|
| `internal_executive_summary` | Internal executives or decision owners need conclusion-first options, trade-offs, residual risk, and next action. | Public announcements, partner obligations, academic methods, or child/beginner education are the main purpose. | `internal_executive_summary/profile.json`; `internal_executive_summary/tone_rules.md`; `internal_executive_summary/rewrite_protocol.md` |
| `partner_business` | External partners, customers, procurement reviewers, or collaboration stakeholders need scope, responsibility, conditions, and next steps made clear. | "External" means public/media release, or "procedure" means beginner learning rather than partner/customer responsibility. | `partner_business/profile.json`; `partner_business/tone_rules.md`; `partner_business/rewrite_protocol.md` |
| `child_education` | Children, beginner learners, or low-prior-knowledge users need concrete examples, activity-centered explanation, or step-by-step followability. | Simplicity would hide evidence limits, responsibilities, public approval wording, legal terms, or academic precision. | `child_education/profile.json`; `child_education/tone_rules.md`; `child_education/rewrite_protocol.md` |
| `press_public` | Journalists, public stakeholders, customers, or approved distribution recipients need public statement/press release tone. | The text is unapproved, internal-only, partner negotiation, contract-like, legal, securities-sensitive, or not actually for public/media distribution. | `press_public/profile.json`; `press_public/tone_rules.md`; `press_public/rewrite_protocol.md` |
| `academic_formal` | Academic readers, research reviewers, policy researchers, or method-sensitive expert audiences need definitions, literature review, method, limits, and citations foregrounded. | The real need is faster executive judgment, public announcement, partner proposal, or beginner activity guidance. | `academic_formal/profile.json`; `academic_formal/tone_rules.md`; `academic_formal/rewrite_protocol.md` |

## Routing Rule

1. Read `INDEX.json` first when alias or cue routing is enough.
2. Read this `CODEMAP.md` when the profile choice needs human-readable context.
3. Read `ROUTE_EXAMPLES.md` when a descriptive request overlaps profiles or document presets.
4. Read only the selected profile's `profile.json`, `tone_rules.md`, and `rewrite_protocol.md` first.
5. Add `language_guidance.md` only when `output_language` is `en` or `mixed` and the selected profile provides it.
6. For a style pass, also read `korean_tone_workflow_design_v1.md` and the templates under `templates/`.

## Ambiguity Rule

Do not force a profile from a single broad word such as "요약", "공식", "외부용",
"쉬운", "전문가용", "일반 사용자", or "절차". Use the profile only when the
reader, purpose, distribution boundary, and document preset all point in the
same direction. If they do not, ask a short routing question and keep the style
profile undecided until the answer is clear.

Style profiles do not replace document presets. For example, `product_manual`
owns procedure structure; `child_education` may guide tone only when the reader
is a child, beginner, or low-prior-knowledge general user. `business_proposal`
owns proposal structure; `partner_business` may guide tone only when partner or
customer scope/responsibility clarity is the reader-fit problem.

## Timing Rule

Choose the style profile during interview or PRD work, before drafting. Run the
actual expression-correction style pass after body chapters, Chapter 0, and
visual captions are stable, but before assembly. Reassemble after the current
style pass so the assembly manifest can record the current style-pass artifact
hashes.

## Protected Boundary

Protected spans include direct quotes, quoted translations, numbers, units,
dates, law/regulation names, proper nouns, source-backed claims, approved public
statements, boilerplate, disclaimers, contact information, embargo text, and
contract-like scope or liability wording. If reader-fit tone conflicts with a
protected span, hold the change or request human review rather than smoothing
the protected content.

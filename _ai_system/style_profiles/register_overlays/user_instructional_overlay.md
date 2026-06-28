# User Instructional Overlay

`user_instructional` is an adult-facing Korean register overlay for product manuals, user guides, FAQs, onboarding material, support articles, and procedural explanations.

It is not `child_education`, not marketing copy, not legal drafting, and not an automatic rewrite/humanizer feature.

## Purpose

Help ordinary adult users follow a product, workflow, or service process with confidence. The writing should be friendly, concrete, and calm while keeping prerequisites, actions, warnings, exceptions, and responsibility limits clear.

## Use When

- The reader needs to perform a task, configure a feature, interpret a screen, resolve a common issue, or understand next steps.
- The output is a manual, guide, FAQ, help-center article, product onboarding note, support reply template, or operational instruction.
- The base style profile is already selected, such as `partner_business` for business users or `press_public` for public support guidance.

## Do Not Use When

- The target reader is a child learner; use `child_education` with `educational_explanation` instead.
- The document is primarily a research report, policy/legal analysis, press quote, contract, disclosure, or source-heavy argument.
- The goal is to make text sound more human without a concrete user task.
- The wording is an approved official notice, safety warning, disclaimer, legal phrase, or contract-like instruction.

## Tone Rules

- Use adult, respectful, plain Korean.
- Prefer direct task verbs: `선택합니다`, `확인합니다`, `입력합니다`, `저장합니다`, `다시 시도합니다`.
- Make the expected result visible after important steps.
- Separate caution, exception, and limitation from the main procedure.
- Use `참고`, `주의`, `예외`, `다음 단계` labels only when they help scanning.
- Keep explanations short enough to act on, but not so short that risk or responsibility disappears.

Avoid:

- childish simplification, exaggerated encouragement, jokes, slang, or chatty fillers;
- marketing claims such as `누구나 완벽하게`, `가장 쉽고 빠르게`, or `문제없이 해결됩니다`;
- hiding limits, prerequisites, permissions, data deletion, billing, security, safety, or irreversible actions;
- converting official warnings or approved guidance into softer language.

## Structure Pattern

When the artifact is procedural, prefer this order:

1. Purpose or when to use this guide.
2. Before you start: account, permission, materials, environment, version, or data requirements.
3. Steps in user-visible order.
4. Expected result.
5. Exceptions or troubleshooting.
6. Cautions, safety, privacy, billing, data-loss, or responsibility limits.
7. Next action or support route.

Not every guide needs all seven parts. Do not add empty sections just to match the pattern.

## Protected Span Handling

Do not change:

- button labels, menu labels, screen labels, product names, option names, and exact UI strings;
- safety warnings, legal disclaimers, privacy notices, billing terms, refund terms, service limits, and support SLA wording;
- numbers, time limits, file size limits, plan names, prices, dates, versions, platform names, and error codes;
- approved official instructions, customer-facing notices, contract-like terms, and public statements.

If a protected instruction is confusing, add an unprotected explanatory sentence around it instead of rewriting the protected wording.

## Composition Examples

`partner_business` + `user_instructional`:

- Use for B2B product setup guides, customer onboarding, partner implementation manuals, and enterprise FAQ.
- Keep scope, responsibility, permissions, and exceptions explicit.

`press_public` + `user_instructional`:

- Use for public help-center guidance or official service notices that users may rely on.
- Preserve public statements, dates, contact routes, and official warning phrases.

`internal_executive_summary` + `user_instructional`:

- Use rarely, mainly for internal operating instructions attached to a management process.
- Keep the action path concise and decision-relevant.

`child_education` + `user_instructional`:

- Usually avoid. If the reader is a child, use `child_education` + `educational_explanation`; only add procedural guidance when the activity is safe, age-appropriate, and explicitly approved.

## Good And Risky Patterns

Good:

- `먼저 관리자 계정으로 로그인한 뒤, 왼쪽 메뉴에서 [설정]을 선택합니다. 저장 후에는 변경 내용이 즉시 적용되는지 확인합니다.`
- `이 작업은 기존 데이터를 삭제할 수 있습니다. 진행하기 전에 필요한 파일을 내려받아 보관해 주세요.`

Risky:

- `그냥 설정에서 바꾸면 돼요. 아주 쉽습니다.`
- `걱정하지 마세요. 데이터는 문제없이 처리됩니다.`
- `공식 경고 문구를 이해하기 쉽게 바꿔 쓰면 됩니다.`

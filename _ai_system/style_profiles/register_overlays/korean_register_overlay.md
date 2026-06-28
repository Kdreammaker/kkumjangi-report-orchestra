# Korean Register Overlay

This document defines Korean register overlays as a separate axis from style profiles. A style profile answers "who is the reader and what risk posture is needed?" A register overlay answers "what delivery mode should the Korean expression follow?"

These overlays are guidance-only. They do not translate automatically, humanize automatically, bypass protected spans, or promote a report stage.

## Common Rules

1. Confirm `output_language` before drafting or style pass work.
2. Select the base style profile first.
3. Select the register overlay only after the artifact type and delivery scene are known.
4. Preserve the document preset's structure and evidence requirements.
5. Preserve protected spans even when the overlay would normally prefer a smoother phrase.
6. Route ambiguity to human review when register choice may affect approval, hierarchy, disclosure, legal meaning, safety, or contract-like responsibility.

## `written_report` - 문어체 보고문

Use for reports, reviews, proposals, analytical memos, research summaries, policy notes, and formal written deliverables.

Guidance:

- Prefer clear written Korean with complete sentences and visible logical connectors.
- Use respectful but neutral endings such as `-합니다`, `-입니다`, `-로 판단됩니다`, and `-이 필요합니다` when the document context supports them.
- Keep certainty aligned to evidence: do not turn `가능성`, `추정`, `검토 필요` into confirmed facts.
- Use concise headings and paragraph openings that identify topic, basis, and implication.
- Avoid over-formal bureaucratic phrasing when a direct business/report sentence is clearer.

Avoid:

- casual speech endings;
- inflated officialese;
- excessive passive voice that hides actors, responsibility, or uncertainty;
- honorific or humble forms that make the argument unclear.

## `oral_briefing` - 구어체 브리핑

Use for meeting remarks, spoken executive updates, oral presentation notes, interview preparation, and verbal briefing scripts.

Guidance:

- Make sentences speakable, shorter, and easier to follow by ear.
- Keep respect level professional; spoken does not mean overly friendly.
- Use signposting phrases such as `핵심은`, `먼저`, `다음으로`, `결론부터 말씀드리면` when they improve listener orientation.
- Apply honorific and hierarchical naming only when the speaking situation requires it.
- When 압존법 may be relevant, follow `honorific_policy.md` and route unclear hierarchy to review.

Avoid:

- slang, exaggerated friendliness, filler, or chat-style rhythm;
- flattening evidence nuance for the sake of speed;
- rewriting formal approvals, quotes, legal phrases, safety warnings, or official statements into spoken paraphrase unless explicitly approved.

## `public_written` - 외부 공개문

Use for press/public materials, website copy, official announcements, partner-distributable statements, and externally quotable text.

Guidance:

- Keep approved claims, quotes, disclaimers, names, dates, and institutional wording intact.
- Prefer plain, confident, verifiable sentences over promotional overclaim.
- Make subject, scope, timing, and responsibility explicit when public readers may rely on the statement.
- Use respectful written Korean without internal shorthand or unapproved assumptions.

Avoid:

- turning internal analysis into public assurance;
- implying endorsement, certification, legal effect, financial advice, or safety guarantee without approved source wording;
- changing quote blocks or approval wording for readability.

## `educational_explanation` - 교육 설명체

Use for concept explanation, learning material, non-specialist education, onboarding lessons, or explanatory sections that support understanding.

Guidance:

- Explain in steps from familiar idea to new idea.
- Define terms before using them heavily.
- Use examples, comparisons, and short summaries only when they do not distort the evidence.
- Keep the learner's age and prior knowledge separate from the register decision. This overlay is not automatically child-facing.
- For children or low-prior-knowledge readers, combine with `child_education`; otherwise pair with the relevant adult style profile.

Avoid:

- childish tone unless the selected style profile and project brief require it;
- replacing technical/legal/source language when exact wording matters;
- simplifying away exceptions, uncertainty, limitations, or responsibility boundaries.

## `user_instructional` - 사용자 안내/매뉴얼체

Use for adult-facing product guides, manuals, FAQs, onboarding instructions, support articles, setup guides, and operational how-to material.

Primary guidance lives in `user_instructional_overlay.md`.

Short rule:

- Be kind, concrete, and procedural.
- Make prerequisites, steps, warnings, exceptions, expected results, and responsibility limits visible.
- Do not sound childish, promotional, or like a hidden rewrite/humanizer layer.

## Section-Level Use

A single report may use different overlays by section:

- Executive summary: `written_report`
- Presentation script appendix: `oral_briefing`
- Public abstract: `public_written`
- Method explanation sidebar: `educational_explanation`
- Product setup appendix: `user_instructional`

Record report-level overlay choices in the PRD when they are known early. Record section-level overlay choices in the PRD, chapter workpack, planning notes, or style-pass artifacts when different sections need different delivery modes. This is still guidance-only documentation, not automatic rewrite or workflow automation.

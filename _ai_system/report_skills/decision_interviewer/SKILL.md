---
name: decision_interviewer
description: Run a short decision interview before planning, drafting, or final synthesis.
triggers:
  - /grill-me
  - grill me
  - decision interview
  - scope interview
  - clarify strategy
  - ask questions first
  - 질문 먼저
  - 방향 먼저
---

# Decision Interviewer

## Mission

Help the AI ask the few questions that materially improve the report before it writes. This skill exists to improve report quality, not to create a long questionnaire.

Use it when:

- starting a new substantial project,
- turning a rough user idea into a PRD,
- moving from PRD to detailed TOC,
- moving from skeleton to chapter workpacks,
- resolving strategic ambiguity before Chapter 0,
- the report risks becoming generic, shallow, or overconfident.

## Operating Rules

- Ask 3 to 7 questions by default.
- Prefer sharp tradeoff questions over broad forms.
- Each question must say why it matters to the report.
- Do not ask for information the workspace can discover from files.
- Do not draft report prose during the interview.
- After the user answers, summarize the decisions and record durable decisions in `questions/question_log.md` or the active PRD/workpack.
- If the user says "just proceed", convert only the current known intent into assumptions and mark unresolved items as assumptions or risks.

## Question Types

Use the smallest useful set:

1. Decision target: What decision should the reader make after reading?
2. Audience pressure: Who must be convinced, and what would make them reject the report?
3. Scope boundary: What should be explicitly excluded?
4. Strategy fork: Which path should be primary, fallback, or only exploratory?
5. Evidence bar: What claims require primary-source proof before they can appear?
6. Risk tolerance: Should the report be conservative, exploratory, or advocacy-oriented?
7. Output shape: What final artifact matters most: HTML, DOCX, slide brief, memo, source pack, or appendix?

## Output Shape

Return a compact interview packet:

- `questions`: numbered questions with why-it-matters.
- `assumptions_if_unanswered`: safe assumptions the AI may use if the user does not answer.
- `files_to_update_after_answer`: PRD, detailed TOC, skeleton, workpack, question log, or assumption register.
- `blocked_until_answer`: only items that truly cannot proceed safely.

## Anti-Patterns

- Do not ask twenty generic discovery questions.
- Do not use the interview to delay obvious setup work.
- Do not turn user preferences into confirmed facts.
- Do not hide unresolved uncertainty in polished prose.

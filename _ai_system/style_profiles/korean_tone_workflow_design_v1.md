# Korean Tone And Style Workflow Design v1

Status: guidance-only workflow, systemized for style-pass use
Implementation status: linked to style profile routing, context packets, current-task guidance, and artifact templates; no automatic rewrite, validator gate, score gate, or AI-detection-evasion workflow is introduced
Primary scope: Korean report/document production support through reader-fit style review

## 1. Design Intent

This workflow helps AI-assisted report production preserve Korean reader fit, document genre, meaning, source strength, and approved wording. It is not an "AI tell remover" and must not make weak evidence sound stronger, convert one document genre into another, or rewrite protected content for smoothness.

The workflow should be used after the document preset, PRD, output language, reader, classification, confidentiality, and style profile are known or explicitly marked unresolved.

Core rule:

1. Detect style risks before rewriting.
2. Mark protected spans before any rewrite.
3. Rewrite only detected, unprotected spans.
4. Record held changes as deliberately as accepted changes.
5. Review fidelity before naturalness; naturalness cannot override fidelity.
6. Roll back, run a narrow second pass, or request human review when meaning, evidence strength, approval wording, or genre fit is at risk.

## 2. Reference Adaptation From `epoko77-ai/im-not-ai`

The external reference is useful for these structural ideas:

- span-based detection rather than whole-document rewriting,
- detailed Korean style-risk taxonomy with sub-patterns,
- severity-aware handling of high-risk, repeated, and weak clustered patterns,
- limited rewriting tied to detected spans,
- separate fidelity audit and naturalness review,
- explicit over-polish/change-rate awareness.

This system changes the purpose and boundary:

- The goal is not to disguise AI authorship. The goal is reader-appropriate Korean document quality.
- The unit of control is the report workflow: PRD, document preset, style profile, source/claim status, approval boundary, and final artifact.
- Direct quotes, numbers, dates, laws, proper nouns, source-backed claims, approved phrases, contract/public wording, and disclosure text are protected spans.
- Genre preservation is stricter than generic humanization. A report must not become an essay; a press release must not become marketing copy; investor analysis must not become investment advice.
- Scores are advisory risk signals only. They do not prove accuracy, legal correctness, source truth, or delivery readiness.
- Change-rate thresholds are not automatic gates. Reviewers record changed span count, touched paragraph count, held changes, and rollback decisions instead.

## 3. Korean Style-Risk Taxonomy Draft

Use this taxonomy as a detection vocabulary. It is not a command to rewrite every occurrence. Some patterns are acceptable when the genre, source wording, legal/technical convention, or approved phrasing requires them.

Each finding should record:

- taxonomy id,
- sub-pattern id or short label,
- severity: `blocker`, `high`, `medium`, `low`,
- risk type: `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, `reader-fit`,
- protected-span status: `fully_protected`, `mixed`, `unprotected`, `unknown`,
- suggested action: `leave`, `limited_rewrite`, `source_check`, `structure_review`, `human_review`, `rollback`.

### KR-T01 Translationese

Sub-patterns:

- T01-a: topic/object padding such as "~에 대해", "~와 관련하여", "~에 있어서" where direct object, topic marker, or plain condition works better.
- T01-b: means/path padding such as "~를 통해", "~에 기반하여", "~을 바탕으로" repeated where a verb or shorter postposition is clearer.
- T01-c: English-style passive agency such as "~에 의해", "~로부터", "생성된/도출된" where actor restoration is safe.
- T01-d: English left-branching relative clauses that place too many modifiers before the head noun.
- T01-e: literal pronoun or inanimate-subject transfer that makes Korean responsibility or actor unclear.
- T01-f: double particles or stiff noun chains created by translating English noun phrases into Korean without restoring Korean case relations.

Limited response:

- Replace only unprotected connective wording or sentence frame.
- Restore actor, object, or predicate only when the draft/source already supports it.
- Keep official terms, source titles, product names, and approved bilingual labels unchanged.

### KR-T02 Mechanical Parallel Structure

Sub-patterns:

- T02-a: repeated "첫째/둘째/셋째" structure used even when the items differ in evidence weight or decision priority.
- T02-b: every paragraph following the same "배경 -> 의미 -> 시사점" pattern.
- T02-c: bullets with identical grammar, length, and abstract nouns that flatten importance.
- T02-d: symmetrical section balance that hides a major risk, blocker, or dependency.
- T02-e: mechanical "문제/원인/대응" pairing when the document needs timeline, owner, or decision order.

Limited response:

- Convert to decision order, risk order, time order, reader question order, or evidence weight when the document genre supports it.
- Do not change TOC structure unless the task is a structural revision.
- Preserve mandated list formats in checklists, legal disclosures, tables, and report templates.

### KR-T03 Excessive Connectors And Sentence Openers

Sub-patterns:

- T03-a: repeated 문두 connectors such as "또한", "따라서", "결론적으로", "한편", "나아가", "즉".
- T03-b: connectors used to imply causality, contrast, or conclusion without claim-register support.
- T03-c: one-sentence paragraphs that exist only to bridge sections.
- T03-d: connector stacking such as "따라서 또한", "즉, 결과적으로", or repeated "이에 따라".
- T03-e: formal connector rhythm that makes a practical document sound like a generic essay.

Limited response:

- Delete weak connectors or replace with concrete actor, condition, evidence, decision, or risk wording.
- Preserve causal caution when evidence is limited.
- If removing the connector changes the logic, hold the span and request source/argument review.

### KR-T04 Stock Report Phrases And Empty Implications

Sub-patterns:

- T04-a: empty implication phrases such as "시사하는 바가 크다", "중요한 의미를 가진다", "주목할 만하다".
- T04-b: unsupported positive labels such as "혁신적", "차별화된", "획기적", "선도적".
- T04-c: conclusion labels that repeat the section function instead of stating the decision or residual risk.
- T04-d: "향후 기대된다", "필요성이 대두된다", "관심이 요구된다" without owner, trigger, or action.
- T04-e: generic summary sentences that do not name action, risk, owner, reader decision, or evidence.

Limited response:

- Replace with the actual implication only if already supported in the draft, source record, claim register, PRD, or approved brief.
- If no implication is supported, delete the sentence or flag for human review.
- Do not add business strategy, recommendation, disclaimer, or legal interpretation to make the prose feel grounded.

### KR-T05 Modifier And Abstract-Noun Overuse

Sub-patterns:

- T05-a: dense suffix chains such as "~적", "~성", "~화", "방향성", "가능성", "효율성", "고도화".
- T05-b: English nominalization residue such as "-tion/-ment/-ity" translated into stacked Korean nouns.
- T05-c: decorative degree words such as "매우", "상당히", "대단히", "핵심적인" without metric, comparison, or threshold.
- T05-d: duplicate modifiers such as "중요하고 핵심적인", "효율적이고 효과적인" where one meaning is enough.
- T05-e: abstract nouns used to avoid actor, scope, metric, or condition.

Limited response:

- Replace abstract nouns with concrete action, metric, scope, owner, or condition when known.
- Remove decorative modifiers before inventing specifics.
- Do not make a cautious or incomplete claim sound quantified.

### KR-T06 Passive, Causative, Hedging, And Formal-Noun Overuse

Sub-patterns:

- T06-a: double passive or stiff passive such as "~되어진다", "~지게 된다", "~로 판단된다".
- T06-b: actorless responsibility wording that hides owner, approver, or operational action.
- T06-c: stacked hedging such as "~할 수 있을 것으로 보인다", "~일 가능성이 있을 수 있다".
- T06-d: formal nouns such as "것", "점", "수", "바", "측면", "부분" creating long indirect sentences.
- T06-e: "필요가 있다", "요구된다", "검토되어야 한다" used without decision owner or next step.

Limited response:

- Use active voice when actor and responsibility are known.
- Keep passive or cautious phrasing when actor is unknown, legally sensitive, evidence-limited, or intentionally non-accusatory.
- Replace formal nouns only when doing so does not change claim strength.

### KR-T07 Rhythm Uniformity

Sub-patterns:

- T07-a: similar sentence lengths across a paragraph, especially repeated mid-length explanatory sentences.
- T07-b: repeated endings such as "~입니다", "~합니다", "~할 수 있습니다", "~이다" without purposeful rhythm.
- T07-c: every paragraph ending with the same summary or implication pattern.
- T07-d: long sentences with multiple commas that should be split for report readability.
- T07-e: short-sentence monotony that makes an executive or educational document feel chopped instead of clear.

Limited response:

- Split overloaded sentences and vary sentence length only where readability improves.
- Do not add rhetorical flourishes, personal voice, or essay-like texture that weakens report tone.
- Keep tables, captions, legal wording, and approved boilerplate rhythm unchanged.

### KR-T08 Bullet, Heading, Parenthesis, And Emphasis Overuse

Sub-patterns:

- T08-a: too many bullets, heading levels, colon-led labels, or bold spans in place of argument hierarchy.
- T08-b: repeated parenthetical English terms after the first useful definition.
- T08-c: quotation marks used for emphasis instead of actual quotation or special term status.
- T08-d: visual separators, long dashes, or decorative labels that make a report look over-produced.
- T08-e: table/list formatting used when sequence, magnitude, dependency, or decision logic would be clearer in prose or a diagram.

Limited response:

- Reduce emphasis to actual decisions, risks, conditions, source status, and required approvals.
- Keep mandated headings, TOC-defined units, disclosure labels, tables, captions, and report template structure.
- Do not remove parenthetical English terms that are official, regulated, contractual, or useful for a professional reader.

### KR-T09 Report Genre Drift

Sub-patterns:

- T09-a: internal report becomes essay-like commentary or thought leadership.
- T09-b: partner document becomes sales copy or accidental contract commitment.
- T09-c: press release becomes promotional marketing copy or internal-risk explanation.
- T09-d: academic or research document becomes opinion essay or advocacy memo.
- T09-e: investor brief, sector analysis, or company analysis becomes investment recommendation, fundraising hype, or target-price advice.
- T09-f: child education material becomes adult policy brief, fear-heavy warning, or oversimplified factual distortion.

Limited response:

- Restore the selected document preset and style profile boundary.
- If genre drift affects structure, stop the style pass and request a report-structure revision.
- Do not convert internal drafts into public copy through style pass alone.

### KR-T10 Reader-Misaligned Tone

Sub-patterns:

- T10-a: executive summary hides decision, owner, timing, or blocker behind background narration.
- T10-b: partner/customer document sounds vague, binding, self-congratulatory, or too internal.
- T10-c: education material uses unexplained jargon, abstract policy language, fear-heavy wording, or examples that overtake the claim.
- T10-d: public statement exposes internal rationale, unapproved claims, unvetted future commitments, or weak source status.
- T10-e: academic document sounds promotional, over-certain, or under-cited.
- T10-f: investor/sector/company analysis sounds like guaranteed return, buy/sell/hold guidance, target-price advice, or fundraising copy.

Limited response:

- Adjust only tone elements that affect reader comprehension, trust, or approval safety.
- Do not change classification, evidence strength, approval status, jurisdiction boundary, or legal/regulatory boundary.
- If reader fit requires new explanation, example, disclaimer, or risk framing, hold the edit unless the PRD/source/owner supports it.

### KR-T11 Over-Certainty And Impressive-Sounding Jargon

Sub-patterns:

- T11-a: fact, correlation, precedent, or model result is written as proof of causation without the required method/source support.
- T11-b: "증명되었다", "확정된다", "반드시", "구조적으로", "극도로", "완벽히" used where the evidence only supports a possibility, pattern, interpretation, or estimate.
- T11-c: impressive but nonstandard English/Korean hybrid terms that are not source terms, domain terms, or useful reader vocabulary.
- T11-d: a debate, seminar, handout, or shared internal note uses combative language that would make the document look like an advocacy script rather than a reviewable discussion artifact.

Limited response:

- Separate `fact`, `data_based`, `interpretation`, `estimate`, and `argument` before rewriting.
- Convert causal or certain wording to conditional wording only when the source/claim record does not support certainty.
- Keep genuinely technical terms, but replace invented or showy labels with reader-understandable Korean terms unless the PRD requires the original term.
- If the artifact will be shared with discussion participants, prefer neutral debate-ready wording over attack, persuasion, or "weapon" metaphors.

## 4. Severity System

Keep the local severity labels: `blocker`, `high`, `medium`, `low`. Do not create a score-based pass gate.

Use the external S1/S2/S3 idea only as a review lens:

| external lens | local severity mapping | handling rule |
|---|---|---|
| S1-equivalent | usually `blocker` when the span is protected, approval-sensitive, evidence-related, public/legal/securities/contract-risk, or genre-drifting; otherwise `high` | One occurrence can be enough to stop acceptance, require rollback, or request human/source review. |
| S2-equivalent | usually `high`; may be `medium` if localized and unprotected | Repetition, density, or reader-trust damage makes it a required finding. Fix only eligible spans. |
| S3-equivalent | usually `low`; becomes `medium` when clustered with other risks | Leave alone unless clustered, distracting, or easy to fix without touching protected meaning. |

Severity guidance:

- `blocker`: protected span drift; approval wording drift; legal/public wording drift; confidentiality leak; contract commitment change; investment-advice risk; serious genre drift; likely meaning, evidence-strength, or source-relationship change.
- `high`: repeated pattern that harms reader trust, evidence interpretation, genre boundary, or approval safety.
- `medium`: localized style issue that can be revised safely and improves reader fit.
- `low`: optional polish; usually leave unchanged unless clustered or already adjacent to a safe limited rewrite.

Severity is not a quality score. A style pass can be `partial` even with few findings if fidelity or approval status is unresolved.

## 5. Protected Span Policy

Protected spans must be marked before rewriting. They include:

- direct quotes and quoted translations,
- numbers, units, dates, percentages, prices, financial metrics, formulas, and valuation terms,
- law names, article numbers, regulation names, official program names, court/regulator wording, and official instructions,
- proper nouns, company names, product names, partner/customer names, people names, jurisdiction names, issuer names, and ticker symbols,
- source-backed claims, claim-register wording, citations, source titles, source ids, access dates, and data-as-of labels,
- approved public statements, quotes, boilerplate, disclaimers, contact information, embargo text, approval wording, confidentiality labels, and disclosure text,
- contract-like scope, responsibility, price, schedule, acceptance, exclusion, liability, confidentiality, or public-release wording.

If a style risk is embedded inside a protected span, do not rewrite it. Options are:

- leave unchanged,
- split surrounding unprotected connective wording,
- add a review note,
- request source-checked or owner-approved correction.

## 6. Tone Passes By Document Type And Reader

### Internal Executive Summary

Purpose: support decision, escalation, or prioritization.

Detect:

- delayed conclusion,
- vague implication,
- repeated connectors,
- hidden owner or decision need,
- uncertainty polished away,
- generic conclusion language replacing risk status.

Limited rewrite:

- put decision need, risk, owner, blocker, or next action earlier,
- shorten background,
- preserve caveats, evidence limits, and unresolved items.

Fail conditions:

- recommendation added without source or mandate,
- risk wording weakened,
- unresolved issue made to sound closed,
- investor/market language becomes action advice.

### Partner Or Customer Document

Purpose: build trust, clarify scope, and avoid accidental commitment.

Detect:

- hype,
- vague value claims,
- binding-sounding terms,
- hidden assumptions,
- internal-only rationale,
- over-friendly tone that obscures scope or responsibility.

Limited rewrite:

- replace hype with concrete condition/value wording,
- distinguish proposal, assumption, confirmed commitment, and approval-needed items,
- keep scope, exclusions, owner, schedule, and handoff visible.

Fail conditions:

- draft phrase becomes contractual commitment,
- approved wording changes,
- value claim gains certainty,
- internal risk or confidential rationale becomes externally visible.

### Child Education Material

Purpose: make learning sequence clear without distorting facts.

Detect:

- unexplained jargon,
- long abstract explanations,
- fear-heavy tone,
- examples that may replace evidence,
- uniform textbook-like rhythm,
- adult business/policy register.

Limited rewrite:

- split into smaller learning steps,
- define necessary terms in plain Korean,
- add simple examples only when they do not change the claim,
- keep warnings calm but clear.

Fail conditions:

- simplification becomes inaccurate,
- safety warning is softened,
- example implies a fact not in the source,
- child-friendly tone becomes childish when the reader is older or mixed.

### Press Release Or Public Statement

Purpose: communicate approved public facts clearly and safely.

Detect:

- unapproved claims,
- internal-risk exposure,
- report-style analysis,
- marketing exaggeration,
- quote or boilerplate drift,
- future commitment without approval status.

Limited rewrite:

- shorten lead without adding claims,
- remove or hold internal rationale,
- keep attribution and approval status explicit,
- preserve approved quote, contact, embargo, and boilerplate wording.

Fail conditions:

- public claim lacks approval/source status,
- headline overstates,
- legal/contact/embargo/quote wording changes,
- analysis becomes a public commitment.

### Academic Or Paper-Like Document

Purpose: preserve method, source boundaries, and argument discipline.

Detect:

- unsupported causal language,
- promotional tone,
- mixed source fact and author inference,
- vague method wording,
- excessive rhetorical formality,
- citation or locator drift.

Limited rewrite:

- label sentence role as definition, literature summary, finding, interpretation, or limitation,
- separate source paraphrase from inference,
- preserve citation style and locators,
- keep uncertainty and limitation visible.

Fail conditions:

- paraphrase gains new analysis,
- inference reads as source fact,
- limitation disappears,
- citation, statistic, or method wording changes for smoothness.

### Investor Brief, Sector Analysis, Or Company Analysis

Purpose: provide concise, evidence-backed business or market analysis without becoming investment advice.

Detect:

- guaranteed-return or certainty language,
- target-price/rating language without authorization,
- growth or valuation hype,
- missing data vintage, currency, unit, or source date,
- internal metrics mixed with external-shareable claims,
- public/partner tone applied to securities-sensitive analysis.

Limited rewrite:

- separate confirmed data, estimate, interpretation, assumption, and open risk,
- keep as-of dates, units, currency, source basis, and approval status visible,
- use cautious projection wording without inventing legal disclaimers.

Fail conditions:

- wording implies buy/sell/hold, target price, suitability, or guaranteed return,
- confidential KPI becomes externally shareable,
- valuation or forecast confidence increases.

## 7. Same Pattern, Different Profile Response

The same surface pattern can require different action depending on reader and document genre.

### Pattern: "중요한 의미를 가진다"

| profile | reader-fit response |
|---|---|
| `internal_executive_summary` | Replace with decision implication: "따라서 이번 주에는 A 승인 여부를 정해야 한다." Only if the decision need already exists. |
| `partner_business` | Replace with scoped value: "이 항목은 착수 범위와 검수 책임을 정하는 데 영향을 준다." Avoid promise language. |
| `child_education` | Replace with learning point: "여기서 기억할 점은 A와 B를 구분하는 것이다." Keep age fit. |
| `press_public` | Delete unless the approved fact needs a concise public implication. Do not add promotional interpretation. |
| `academic_formal` | Replace with source-bounded interpretation: "이 결과는 A 조건에서 B 가능성을 보여준다." Preserve limitation. |

### Pattern: excessive English parenthesis

| profile | reader-fit response |
|---|---|
| `internal_executive_summary` | Keep official KPI/product terms; remove repeated English after first definition if it slows decision reading. |
| `partner_business` | Keep terms needed for shared scope or integration; define once and use the agreed label consistently. |
| `child_education` | Use Korean explanation first; keep English only if it is the learning target. |
| `press_public` | Keep brand, official feature name, or approved bilingual wording; avoid repeated technical parenthesis in the lead. |
| `academic_formal` | Keep established scholarly terms, original-language constructs, and citation terminology when needed for precision. |

### Pattern: hedging and passive wording

| profile | reader-fit response |
|---|---|
| `internal_executive_summary` | Convert to active owner/action when known; keep uncertainty if decision risk is unresolved. |
| `partner_business` | Avoid both overcommitment and evasiveness; name conditions, assumptions, and approval-needed items. |
| `child_education` | Use direct, calm sentences; do not create false certainty in safety or science topics. |
| `press_public` | Keep approved cautious wording for regulatory, legal, future, or financial statements. |
| `academic_formal` | Preserve hedging where method, sample, or inference limits require it. |

### Pattern: bullet and bold overuse

| profile | reader-fit response |
|---|---|
| `internal_executive_summary` | Keep bullets for decisions, risks, owners, and dates; remove decorative emphasis. |
| `partner_business` | Keep bullets for scope, assumptions, deliverables, and responsibilities; avoid sales-card rhythm. |
| `child_education` | Use short lists for steps or concepts, but avoid dense nested bullets. |
| `press_public` | Minimize bullets; public copy usually needs a clear lead, facts, quote, and boilerplate. |
| `academic_formal` | Prefer prose or tables unless the preset explicitly calls for enumerated items. |

## 8. Workflow

### Step 1. Drafting Completes

Input should be a chapter fragment, section draft, assembled reading copy excerpt, press/public draft, investor/partner brief section, or education material section.

Required context:

- document preset,
- style profile,
- output language,
- reader and distribution boundary,
- classification and confidentiality,
- source/claim status where claims are involved.

If output language, reader, classification, or external-sharing boundary is undecided, do not perform a style rewrite. Ask or mark blocked.

### Step 2. Style-Risk Detection

Produce a finding list:

- span id,
- location,
- taxonomy id and sub-pattern,
- severity: `blocker`, `high`, `medium`, `low`,
- S-lens: `S1-equivalent`, `S2-equivalent`, `S3-equivalent`, or `none`,
- risk type: `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, `reader-fit`,
- protected-span status,
- suggested action: leave, limited rewrite, source check, structure review, human review.

### Step 3. Protected Span Marking

Before rewriting, mark protected spans and classify the surrounding sentence:

- fully protected: no rewrite,
- mixed: revise only unprotected connective wording,
- unprotected: eligible for limited rewrite,
- unknown: hold for source/owner review.

### Step 4. Limited Rewrite Only

Rules:

- rewrite only finding-linked spans,
- preserve claim type, actor, timing, scope, confidence, caveat, and source relationship,
- do not add new claims, examples, recommendations, disclaimers, legal/securities wording, or public commitments,
- keep document preset and style profile boundaries,
- track each changed span,
- track each held or rejected change.

Explicit failure conditions:

- whole-document polish without finding-linked spans,
- broad sentence rewriting only because it "sounds better",
- unsupported concretization such as adding owner, metric, example, cause, recommendation, risk, or benefit not present in the evidence base,
- genre-changing improvement such as turning an internal report into public copy, a partner proposal into a contract promise, or investor analysis into advice,
- protected span paraphrase for smoothness,
- change that weakens uncertainty, caveat, source relationship, approval status, or confidentiality.

### Step 5. Fidelity Review

Check whether the revised text preserves:

- facts, numbers, dates, names, citations, and source locators,
- claim type: direct quote, paraphrase, data-based statement, inference, recommendation,
- evidence strength and uncertainty,
- approval, confidentiality, contract, and public wording,
- genre and document purpose,
- changed span count, touched paragraph count, held changes, and rollback decisions.

If any fidelity check fails, reject the edit or roll back the affected span.

### Step 6. Naturalness Review

Run naturalness review after fidelity review, using `style_naturalness_review.md` or an equivalent section in the active style-pass notes.

Check whether the revised text:

- reduces the detected Korean style risk,
- remains appropriate for the selected reader and distribution boundary,
- avoids over-polish,
- avoids new stock phrases,
- avoids rhythm uniformity introduced by the rewrite,
- does not overuse bullets, headings, bold, parenthesis, quotation marks, or rhetorical pacing,
- keeps the selected document preset and style profile visible.

Naturalness review cannot override fidelity failure. If a natural version conflicts with fidelity, keep the faithful version and record the naturalness limitation.

### Step 7. Decision

Accept:

- all protected spans preserved,
- meaning and evidence strength preserved,
- reader fit improved,
- genre maintained,
- change scope is limited and auditable.

Second pass:

- only when residual issues are localized and low-risk.

Rollback:

- when meaning, evidence strength, approval wording, protected span, or genre changed.

Human review:

- when rewrite requires source interpretation, legal/public approval, securities boundary judgment, contract wording, child-safety judgment, or document-genre restructuring.

## 9. Implementation Split

### Systemize Now

These are part of the guidance system:

- common style-profile design note,
- protected-span policy for all style-profile revisions,
- style pass notes that distinguish `style-only`, `evidence-related`, `approval-sensitive`, `genre-drift`, and `reader-fit`,
- tone pass selection in PRD/current-task language when Korean style work is requested,
- artifact templates for risk findings, protected spans, rewrite diff, fidelity review, and naturalness review,
- automation status remains `guidance_only`.

### Rule Documents Are Enough For Now

These remain human/AI procedure, not validators:

- nuanced reader-fit judgment,
- whether a sentence sounds too essay-like or too promotional,
- whether a simplification is pedagogically helpful,
- whether a public statement sounds approved enough for release,
- whether investor analysis crosses into advice,
- whether a changed span count is too broad for the requested style pass.

### Hold For Later

Do not implement now:

- automatic whole-document Korean rewrite,
- automatic protected-span extraction that rewrites around uncertain spans,
- automatic change-rate scoring as an acceptance gate,
- AI-authorship disguise language,
- jurisdiction-specific legal, securities, or public-disclosure disclaimer generation,
- auto-conversion of internal drafts into public documents,
- automatic naturalness scoring or A-D grading.

### Future Validator Or Tool Candidates

These are candidates for later approval:

- `detect_korean_style_risks.py`: report taxonomy-tagged findings without rewriting,
- `mark_protected_spans.py`: identify obvious protected spans and produce a review map,
- `validate_style_pass_fidelity.py`: compare original/revised spans for protected-span drift and numeric/name/date changes,
- `validate_style_profile_alignment.py`: check PRD-selected style profile against document preset and report classification,
- optional style-pass artifact schema validation, if separately approved later.

## 10. Minimal Artifact Model

For guidance-only style-pass work, keep outputs small and auditable:

- `style_risk_findings.json`: findings, locations, taxonomy ids, sub-patterns, S-lens, severity, protected-span status, and recommended action.
- `protected_spans.json`: protected span map with type and source of protection.
- `style_rewrite_diff.md`: only changed spans, before/after, rationale, changed span count, touched paragraph count, and held changes.
- `style_fidelity_review.md`: pass/partial/blocked/rollback/human-review result with fidelity and change-scope checks.
- `style_naturalness_review.md`: reader-fit naturalness review, residual style risks, over-polish check, and the explicit rule that naturalness cannot override fidelity.

Do not store raw prompts, hidden instructions, or unrelated source text in shared style artifacts.

Templates are stored in `_ai_system/style_profiles/templates/`. Context packets include these templates when a style profile is selected or `--stage style` is requested.

## 11. Workflow Placement

- `INDEX.json` names this file as the common Korean tone workflow.
- `query_style_profile.py` includes this workflow and the style-pass templates with matched style-profile assets.
- `compose_report_context.py --stage style --style-profile <profile>` or `--style-query <tone>` produces a context packet showing which workflow files to read and which artifacts to leave.
- `tasks/current_task.md` may use a `style` row when style review is the active work unit.

Investor brief, sector analysis, and company analysis stay in document presets for structure, evidence, visuals, and review checklist. Their tone pass uses this common workflow plus the selected style profile, not a duplicate investor-specific rewrite engine.

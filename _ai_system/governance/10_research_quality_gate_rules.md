# Research Quality Gate Rules

## Purpose

This rule prevents a report from treating plausible AI-written research text as verified source evidence.

Use this rule whenever sources, source records, claim registers, citations, legal/regulatory statements, benchmark cases, estimates, or report conclusions are created or revised.

This rule complements:

- `_ai_system/governance/01_research_evidence_rules.md`
- `_ai_system/governance/02_report_workflow_rules.md`
- `_ai_system/governance/08_reference_intake_rules.md`
- `_ai_system/governance/11_gate_based_execution_rules.md`
- `_ai_system/governance/12_report_quality_scoring_rules.md`

## Core Principle

Workspace validation proves that the working system is organized and runnable. It does not prove that research claims are true.

Do not describe a report, source pack, or claim register as verified, final, evidence-backed, or ready for business use unless the research quality gate has been checked.

## Evidence Classes

Classify every research artifact before it supports a report claim.

| evidence_class | Meaning | May support `confirmed_fact`? |
|---|---|---|
| `original_official` | Official statute, regulation, regulator page, filing, official PDF, official HTML capture, official dataset, or official exchange/company document. | yes |
| `original_commercial` | Primary company, issuer, exchange, or partner material that is not legal/regulatory. | yes, for that issuer/company's own statements |
| `original_secondary` | Reputable news, law firm note, research report, academic paper, or professional analysis. | only for what that source says; not for legal conclusions alone |
| `captured_webpage` | Saved HTML/PDF/screenshot capture of a live webpage with URL and access time. | yes, if publisher tier supports it |
| `extracted_text` | Text extracted from a preserved original. | only if linked to the preserved original |
| `working_translation` | AI or human working translation of a foreign-language original. | no, unless paired with original text |
| `ai_working_summary` | AI-written summary, synthesis, or memo derived from one or more sources. | no |
| `analysis_note` | Analyst interpretation or hypothesis. | no |
| `unknown_origin` | File or note whose origin cannot be verified. | no |

## Original Source Boundary

`references/received_originals/` is for true originals only.

Allowed:

- user-provided original files,
- exact official URLs with verified access and quote/location locators,
- user-provided official PDFs/files,
- saved official HTML pages,
- SEC/EDGAR filings,
- law or regulation text captured from an official database,
- screenshots or page captures when the layout itself is evidence.

Not allowed as originals:

- AI-written summaries,
- AI-translated summaries without the source text,
- manually rewritten excerpts without source location,
- notes that say they are "based on" a source but do not preserve the source,
- synthetic examples or reconstructed quotations.

Store non-original derivatives under the relevant project:

- `evidence/extracted_text/`
- `evidence/web_captures/`
- `evidence/ocr/`
- `notes/source_working_summaries/`
- `translation/working_translations/`

If a derivative is currently stored under `references/received_originals/`, mark it as `ai_working_summary`, `analysis_note`, or `unknown_origin`, and do not cite it as a source until a real original is added.

## Source Readiness Status

Use these statuses in source records, source indexes, or notes where practical.

- `inventoried`: listed in the reference inventory only.
- `link_confirmed`: exact official URL/source locator, publisher, and access date are registered. This is useful triage, but it is not by itself quote verification or report-citable evidence.
- `original_preserved`: original file, official URL capture, or official URL has been preserved with access date.
- `parsed`: text extraction, OCR, or capture processing was completed.
- `source_record_draft`: source record exists but has not been checked against the original.
- `quote_verified`: exact quotes were checked against the preserved original or official live source.
- `claim_ready`: source can support claim-register rows, subject to claim type.
- `report_citable`: source can be cited in the reader-facing report.
- `rejected`: source is unreliable, stale, unverifiable, irrelevant, or incorrectly stored.

Minimum report-use rule:

- A source must be at least `claim_ready` before supporting a claim register row.
- A source must be `report_citable` before appearing as a reader-facing citation.
- `inventoried`, `parsed`, or `source_record_draft` alone is not enough.
- A generic homepage URL such as a regulator home page, company home page, or statute portal top page is not enough for `original_verified=yes` or `report_citable`. Use an exact document URL and page/section/quote locator, or a user-provided/captured original when file-level evidence is required.
- Dummy PDFs, placeholder PDFs, shell PDFs, AI-written extraction stubs, or files created only to satisfy a validator are not originals. They must be marked rejected/not_verified and cannot support `Fact`, `confirmed_fact`, or `report_citable`.
- `source_id`, title, publisher, and original path must describe the same source. Do not assign a market report source id to an unrelated internal PDF or a statute source id to a generic law portal page.
- Source index titles and source record titles must not add unsupported benchmark names, institutions, statutes, or jurisdictions that are absent from the original source metadata or exact-quote section.
- Exact quote sections must contain source-specific wording with enough length and context to verify against the original. Generic portal text, page chrome, document category labels, or a regulator/company name alone cannot move a source to `quote_verified`.
- If source metadata and locator disagree, the source is blocked. A law database URL cannot verify a political pledge, company page, market report, or regulator release unless the law database is actually the cited source and the record title/publisher say so.
- AI should not manually promote a source to `report_citable` just by filling fields. Promotion must be supported by preserved original evidence and checked by the research integrity tool.
- `report_citable` requires a physical source record under `references/source_records/` with enough detail to audit the source. A source index row alone is not sufficient.
- The source record must point to a preserved user-provided original file, exact official URL, or explicitly requested captured webpage/PDF. Generic homepages, portal top pages, and AI-written summaries are not sufficient.
- URL-only report-citable sources must also have a row in `references/source_link_register.csv` with an exact non-generic URL, access time, verified URL status, source locator, and `use_level=quote_verified` or `report_citable`. If file-level evidence is needed, track it in `references/user_requested_materials.md` instead of pretending the source is preserved.
- Do not attempt AI downloads or web captures merely because a URL source exists. Keep the source at lead/url-only/collection-blocked level until the exact link, locator, and source-record evidence support report use.
- URL-only quote verification is an AI review task over exact links and recorded locators. Fetch/capture tools are optional manual audit aids, not normal production gates.
- Overseas benchmark cases must be supported by original or high-quality source records for the specific case. Internal strategy slides may identify a benchmark lead, but they do not verify the foreign case as fact.
- A report that names an external company, regulator, filing, law, product structure, dataset, market precedent, or benchmark case must have a source record for that named case. A source that briefly mentions one example does not verify another named example or adjacent case.

## Claim Readiness Rules

Every material claim should include or be traceable to:

- `claim_id`
- `claim_type`
- `citation_type`
- `claim_status`
- `source_id`
- `evidence_class`
- `source_readiness_status`
- `original_verified`
- `exact_quote_location` when the claim is a fact or quote
- `assumption_id` and `data_file_id` when the claim is an estimate
- `requires_counsel_review` when legal, regulatory, tax, AML, licensing, cross-border, consumer-protection, or sandbox strategy risk is involved
- `report_use_allowed`

Recommended claim statuses:

- `draft`
- `source_linked`
- `quote_verified`
- `interpretation_reviewed`
- `estimate_reviewed`
- `report_citable`
- `rejected`

Hard gates:

- `confirmed_fact` requires `original_verified=yes` and either `quote_verified` or an official data/statute location.
- `citation_type=direct_quote` requires exact copied wording and an auditable source location.
- `citation_type=paraphrase` requires a source location or source record note showing what was restated.
- `citation_type=inference` requires reasoning notes; it must not be presented as a source fact.
- `Fact` and `confirmed_fact` claims require an auditable location such as page number, article, section, exact URL, capture filename, or table identifier. A source record path alone is not enough for delivery-stage work.
- `summary` requires a preserved original or reputable secondary source and should not add new meaning.
- `interpretation` requires source ids plus reasoning notes.
- `estimate` requires data file ids plus assumption ids and sensitivity or confidence notes.
- `unresolved_issue` must be visibly framed as uncertain.
- `ai_working_summary` cannot support `confirmed_fact`.
- A claim with `report_use_allowed=no` must not appear as a report conclusion.

## Citation Gate

Before a report draft is described as evidence-backed:

1. Every reader-facing citation maps to a source record.
2. Every source record maps to a preserved user-provided original, exact official URL, or explicitly requested capture.
3. Every exact quote includes page, section, paragraph, line, or URL context where available.
4. Every local dataset is described as a reproducibility artifact, not as the external source itself.
5. Every estimate cites both source data and assumptions.
6. Every foreign-language source preserves original text separately from working translation and analysis.
7. The PRD-confirmed output language, citation display language, access-date style, and caption labels match the rendered report.
8. English `Source:`, `Underlying data:`, `Data basis:`, or `Accessed YYYY-MM-DD` labels appear only when the report is explicitly marked as English or mixed-language output.
9. Language guidance has not changed direct quotes, numbers, statute names, proper nouns, approved public wording, source-backed claims, citation locators, or access dates unless the underlying source/claim record was deliberately corrected.
10. Reader-facing reports do not expose `source_id`, `claim_id`, `assumption_id`, or local path metadata.
11. Detailed evidence ledgers are in project registers or appendices, not used as a replacement for footnotes/endnotes.
12. Every chart or quantitative table maps to a local `.csv` or `.xlsx` reproducibility file and, where applicable, assumptions.
13. The report length and depth are proportionate to the PRD and TOC. A short memo may be valid only if labeled as a brief/scaffold; it should not be called a comprehensive or final internal review report.
14. The report earns a higher quality level when it includes original-backed evidence, claim locations, data-backed visuals, reusable template formatting, and verified DOCX/PDF conversion readiness.

## Report Artifact Gate

For substantial HTML reports, run `_ai_system/tools/validate_report_artifact.py --project <project_name>` before delivery.

The artifact gate should fail or warn when:

- internal source/claim IDs appear in visible prose,
- the body contains an internal evidence or claim ledger,
- footnotes/endnotes are missing,
- table or figure sources are missing,
- local `data_sources/` paths are shown as visible source text,
- Appendix sections or final reference lists with accessible links are missing,
- confidential covers lack the reusable confidential tag and sentence-form warning when the report is marked 대외비,
- charts/figures are absent despite market, comparison, timeline, or roadmap content,
- sales-like certainty terms remain in legal/regulatory prose,
- report-specific HTML uses only one-off styling where a reusable workspace report template should be used,
- English caption/access-date labels appear without an explicit English or mixed-language marker,
- a generated DOCX/PDF is described as converted or delivery-ready without structure/render verification.

## Report Stage Labels

Use conservative stage labels.

- `scaffold`: structure exists, evidence may be missing.
- `evidence_mapping_draft`: sources and claims are being mapped.
- `unverified_draft`: report prose exists but research quality gate has not passed.
- `internally_reviewable_draft`: major claims have citable sources, but legal/business review is still required.
- `final_candidate`: content, citations, tone, charts, and assumptions have passed internal QA; still not legal advice.

Do not call a report `final`, `completed`, `fully verified`, or `ready for submission` merely because workspace validation passed.

Maintain the current stage in `project_state/report_stage_manifest.json` when practical. A report should not move beyond `draft_allowed` unless source and claim gates support substantive prose, and should not move to `review_candidate` unless research integrity and report artifact checks pass or residual risks are explicitly recorded.

Stage labels are not self-certifying. If `_ai_system/tools/report_gate_status.py --project <project_name>` reports blockers, the report must be treated as blocked even when the manifest or worklog says `review_candidate`.

## Style Profile Protection Gate

A style profile can make prose more suitable for a reader, but it must not weaken research integrity.

Protected spans must survive tone adjustment unchanged unless the source record, claim register, or legal wording is deliberately corrected and logged:

- exact direct quotes and quoted translations,
- numbers, dates, percentages, formulas, table values, and dataset labels,
- statute names, article/section numbers, regulator names, company names, product names, and other proper nouns,
- source-backed claim wording that depends on a verified quote, page, URL, filing, regulation, dataset, or capture,
- citation locators, access dates, source titles, and reference-list details.

If a style pass changes any protected span, treat it as a research-quality issue until the claim/source record is rechecked. Style profile guidance does not replace quote verification, claim readiness, legal review, citation display checks, or source-register consistency.

## Language Guidance Boundary

Language guidance helps the AI choose reader-appropriate questions, caution levels, display labels, access-date notation, and genre boundaries. It is not automatic translation, automatic humanization, jurisdiction-specific legal review, securities-law review, source verification, or approval review.

When `output_language=en` or `mixed`, keep original source wording and working translations distinct. If an English report cites a Korean, Japanese, Chinese, or other non-English source, preserve the original source title and quoted wording in the source record, and mark translated/paraphrased reader-facing text as translation or paraphrase where material.

## Tone Gate

Regulatory and legal reports should avoid sales-like certainty.

Avoid:

- `완벽히`
- `무력화`
- `완전 분쇄`
- `원천 차단`
- `무조건`
- `최고 수준`
- `압도적`
- `전 세계에 입증`
- `합법성 확보`

Prefer:

- `가능성이 있다`
- `조건부로 검토할 수 있다`
- `추가 확인이 필요하다`
- `규제기관 반론 가능성이 있다`
- `법률 검토가 필요하다`
- `현재 확인 가능한 자료 기준`

## Worklog Reporting Gate

In worklogs and user reports:

- Lead with the current gate, allowed actions, blocked actions, and blockers for report-stage work.
- Say `workspace validation passed` only for folder, launcher, HTML, path, and snapshot checks.
- Say `research integrity checked` only after source-to-claim traceability was checked.
- Say `official source collected` only when an official original, official URL, or official capture exists.
- Say `external source summarized only` or `collection blocked` when no original file, exact URL, or capture was preserved.
- Say `AI working summary created` when the file is a summary or synthesis.
- Separate `passed`, `warning`, `residual risk`, and `not tested`.

## Required Checks Before Major Report Delivery

For a substantial report draft or revision:

1. Run or manually perform source traceability checks.
2. Run or manually perform claim-readiness checks.
3. Run workspace validation separately.
4. Report both results separately.
5. If either check is skipped, state `not tested` and explain why.
6. Run report artifact validation for HTML reports and attach or summarize the result.
7. For substantial internal review reports, run strict gates:
   - `_ai_system/tools/report_preflight.py --project <project_name> --for-delivery --strict-research`
   - `_ai_system/tools/validate_report_artifact.py --project <project_name> --strict-delivery`
   - `_ai_system/tools/validate_research_integrity.py --project <project_name>` for normal report gates; `--check-urls` is an optional live availability probe, not source truth proof.

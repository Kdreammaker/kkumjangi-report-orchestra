# Research and Evidence Rules

## Working Principles

- Separate source evidence from analysis. Exact quotes, paraphrases, and analyst interpretation must never be blended.
- Apply `_ai_system/governance/10_research_quality_gate_rules.md` before a source supports a report claim or reader-facing citation.
- Prefer primary sources first: statutes, regulator releases, official sandbox pages, exchange/company announcements, filings, prospectuses, and court or enforcement materials.
- Use reputable secondary sources only to supplement context, never as the only basis for legal or factual conclusions.
- Record access date for web sources because law, regulatory guidance, and market claims can change.
- For market-size or business-effect estimates, write the calculation logic and assumptions next to the estimate.
- Keep internal strategy hypotheses clearly marked as hypotheses, not confirmed facts.
- Preserve uncertainty. Use labels such as `confirmed`, `likely`, `unclear`, `not verified`, and `requires counsel review`.
- Do not treat sandbox designation as permission to bypass non-waivable rules. In particular, check whether each rule is eligible for regulatory special treatment.
- Do not store secrets, account identifiers, raw personal data, API keys, cookies, unpublished partner materials, or private credentials in this workspace.
- Treat legal analysis as structured business research, not legal advice. Mark items requiring Korean, US, Singapore, China, Hong Kong, or other qualified counsel review.
- Design the evidence trail so every important report sentence can be traced back to a source id, a quote/paraphrase, and an interpretation note.

## Source Reliability Tiers

Assign every source a reliability tier in the source record.

- `Tier 1 - Primary legal/regulatory`: statutes, enforcement decrees, supervisory regulations, official regulator releases, official sandbox decisions, court decisions, enforcement orders, stock-exchange rules, official filing documents, prospectuses, registration statements, and audited disclosures.
- `Tier 2 - Primary commercial/issuer`: company official announcements, official product terms, whitepapers, technical docs, exchange listing pages, custody terms, risk disclosures, and official FAQ pages.
- `Tier 3 - Professional analysis`: Big4, major law firms, regulated financial institutions, recognized research firms, and academic or policy-institute papers.
- `Tier 4 - Reputable news`: major business/legal/financial media. Use for event discovery and timeline support, not as sole support for legal conclusions.
- `Tier 5 - Low-verification context`: blogs, newsletters, community posts, podcasts, social media, forums, and unverified explainers. Use only as lead-generation or market-sentiment context.

Rules:

- Core legal conclusions should rely on Tier 1 sources wherever possible.
- Product-structure conclusions should rely on Tier 1-2 sources wherever possible.
- Market or competitor timeline claims may use Tier 3-4 sources, but important claims need confirmation from Tier 1-2 sources.
- Tier 5 sources must not be cited as dispositive evidence in the internal review report.
- If sources conflict, prefer the higher tier and record the conflict in the active worklog.

## Original and Derivative Boundary

- A preserved original is the user-provided or explicitly approved source file/capture itself, not an AI summary of it.
- AI-written summaries, reconstructed excerpts, working translations, and analyst notes are derivatives. They may help internal work, but they are not original evidence.
- Do not store derivatives under `references/received_originals/` unless they are clearly marked as non-original and excluded from report citation.
- A derivative can support a report only by pointing back to a preserved original or official URL/capture.
- Do not assign `Tier 1` to a derivative merely because it describes a regulator, statute, filing, or official document.
- For external research, the AI must first register the exact official link or source locator before summarizing: file/document name when known, publisher, access date, URL status, quote/location status, and use level. AI file download is not the proof path.
- Do not try to preserve external files by AI download attempts. If an exact official URL is usable, record the link and quote/location status. If a file is genuinely needed, add it to `references/user_requested_materials.md` with the official link and what the user should provide.
- Separate `link confirmed`, `original file/capture preserved`, `quote verified`, and `report_citable`. Do not collapse these into one status.
- Exact quote verification must use a source-specific passage, not a generic portal title, menu label, or homepage text. A short generic phrase such as a law portal banner, regulator name, or document category is not a valid exact quote.
- Source title, publisher, URL host, and quoted passage must describe the same original. For example, do not use a generic law portal URL as proof for a party pledge, company report, press release, or survey merely because the URL is reachable.
- If the needed source is a file, do not invent a capture or describe a failed AI download. Record the item in `references/user_requested_materials.md` with the official link, source name, why it is needed, and what the user should provide.
- Internal strategy decks can be used as evidence of internal thinking, but they do not verify outside facts such as foreign competitor product structure, overseas regulatory approval, market size, or legal status. Those outside facts need separate external source records.
- Overseas benchmark names in a report, TOC, source record, or claim register require source records for the specific overseas case. A Korean or internal document that only mentions a foreign company is a lead, not verified evidence for that foreign company's product, regulatory status, filing, or legal structure.
- Do not add benchmark names to a source title or notes to make an unrelated source pass a citation gate. The source title, original file/URL, exact quote location, and source record must describe the same original source.

## Source Record Format

For every meaningful source, create or update a source record in the relevant `references/` folder. Use Markdown unless a spreadsheet/table is more practical.

Required fields:

- `source_id`: stable short id, for example `kr-fsc-2024-virtual-asset-user-protection`.
- `title`: source title.
- `publisher`: regulator, company, law database, news outlet, or research firm.
- `url_or_path`: source URL or local file path.
- `accessed_at`: date and time in `YYYY-MM-DD HH:mm KST`.
- `jurisdiction`: Korea, US, Singapore, China, Hong Kong, EU, Global, or other.
- `source_type`: statute, regulation, guidance, press release, filing, whitepaper, report, news, blog, data table, screenshot, crawl.
- `relevance`: why this source matters for the project.
- `exact_quote`: short exact quote if needed. Keep quotes concise and preserve original wording.
- `paraphrase`: neutral restatement in our own words.
- `interpretation`: our analysis or inference, clearly labeled.
- `assumptions`: assumptions used for interpretation or estimates.
- `confidence`: high, medium, low.
- `follow_up`: unresolved checks or documents to find.

Recommended quality-gate fields:

- `evidence_class`: for example `original_official`, `original_commercial`, `original_secondary`, `captured_webpage`, `extracted_text`, `working_translation`, `ai_working_summary`, `analysis_note`, or `unknown_origin`.
- `source_readiness_status`: `inventoried`, `original_preserved`, `parsed`, `source_record_draft`, `quote_verified`, `claim_ready`, `report_citable`, or `rejected`.
- `original_verified`: yes/no.
- `original_url`: official live URL when available.
- `local_original_path`: preserved original path when available.
- `capture_path`: local web/PDF/screenshot capture path when available.
- `quote_location`: page, section, paragraph, line, URL anchor, or timestamp where available.

## Quote, Paraphrase, and Interpretation Rules

Use these labels consistently:

- `원문 인용`: exact wording copied from a source.
- `요약`: faithful restatement without adding meaning.
- `해석`: our reasoning based on one or more sources.
- `추정`: a calculated or judgment-based estimate.

Use `citation_type` consistently in claim registers:

- `direct_quote`: the report copies source wording. Use quotation marks or block quotes, keep the quote short, and include page/section/paragraph/URL location.
- `paraphrase`: the report restates source content in our own words. Do not use quotation marks and do not add analysis inside the paraphrase.
- `data_based`: the statement is supported by a dataset, calculation, or local CSV/XLSX reproducibility file. Cite the external source separately from the local data artifact.
- `inference`: the statement is analyst/AI reasoning based on sources. Keep the reasoning chain and limits visible.

Direct quotes and paraphrases are both citations, but they are not the same. Do not make a paraphrase look like the source's exact wording, and do not treat an inference as a source fact.

When writing `해석` or `추정`, add a footnote-style explanation with:

- the source ids used,
- the reasoning chain,
- any limiting assumptions,
- what would change the conclusion.

Example:

```markdown
해석: 이 구조는 국내 투자자 대상 직접 판매보다 해외 투자자 대상 거래 접근으로 설계하는 편이 규제 리스크가 낮을 수 있다.[^rwa-001]

[^rwa-001]: 근거: `source_id_a`는 국내 공모/중개 규제를, `source_id_b`는 해외 tokenized stock 구조를 설명한다. 단, 한국 거주자 접근 차단 방식과 외국환 신고 요건은 별도 법률 검토가 필요하다.
```

## Foreign Language Handling

Foreign-language sources must preserve the original meaning and legal nuance.

- Keep the original source as the authoritative evidence.
- For important passages, record `원문 인용`, `직역`, and `업무상 해석` separately.
- Do not collapse legal terms into loose Korean equivalents. Maintain a glossary for recurring terms.
- Mark ambiguous translations with `translation_risk: yes`.
- For statutes, regulator guidance, offering documents, and product terms, translate close to the source text first and analyze separately.
- Record the source language, translator method, and whether a bilingual human/legal review is needed.
- When a source is machine-translated, label the Korean text as a working translation and do not quote it as if it were official.

Key terms that need consistent handling include:

- project-specific legal, commercial, technical, and market terms that affect interpretation, rights, obligations, eligibility, risk, or investor/customer access.

## Legal Interpretation Boundary

- Distinguish `법령 원문`, `감독당국 설명`, `판례/제재 사례`, `전문가 해설`, and `our interpretation`.
- Use `requires counsel review` when a conclusion affects product launch, licensing, investor eligibility, overseas offering, tax, foreign exchange, AML, consumer protection, or sandbox application strategy.
- Do not say a structure is legally possible unless the required permissions, exemptions, and non-waivable obligations are identified.
- For every candidate structure, identify:
  - applicable laws,
  - special treatment requested through sandbox,
  - obligations that likely remain non-waivable,
  - user protection measures,
  - operational controls,
  - kill-switch or exit plan.

## Citation Standard

- Use stable source ids in internal research records, source indexes, claim registers, assumption registers, data files, and HTML comments.
- Do not expose internal ids such as `[source: kr-fsc-2024-virtual-asset-user-protection]` in rendered report prose.
- Rendered Korean reports should use reader-facing citation marks, such as numbered footnotes/endnotes for body text and `주:`/`자료:` below tables and figures.
- For exact quotes, include page/section/paragraph where available.
- For screenshots or captured webpages, cite both the live URL and local evidence path in the source record or appendix artifact table.
- For estimates, cite the data source ids and the assumption ids in the claim register, data file, or HTML comments; render the source to readers in Korean bibliographic form.
- Do not cite a source that has not been entered into a `source_master_index.md` or project source record.
- Do not cite a source as a confirmed fact unless the original is verified under `_ai_system/governance/10_research_quality_gate_rules.md`.

## Estimate Standard

Every market-size, revenue, cost, or business-effect estimate must include:

- metric definition,
- source data,
- calculation formula,
- assumptions,
- sensitivity range,
- confidence level,
- what evidence would improve confidence.

Use the labels:

- `확정 데이터`: reported or official figure.
- `보정 데이터`: adjusted figure based on stated method.
- `추정`: analyst estimate based on assumptions.
- `시나리오`: low/base/high cases.

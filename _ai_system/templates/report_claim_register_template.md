# Report Claim Register Template

Use this register to prevent unsupported report writing. Every material report claim must be registered before it is used in a report body.

| claim_id | report | section | claim_text_ko | classification | citation_type | source_ids | evidence_paths | data_file_ids | assumption_ids | evidence_class | source_readiness_status | original_verified | exact_quote_location | requires_counsel_review | report_use_allowed | confidence | status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  | confirmed_fact / summary / interpretation / estimate / unresolved_issue | direct_quote / paraphrase / data_based / inference / no_citation |  |  |  |  | original_official / original_commercial / original_secondary / captured_webpage / extracted_text / working_translation / ai_working_summary / analysis_note / unknown_origin | inventoried / original_preserved / parsed / source_record_draft / quote_verified / claim_ready / report_citable / rejected | yes/no |  | yes/no | yes/no | high/medium/low | draft / source_linked / quote_verified / interpretation_reviewed / estimate_reviewed / report_citable / rejected |  |

## Status Rules

- `draft`: possible claim, not yet researched.
- `source_linked`: sources have been found but original verification is incomplete.
- `quote_verified`: exact quote or official location has been checked.
- `interpretation_reviewed`: interpretation has source ids plus reasoning notes.
- `estimate_reviewed`: estimate has source ids, data file ids, assumption ids, and sensitivity/confidence notes.
- `report_citable`: claim may appear in reader-facing report citations.
- `rejected`: claim should not be used; explain why in notes.

## Use Rules

- Only `report_citable` claims may appear as report conclusions.
- Legacy statuses such as `source_backed` or `cited` do not prove original verification.
- `confirmed_fact` requires original verification and quote/page/section/URL location where available.
- `direct_quote` means source wording is copied and requires exact quote text plus page/section/paragraph/URL location.
- `paraphrase` means source content is restated in our words and must not add new meaning.
- `data_based` means a local CSV/XLSX or dataset supports the statement; the local file is a reproducibility artifact, not the external source itself.
- `inference` means AI/analyst reasoning based on sources; keep the reasoning and limits visible.
- AI-created summaries or translations cannot support `confirmed_fact` unless they point back to a verified original.
- `interpretation` and `estimate` claims must cite both sources and reasoning/assumptions.
- `unresolved_issue` claims may appear in risk or open-question sections if the uncertainty is explicit.

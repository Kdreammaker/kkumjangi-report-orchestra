# Document Preset Codemap

Use this codemap to route document-type work without opening every preset
folder. The compact machine-readable source is `INDEX.json`.

| Preset | Purpose | Default mode | Read first |
|---|---|---|---|
| `general_report` | Evidence-backed business, policy, research, or strategy-style report. | `substantial` | `general_report/preset.json`; `general_report/prd_questions.md` |
| `business_strategy` | Decision memo or internal review for executives and operating teams. | `substantial` | `business_strategy/preset.json`; `business_strategy/prd_questions.md` |
| `regulatory_review` | Legal, policy, compliance, or approval-path review. | `substantial` | `regulatory_review/preset.json`; `regulatory_review/prd_questions.md` |
| `academic_research` | Literature-heavy synthesis with methods, citations, and limitations. | `substantial` | `academic_research/preset.json`; `academic_research/prd_questions.md` |
| `technical_design` | Architecture, API, data model, security, testing, and operations design. | `standard` | `technical_design/preset.json`; `technical_design/prd_questions.md` |
| `service_planning` | User, UX flow, operating policy, KPI, and rollout planning. | `standard` | `service_planning/preset.json`; `service_planning/prd_questions.md` |
| `product_prd` | Product requirements, acceptance criteria, rollout, and product decisions. | `standard` | `product_prd/preset.json`; `product_prd/prd_questions.md` |
| `investor_brief` | Document-style investor brief, IR explanatory material, factbook, or investor Q&A brief; not an IR deck. | `standard` | `investor_brief/preset.json`; `investor_brief/prd_questions.md` |
| `equity_research` | Sector or company analysis centered on performance, valuation assumptions, catalysts, risks, and non-advisory limits. | `substantial` | `equity_research/preset.json`; `equity_research/prd_questions.md` |
| `business_proposal` | Partner-facing or customer-facing business proposal with scope, value, execution plan, terms, and next decision. | `standard` | `business_proposal/preset.json`; `business_proposal/prd_questions.md` |
| `product_manual` | Product manual or user guide covering procedures, installation, configuration, FAQ, troubleshooting, and version notes. | `standard` | `product_manual/preset.json`; `product_manual/prd_questions.md` |
| `education_curriculum` | Curriculum, lesson material, instructor notes, learner handouts, activities, assignments, and assessment design. | `standard` | `education_curriculum/preset.json`; `education_curriculum/prd_questions.md` |
| `academic_paper` | Paper-style academic document with abstract, research questions, methodology, literature review, limitations, and references. | `substantial` | `academic_paper/preset.json`; `academic_paper/prd_questions.md` |
| `press_release` | Short-form external public release flow: brief PRD, fact/approval check, draft writing, and public-risk review; not a substantial report. | `brief` | `press_release/preset.json`; `press_release/prd_questions.md` |

## Hold Candidates

These requests are recognized in `INDEX.json`, but are intentionally not active
document presets. Treat them as hold or follow-up-module candidates rather than
routing them into the report factory by analogy.

| Candidate | Aliases | Reason |
|---|---|---|
| `quotation` | 견적, 견적서 | Pricing, tax, validity, and line-item arithmetic need a separate commercial document data model. |
| `newsletter` | 뉴스레터 | Email cadence, CTA, audience segmentation, and send-format constraints do not fit the substantial report flow. |
| `resume_career_profile` | 이력서, 경력기술서, 이력서/경력기술서 | Career profile writing needs a lighter privacy-first profile module rather than the full report factory. |

## Stage Overlay Rule

After selecting a preset, read only the current stage overlay:

- PRD or interview work: `prd_questions.md`
- Workflow mode, TOC, workpack, visual/data, or stage compression work: `stage_overlays.md`
- Layout/design pattern work for extension presets: `design_patterns.md`
- Closeout or quality review: `validation_checklist.md`

These modules are source-of-truth guidance. `stage_overlays.md` can change
the shape of the workflow, such as replacing report chapters with lesson
sections, task blocks, proposal sections, factbook sections, or public-release
blocks. It does not automate writing quality, source truth, legal review,
approval, or delivery readiness. Future tooling may generate a separate
derived index, but the generated index must not replace these files.

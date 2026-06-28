# Academic Paper Design Patterns

## Document Purpose And Reader

- Purpose: Produce a paper-style academic document, seminar paper, journal-style article, thesis chapter, or working paper.
- Primary readers: academic reviewers, faculty, researchers, students, policy researchers, or technical reviewers.
- The document should foreground research question, method, evidence, contribution, limitations, and references.

## Recommended Document Structure

- Title and metadata: title, author/status if needed, version, date, discipline, and citation style.
- Abstract: research question, method, evidence base, main finding, and limitation in concise form.
- Introduction: research problem, contribution, scope, and paper roadmap.
- Literature review: grouped by themes, schools, methods, or debates.
- Methodology: data, sample, procedure, analytical approach, validity constraints, and ethics if relevant.
- Findings/analysis: evidence, interpretation, tables/figures, and alternative explanations.
- Discussion and limitations: contribution, boundary of claims, limitations, and future research.
- References: style-consistent bibliography and any appendix or data notes.

## Recommended Layout Blocks

- Abstract block before the main body.
- Methodology box or section with data, method, sample, and limits.
- Numbered tables and figures with captions.
- Limitations section that is visible before the conclusion or inside discussion.
- Reference list with consistent style and line wrapping.

## Design Application Priorities

- Use the abstract to summarize research question, methodology, evidence base, result, and limitation without adding claims that the body cannot support.
- Use methodology tables when variables, sample, period, instruments, coding scheme, or procedure need side-by-side comparison.
- Use data note blocks when dataset limits, access dates, missingness, ethical constraints, or source-status boundaries affect interpretation.
- Use results sections for findings and discussion sections for interpretation, implications, alternative explanations, and limitations.
- Use appendix sections for instruments, extended tables, coding details, robustness checks, or long evidence extracts that would interrupt the main argument.
- Keep references, DOI strings, URLs, long titles, and dense table cells wrapping within semantic paragraphs or table cells; do not solve academic layout by broad forced character breaking.

## Tables, Figures, And Captions

- Table captions should appear with table number, title, source, and note where relevant.
- Figure captions should explain the analytical point, not only name the figure.
- Evidence tables should separate source facts, coded categories, and author interpretation.
- References and citations must not be replaced by generic source mentions.

## AI Judgment Needed

- Decide whether the paper structure should emphasize abstract/methodology/results/discussion/references, or a discipline-specific variation.
- Decide whether a method detail belongs in prose, methodology table, data note, footnote-style note, or appendix.
- Decide whether a result is source fact, coded category, statistical output, author interpretation, or inference.
- Decide whether long references, DOI/URL strings, and evidence tables should be split, shortened in display text, or moved to appendix detail while preserving citation integrity.

## Deferred Export-Native Features

- Do not claim Word-native field codes, SEQ captions, generated DOCX captions, PAGE/NUMPAGES fields, or native bibliography management.
- Do not claim automatic landscape sections for method tables, evidence matrices, or appendix tables.
- Treat citation-manager integration, native caption numbering, and journal-template automation as separate work outside this module.

## Word/DOCX Compatibility

- Keep evidence tables, coding matrices, and method tables within Word page width; split dense tables by construct, sample, period, or theme.
- Long titles, citations, reference URLs, table cells, and notes must wrap cleanly.
- Use static figures with captions, source notes, and alternative descriptions.
- Limit fixed-width fonts to short code, formulas, transcript excerpts, or syntax-sensitive snippets; do not use fixed-width styling for full paragraphs or broad tables.
- Avoid interactive HTML, viewport-dependent layouts, and complex absolute positioning.
- DOCX/PDF conversion still requires separate export validation; this pattern does not guarantee conversion success.

## Patterns To Avoid

- Business-report recommendation structure unless the academic genre requires it.
- Literature summaries with no synthesis or contribution.
- Method claims that exceed available data.
- Missing limitations or references.
- Fixed-width typography across body text.

## Reviewer Checkpoints

- Are abstract, methodology, references, table/figure captions, and limitations visible?
- Is the research question tied to method and evidence?
- Are citation style and reference list consistent?
- Do tables and figures distinguish source fact from analysis?
- Is the document export-safe without broad fixed-width layouts?
- Are long references, DOI/URL strings, and dense method or evidence tables handled without broad forced character-breaking layout rules?

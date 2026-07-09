# Book Manuscript Design Patterns

## Document Purpose And Reader

- Purpose: Create or adapt a book-like manuscript for novels, nonfiction, professional books, textbooks, workbooks, essays, or long-form publication material.
- Primary readers: author, editor, publisher, internal reviewer, educator, professional reader, or beta reader.
- The document should preserve authorial voice and source/provenance while making manuscript structure and export format consistent.

## Recommended Document Structure

- Title/metadata page: title, subtitle, author/editor, manuscript type, version, status, date, and rights/confidentiality note.
- Front matter: preface, introduction, notes to reader, table of contents, acknowledgments, or usage notes when needed.
- Body matter: parts, chapters, scenes, lessons, sections, examples, exercises, figures, tables, and sidebars.
- Back matter: notes, references, bibliography, glossary, appendices, answer key, author bio, and revision log when needed.
- For novels: parts, chapters, scene breaks, point-of-view notes only when editorially required, and continuity/canon notes outside reader prose.
- For professional books: chapter objectives, examples, diagrams/tables, key takeaways, citations, caveats, and exercises when useful.

## Recommended Layout Blocks

- Manuscript title page with plain metadata rather than promotional cover design.
- Part/chapter openers with stable hierarchy and clear page-break intent.
- Scene breaks or section dividers that survive Word import without decorative CSS reliance.
- Sidebars or callouts for notes, examples, warnings, exercises, or editor notes.
- References, notes, glossary, and appendix tables with inline borders and captions.

## Design Application Priorities

- Preserve voice, prose, dialogue, names, canon, citations, and approved terminology unless the user explicitly asks for editorial rewriting.
- Use `formal_outline` for structured professional/book outlines and `symbol_bullets` for compact support lists.
- Keep book hierarchy distinct from report hierarchy; do not force executive-summary/report recommendation blocks into manuscripts.
- Make editorial notes, producer/editor notes, and reader-facing prose visually distinct.
- Use static images and simple tables for export-oriented manuscripts.
- Keep publishing-native features as deferred unless implemented in the target export path.

## Tables, Figures, And Captions

- Tables and figures should support the manuscript, not turn it into a slide/report hybrid.
- Captions should remain close to the figure/table and include source/copyright status when relevant.
- Exercises and worksheets should avoid complex layout that collapses in Word import.
- Reference tables should distinguish source title, author/publisher, date, URL/DOI, and usage status where applicable.

## AI Judgment Needed

- Decide whether the task is formatting-only, light editorial cleanup, structure repair, copyedit, line edit, substantive rewrite, or new drafting.
- Decide whether material belongs in reader-facing prose, editor note, producer note, footnote/endnote, appendix, glossary, or revision log.
- Decide whether a book section should keep literary/prose rhythm even when it looks less "report-like."
- Decide whether the selected export path should be Word-import HTML, native DOCX, PDF proof, or another artifact.

## Deferred Export-Native Features

- Do not claim print-ready typesetting, ebook packaging, imposition, automatic index, running heads, cross-references, generated captions, or Word style template automation.
- Do not claim publisher-specific Chicago/APA/MLA compliance unless a separate style-sheet review is performed.
- Treat final cover design, ISBN/barcode, rights metadata packaging, and ebook conversion as separate work.

## Word/DOCX Compatibility

- Use inline-first HTML for Word import targets and keep page background white.
- Prefer normal paragraphs, semantic headings, simple lists, static images, and simple tables.
- Avoid decorative drop caps, complex floats, CSS counters as the only numbering source, viewport-dependent layout, and background-heavy effects.
- Use native DOCX export when chapter/list hierarchy fidelity matters.
- Export validation is required before claiming delivery readiness.

## Patterns To Avoid

- Rewriting literary prose when the request was format cleanup.
- Treating all books as business reports with recommendations and decision memos.
- Hiding editorial/producer notes inside reader prose.
- Claiming final publishing readiness from HTML or DOCX existence alone.

## Reviewer Checkpoints

- Is the manuscript type and editorial depth clear?
- Are original prose, dialogue, protected spans, citations, and terminology preserved as required?
- Is the book hierarchy stable across front matter, body matter, and back matter?
- Are lists, notes, figures, tables, and sidebars export-friendly?
- Are publishing-native features clearly deferred unless separately verified?

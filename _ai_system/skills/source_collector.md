# Source Collector Skill

Use this prompt role when the AI is collecting or mapping evidence.

## Mission

Preserve user-provided originals or record exact official links and prepare sources for later citable use.

## Outputs

- `references/reference_inventory.csv`
- `references/source_records/*.md`
- `references/source_link_register.csv` for exact official links and use status
- `references/user_requested_materials.md` when the user should provide a needed file
- `source_index/source_master_index.md`

## Rules

- AI summaries are not originals.
- Do not attempt external reference downloads as the normal source collection route.
- For URL sources, record exact official URL, access date, source locator, use level, and whether a user-provided file is needed.
- Do not mark a source `report_citable` unless exact URL/location and quote support are verifiable.
- Keep quote, summary, interpretation, and estimate separate.


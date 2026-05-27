# Report Factory Context

Use `_ai_system/tools/compose_report_context.py` before a stage-specific AI run.

Examples:

```powershell
python _ai_system/tools/compose_report_context.py --project my_project --stage architect
python _ai_system/tools/compose_report_context.py --project my_project --stage interview
python _ai_system/tools/compose_report_context.py --project my_project --stage chapter --chapter ch03 --write-packet
python _ai_system/tools/compose_report_context.py --project my_project --stage chart --chapter ch03
python _ai_system/tools/compose_report_context.py --project my_project --stage assemble
```

The output is a compact manifest of files the AI should read for that stage. This keeps context smaller and makes chapter writing richer without asking the AI to reread the whole workspace.

With `--write-packet`, the tool also writes `context_packets/*.compact.md` and `context_packets/*.files.compact.tsv`. These are AI input packets, not evidence originals. They keep the first read bounded while preserving the original source records, claim register, and reference inventory for verification.

Use `interview` for a short decision interview. `/grill-me` is only a shortcut; ordinary requests such as "ask me a few questions first" should use the same stage. Use `chart` when the AI is building concrete tables, graphs, diagrams, or chart data files rather than only planning visual intent.

# Changelog

## 1.1.2 - 2026-07-20

- Corrected current HWP/HWPX guidance: the owned engine is embedded in every distributed package and needs no separate repository or external CLI configuration.
- Clarified that Report Orchestra cover/chapter sources are automatically adapted through `report_export_ir.v1` by `export_report_hwpx.py`; users do not need to rewrite system-authored reports into the low-level HTML contract.
- Limited the `arbitrary_html_supported: false` explanation to direct low-level conversion of arbitrary external web HTML. The controlled `hwpx-authoring-html.v1` boundary remains an input-safety and deterministic-conversion contract, not a restriction on normal Report Factory export.
- This release corrects documentation and public release metadata; engine behavior remains unchanged. Native Hancom visual identity still requires a separate open/render check.

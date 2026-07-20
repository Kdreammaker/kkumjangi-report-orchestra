# Changelog

## 1.1.0 - 2026-07-20

- Clarified that the private owned HWP/HWPX engine and native Report Factory HWPX exporter are not distributed in the public seed.
- Removed public commands that would otherwise imply the private embedded engine is available; native DOCX and ordinary report workflows are unchanged.
- Kept public package validation channel-aware so the intentional absence of the private engine is treated as a valid public boundary, not a broken installation.

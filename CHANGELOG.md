# Changelog

## 1.0.4 - 2026-06-28

- Changed report design guidance, report HTML templates, chapter fragments, and reusable cover rendering to an inline-first authoring policy for DOCX/Google Docs compatibility-minded import tests.
- Added shared inline style helpers for generated cover metadata, approval blocks, reference appendices, and data appendices so core typography, color, border, and spacing are not class-only.
- Kept CSS as browser preview, print, and fallback support for page rules, print behavior, font fallback, and long-token handling rather than treating CSS as the only source of report styling.
- Tightened export/report-factory guidance around class-only/CSS-variable-only styling, grid/flex-only cover metadata, `nth-child`, `@font-face`-only typography, and background-heavy effects.
- Fixed non-confidential cover/report validation handling so `대외비 아님` is not treated as a confidential signal.
- Compatibility remains export-verification-first; this release does not claim full DOCX or Google Docs rendering parity.

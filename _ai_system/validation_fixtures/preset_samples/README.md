# Preset Artifact Sample Fixtures

This folder contains validation-only sample report artifacts for document preset
checks. The samples are not active business projects and do not contain real
project, market, issuer, customer, or personal data.

Each preset fixture is shaped like a small project folder so the report artifact
validators can inspect the same `reports/` and `data_sources/` structure used by
ordinary report workspaces.

## Samples

| Preset | Sample HTML | Status |
|---|---|---|
| `investor_brief` | `investor_brief/reports/investor_brief_fixture.html` | validation fixture only |
| `press_release` | `press_release/reports/press_release_fixture.html` | validation fixture only |
| `equity_research` | `equity_research/reports/equity_research_fixture.html` | validation fixture only |
| `business_proposal` | `business_proposal/reports/business_proposal_fixture.html` | validation fixture only |
| `product_manual` | `product_manual/reports/product_manual_fixture.html` | validation fixture only |

English language-layer fixtures also live inside the existing preset folders:

| Preset | English Sample HTML | Status |
|---|---|---|
| `business_proposal` | `business_proposal/reports/business_proposal_fixture_en.html` | validation fixture only |
| `press_release` | `press_release/reports/press_release_fixture_en.html` | validation fixture only |
| `investor_brief` | `investor_brief/reports/investor_brief_fixture_en.html` | validation fixture only |
| `equity_research` | `equity_research/reports/equity_research_fixture_en.html` | validation fixture only |

## Fixture Rules

- All names, metrics, quote text, contacts, issuer labels, and data values are
  synthetic fixture values.
- Reader-facing source captions name the fixture basis instead of exposing local
  paths.
- Hidden HTML comments may include `data_sources/*.csv` references so strict
  artifact validation can confirm backing files without leaking local paths to
  the reading copy.
- English fixtures must declare `<html lang="en">` or an explicit
  `output_language` marker before using `Source:`, `Underlying data:`,
  `Data basis:`, or `Accessed YYYY-MM-DD`.
- English fixtures are a language layer over existing presets, not separate
  English-only presets. They must not imply automatic translation, automatic
  rewrite, or jurisdiction-specific legal/securities disclaimer generation.
- DOCX/PDF export is not guaranteed by these samples. Export validation must be
  run separately when a converter is available.
- Passing these fixtures proves only validator and preset-structure coverage. It
  does not prove real report quality, source truth, legal suitability, product
  readiness, investment suitability, or customer delivery readiness.

# Changelog

## 1.0.7 - 2026-07-19

- Added `_ai_system/tools/convert_hwp_to_hwpx.py` as a thin local caller for the separately distributed project-owned Python/rule engine; conversion rules are not copied into Report Orchestra.
- Added a release smoke for engine discovery, bounded invocation, public-safe failures, and HWPX output creation.
- Updated export and adaptation rules so configured HWP-to-HWPX conversion is supported while arbitrary HTML-to-native-HWPX remains out of scope.
- Preserved target-specific DOCX-compatible and HWPX-compatible HTML authoring rules instead of treating them as one interchangeable profile.
- Preserved local-first, no-cloud-upload-by-default guidance and public issue privacy warnings.

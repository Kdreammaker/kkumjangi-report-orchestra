# Changelog

## 1.0.8 - 2026-07-19

- Added `_ai_system/tools/convert_html_hwpx.py` as a thin bidirectional caller for the shared owned engine's `hwpx-authoring-html.v1` contract; conversion rules remain outside Report Orchestra.
- Added a release smoke for engine discovery, bounded invocation, local outputs, public-safe failures, both conversion directions, and false-by-default visual claims.
- Updated export, adaptation, install, and runtime guidance: controlled authoring HTML can create native HWPX when the companion engine is configured, while ordinary/arbitrary HTML remains unsupported and Chromium preview parity remains unverified.

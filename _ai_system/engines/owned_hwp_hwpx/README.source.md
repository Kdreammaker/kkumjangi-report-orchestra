# Owned HWP/HWPX Engine

This directory contains the Python standard-library HWP reader, neutral model,
and deterministic HWPX writer used to replace the conversion-time HWP OSS
runtime after the integration and release gates pass.

## Stable Python API

```python
from owned_hwp_hwpx import convert_hwp_to_hwpx

receipt = convert_hwp_to_hwpx(
    "source.hwp",
    "output.hwpx",
    compatibility_profile="hancom",
    manifest_path="conversion.json",
)
```

The same package exposes a controlled HWPX authoring HTML contract:

```python
from owned_hwp_hwpx import (
    convert_authoring_html_to_hwpx,
    convert_hwpx_to_authoring_html,
)

convert_hwpx_to_authoring_html("source.hwpx", "source.html")
convert_authoring_html_to_hwpx("source.html", "output.hwpx")
```

Only `hwpx-authoring-html.v1` is accepted. This is an inline-first,
resource-contained authoring format with explicit HWPX metadata; it is not an
arbitrary HTML importer and is intentionally separate from DOCX-compatible
HTML.

The receipt and optional JSON manifest contain no local paths, filenames, raw
document text, binary payloads, or exception details. Production callers must
choose `hancom` or `portable`; the paired-corpus `oracle` mode is not available
through this API.

## CLI

```text
python scripts/convert_owned_hwp_to_hwpx.py SOURCE.hwp OUTPUT.hwpx \
  --profile hancom --manifest conversion.json
python scripts/convert_owned_html_hwpx.py hwpx-to-html SOURCE.hwpx TARGET.html
python scripts/convert_owned_html_hwpx.py html-to-hwpx SOURCE.html TARGET.hwpx
```

The CLI writes one JSON object to standard output and returns stable nonzero
exit codes for invalid input, missing input, output conflicts, conversion
failure, and generated-package validation failure.

## Current Boundary

The writer validates 16 package/model components before committing output,
including native-reader package graph, inline controls, HwpUnitChar case and
default branches, paragraph break flags, line segments, structural controls,
tables, objects, binary payload digests, and normalized paragraph content. The
renderer-facing HWP-to-HWPX rule gate passes across all 51 paired files. The
controlled HTML/HWPX path passes semantic, deterministic package, native
package, and actual Local Bridge CLI checks for all 61 corpus documents. All
61 regenerated files open without a damage dialog in Hancom Viewer; 57 pass
the strict visual threshold, 60 preserve page count, and 899 pages were
compared. Four residual rendering cases and Chromium authoring HTML remain
explicit fidelity gaps, so visual equivalence is not claimed by default.
Playwright, PyMuPDF, NumPy, and Pillow are used only for validation evidence;
the production conversion path remains the owned Python/rule engine.

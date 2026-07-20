# Embedded Owned HWP/HWPX Engine

This directory is the Report Orchestra-owned runtime for HWP/HWPX conversion.
It is part of the system core and must work without another repository,
environment-variable engine paths, or an external conversion service.

Supported production operations are:

- HWP 5.x to deterministic native HWPX,
- native HWPX to `hwpx-authoring-html.v1`,
- `hwpx-authoring-html.v1` to deterministic native HWPX.

The production conversion path uses the Python standard library. Rendering and
visual-comparison dependencies are validation-only and are not imported by the
ordinary conversion commands.

`IMPORT_PROVENANCE.json` records the one-time validated source snapshot. After
that import, this engine has an independent Report Orchestra lifecycle. Do not
add an automatic dependency or synchronization path back to the source
repository.

Ordinary report HTML and DOCX-oriented HTML are not accepted as controlled
authoring HTML. Report Factory exports must map their source structure through
the Report Export IR and owned Document IR instead of relabeling arbitrary
HTML.

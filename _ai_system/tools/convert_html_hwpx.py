"""Convert controlled authoring HTML and HWPX through the embedded engine."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ENGINE_ROOT = Path(__file__).resolve().parents[1] / "engines" / "owned_hwp_hwpx"
sys.path.insert(0, str(ENGINE_ROOT))

from owned_hwp_hwpx import (  # noqa: E402
    ENGINE_ID,
    ENGINE_VERSION,
    OwnedAuthoringHtmlError,
    OwnedHwpxReadError,
    convert_authoring_html_to_hwpx,
    convert_hwpx_to_authoring_html,
)


DIRECTIONS = {
    "html-to-hwpx": (".html", ".hwpx"),
    "hwpx-to-html": (".hwpx", ".html"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert the controlled HWPX authoring HTML contract and native HWPX."
    )
    parser.add_argument("direction", nargs="?", choices=tuple(DIRECTIONS))
    parser.add_argument("source", nargs="?")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--probe", action="store_true")
    return parser.parse_args()


def safe_payload(status: str, code: str, **extra: object) -> dict[str, object]:
    return {
        "schema_version": "report_orchestra_owned_html_hwpx_embedded.v1",
        "status": status,
        "code": code,
        "local_absolute_paths_included": False,
        "raw_source_text_included": False,
        **extra,
    }


def main() -> int:
    args = parse_args()
    if args.probe:
        print(
            json.dumps(
                safe_payload(
                    "available",
                    "ok",
                    engine_id=ENGINE_ID,
                    engine_version=ENGINE_VERSION,
                    runtime_dependency_mode="embedded_system_core",
                    authoring_html_contract="hwpx-authoring-html.v1",
                )
            )
        )
        return 0

    direction = str(args.direction or "")
    contract = DIRECTIONS.get(direction)
    source = Path(args.source or "")
    output = Path(args.output or "")
    if contract is None:
        print(json.dumps(safe_payload("blocked", "html_hwpx_direction_required")))
        return 2
    if source.suffix.lower() != contract[0] or not source.is_file():
        print(json.dumps(safe_payload("blocked", "html_hwpx_source_required")))
        return 2
    if output.suffix.lower() != contract[1]:
        print(json.dumps(safe_payload("blocked", "html_hwpx_output_extension_invalid")))
        return 2
    if output.exists() and not args.overwrite:
        print(json.dumps(safe_payload("blocked", "html_hwpx_output_exists")))
        return 2

    try:
        if direction == "hwpx-to-html":
            result = convert_hwpx_to_authoring_html(source, output)
        else:
            result = convert_authoring_html_to_hwpx(source, output)
    except (OwnedAuthoringHtmlError, OwnedHwpxReadError) as exc:
        print(json.dumps(safe_payload("failed", str(exc))))
        return 5
    except (OSError, ValueError, TypeError):
        print(json.dumps(safe_payload("failed", "owned_html_hwpx_conversion_failed")))
        return 5

    if result.get("status") != "converted" or not output.is_file():
        print(json.dumps(safe_payload("failed", str(result.get("reason") or "owned_html_hwpx_conversion_failed"))))
        return 5
    print(
        json.dumps(
            safe_payload(
                "converted",
                "ok",
                direction=direction,
                engine_id=ENGINE_ID,
                engine_version=ENGINE_VERSION,
                source_format=str(result.get("source_format") or contract[0][1:]),
                target_format=str(result.get("target_format") or contract[1][1:]),
                output_bytes=output.stat().st_size,
                native_package_contract_status=result.get("native_package_contract_status"),
                external_resource_fetch_required=False,
                visual_equivalence_claimed=False,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

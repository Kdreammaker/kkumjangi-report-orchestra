"""Convert HWP to HWPX through the embedded Report Orchestra engine."""

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
    OwnedHwpConversionError,
    convert_hwp_to_hwpx,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HWP to HWPX through the embedded owned engine."
    )
    parser.add_argument("source", nargs="?", help="Source .hwp file")
    parser.add_argument("output", nargs="?", help="Destination .hwpx file")
    parser.add_argument("--profile", choices=("hancom", "portable"), default="hancom")
    parser.add_argument("--manifest", help="Optional path for the engine result manifest")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--probe", action="store_true", help="Report embedded engine availability and version")
    return parser.parse_args()


def safe_payload(status: str, code: str, **extra: object) -> dict[str, object]:
    return {
        "schema_version": "report_orchestra_owned_hwp_hwpx_embedded.v1",
        "status": status,
        "code": code,
        "local_absolute_paths_included": False,
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
                )
            )
        )
        return 0

    source = Path(args.source or "")
    output = Path(args.output or "")
    manifest = Path(args.manifest) if args.manifest else None
    try:
        result = convert_hwp_to_hwpx(
            source,
            output,
            compatibility_profile=args.profile,
            overwrite=args.overwrite,
            manifest_path=manifest,
        )
    except OwnedHwpConversionError as exc:
        print(json.dumps(safe_payload("failed", exc.code)))
        return exc.exit_code
    except Exception:
        print(json.dumps(safe_payload("failed", "owned_hwp_hwpx_conversion_failed")))
        return 5

    engine = result.get("engine") if isinstance(result.get("engine"), dict) else {}
    print(
        json.dumps(
            safe_payload(
                "converted",
                "ok",
                engine_id=str(engine.get("id") or ENGINE_ID),
                engine_version=str(engine.get("version") or ENGINE_VERSION),
                compatibility_profile=args.profile,
                output_bytes=output.stat().st_size,
                validation_status=result.get("validation_status", "pass"),
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

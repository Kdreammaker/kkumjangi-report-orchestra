"""Invoke the separately distributed owned authoring HTML/HWPX engine CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ENGINE_ENV = "OWNED_HTML_HWPX_CLI"
MAX_TIMEOUT_SECONDS = 300
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
    parser.add_argument("--engine-cli", help=f"Owned engine CLI path; defaults to {ENGINE_ENV}")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (1-300)")
    parser.add_argument("--probe", action="store_true")
    return parser.parse_args()


def safe_payload(status: str, code: str, **extra: object) -> dict[str, object]:
    return {
        "schema_version": "report_orchestra_owned_html_hwpx_bridge.v1",
        "status": status,
        "code": code,
        "local_absolute_paths_included": False,
        "raw_source_text_included": False,
        **extra,
    }


def resolve_engine_cli(value: str | None) -> Path | None:
    candidate = str(value or os.environ.get(ENGINE_ENV, "")).strip()
    if not candidate:
        return None
    path = Path(candidate).expanduser().resolve()
    return path if path.is_file() and path.suffix.lower() == ".py" else None


def invoke_engine(engine_cli: Path, args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(engine_cli), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(1, min(timeout, MAX_TIMEOUT_SECONDS)),
        shell=False,
    )


def parse_engine_payload(stdout: str) -> dict[str, object]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    args = parse_args()
    engine_cli = resolve_engine_cli(args.engine_cli)
    if engine_cli is None:
        print(json.dumps(safe_payload("blocked", "owned_html_hwpx_engine_not_configured")))
        return 2

    if args.probe:
        try:
            completed = invoke_engine(engine_cli, ["--version"], args.timeout)
        except (OSError, subprocess.TimeoutExpired):
            print(json.dumps(safe_payload("failed", "owned_html_hwpx_engine_probe_failed")))
            return 3
        version = completed.stdout.strip() if completed.returncode == 0 else ""
        ok = bool(version)
        print(json.dumps(safe_payload("available" if ok else "failed", "ok" if ok else "owned_html_hwpx_engine_probe_failed", engine_version=version)))
        return 0 if ok else 3

    direction = str(args.direction or "")
    source = Path(args.source or "")
    output = Path(args.output or "")
    contract = DIRECTIONS.get(direction)
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
        completed = invoke_engine(
            engine_cli,
            [direction, str(source.resolve()), str(output.resolve())],
            args.timeout,
        )
    except subprocess.TimeoutExpired:
        print(json.dumps(safe_payload("failed", "owned_html_hwpx_conversion_timeout")))
        return 3
    except OSError:
        print(json.dumps(safe_payload("failed", "owned_html_hwpx_engine_start_failed")))
        return 3

    payload = parse_engine_payload(completed.stdout)
    if completed.returncode != 0 or payload.get("status") != "converted":
        print(json.dumps(safe_payload("failed", str(payload.get("reason") or "owned_html_hwpx_conversion_failed"))))
        return completed.returncode or 3
    if not output.is_file() or output.stat().st_size == 0:
        print(json.dumps(safe_payload("failed", "html_hwpx_output_missing")))
        return 3

    print(
        json.dumps(
            safe_payload(
                "converted",
                "ok",
                direction=direction,
                engine_id="owned_html_hwpx_python",
                engine_version=str(payload.get("engine_version") or "0.2.0"),
                source_format=str(payload.get("source_format") or contract[0][1:]),
                target_format=str(payload.get("target_format") or contract[1][1:]),
                output_bytes=output.stat().st_size,
                native_package_contract_status=payload.get("native_package_contract_status"),
                external_resource_fetch_required=False,
                visual_equivalence_claimed=False,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

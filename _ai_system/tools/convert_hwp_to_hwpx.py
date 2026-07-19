"""Invoke the separately distributed owned HWP-to-HWPX engine CLI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ENGINE_ENV = "OWNED_HWP_HWPX_CLI"
MAX_TIMEOUT_SECONDS = 300


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert HWP to HWPX through the shared owned engine CLI."
    )
    parser.add_argument("source", nargs="?", help="Source .hwp file")
    parser.add_argument("output", nargs="?", help="Destination .hwpx file")
    parser.add_argument("--engine-cli", help=f"Owned engine CLI path; defaults to {ENGINE_ENV}")
    parser.add_argument("--profile", choices=("hancom", "portable"), default="hancom")
    parser.add_argument("--manifest", help="Optional path for the engine result manifest")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (1-300)")
    parser.add_argument("--probe", action="store_true", help="Report engine availability and version")
    return parser.parse_args()


def safe_payload(status: str, code: str, **extra: object) -> dict[str, object]:
    return {
        "schema_version": "report_orchestra_owned_hwp_hwpx_bridge.v1",
        "status": status,
        "code": code,
        "local_absolute_paths_included": False,
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
        print(json.dumps(safe_payload("blocked", "owned_hwp_hwpx_engine_not_configured")))
        return 2

    if args.probe:
        try:
            completed = invoke_engine(engine_cli, ["--version"], args.timeout)
        except (OSError, subprocess.TimeoutExpired):
            print(json.dumps(safe_payload("failed", "owned_hwp_hwpx_engine_probe_failed")))
            return 3
        version = completed.stdout.strip() if completed.returncode == 0 else ""
        ok = bool(version)
        print(json.dumps(safe_payload("available" if ok else "failed", "ok" if ok else "owned_hwp_hwpx_engine_probe_failed", engine_version=version)))
        return 0 if ok else 3

    source = Path(args.source or "")
    output = Path(args.output or "")
    if source.suffix.lower() != ".hwp" or not source.is_file():
        print(json.dumps(safe_payload("blocked", "hwp_source_required")))
        return 2
    if output.suffix.lower() != ".hwpx":
        print(json.dumps(safe_payload("blocked", "hwpx_output_required")))
        return 2

    command = [str(source.resolve()), str(output.resolve()), "--profile", args.profile]
    if args.manifest:
        command.extend(("--manifest", str(Path(args.manifest).resolve())))
    if args.overwrite:
        command.append("--overwrite")
    try:
        completed = invoke_engine(engine_cli, command, args.timeout)
    except subprocess.TimeoutExpired:
        print(json.dumps(safe_payload("failed", "owned_hwp_hwpx_conversion_timeout")))
        return 3
    except OSError:
        print(json.dumps(safe_payload("failed", "owned_hwp_hwpx_engine_start_failed")))
        return 3

    payload = parse_engine_payload(completed.stdout)
    if completed.returncode != 0 or payload.get("status") != "converted":
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        code = str(error.get("code") or "owned_hwp_hwpx_conversion_failed")
        print(json.dumps(safe_payload("failed", code)))
        return completed.returncode or 3
    if not output.is_file() or output.stat().st_size == 0:
        print(json.dumps(safe_payload("failed", "hwpx_output_missing")))
        return 3

    engine = payload.get("engine") if isinstance(payload.get("engine"), dict) else {}
    print(
        json.dumps(
            safe_payload(
                "converted",
                "ok",
                engine_id=str(engine.get("id") or "owned_hwp_hwpx_python"),
                engine_version=str(engine.get("version") or "unknown"),
                compatibility_profile=args.profile,
                output_bytes=output.stat().st_size,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

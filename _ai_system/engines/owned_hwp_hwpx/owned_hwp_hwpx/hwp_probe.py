"""Minimal owned HWP container probe.

The first replacement step is intentionally conservative: verify the HWP
container shape without extracting raw document text or private metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


HWP_CFB_MAGIC = bytes.fromhex("d0 cf 11 e0 a1 b1 1a e1")


def _size_bucket(size_bytes: int) -> str:
    if size_bytes < 16 * 1024:
        return "lt_16kb"
    if size_bytes < 128 * 1024:
        return "lt_128kb"
    if size_bytes < 1024 * 1024:
        return "lt_1mb"
    if size_bytes < 10 * 1024 * 1024:
        return "lt_10mb"
    return "gte_10mb"


def probe_hwp_file(path: Path) -> dict[str, Any]:
    """Return a path-free container probe for a candidate HWP file."""

    try:
        stat = path.stat()
    except FileNotFoundError:
        return {
            "status": "missing",
            "is_ole_cfb": False,
            "size_bucket": "missing",
            "size_bytes": 0,
        }

    with path.open("rb") as handle:
        magic = handle.read(len(HWP_CFB_MAGIC))

    is_ole_cfb = magic == HWP_CFB_MAGIC
    return {
        "status": "probe_ok" if is_ole_cfb else "not_ole_cfb",
        "is_ole_cfb": is_ole_cfb,
        "size_bucket": _size_bucket(stat.st_size),
        "size_bytes": stat.st_size,
        "magic_probe": "ole_cfb_v1" if is_ole_cfb else "unknown",
    }

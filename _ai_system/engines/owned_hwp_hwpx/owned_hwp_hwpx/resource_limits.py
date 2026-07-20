"""Resource limits shared by the owned HWP/HWPX engine."""

from __future__ import annotations

from pathlib import Path
import zlib


MAX_SOURCE_BYTES = 256 * 1024 * 1024
MAX_DECOMPRESSED_STREAM_BYTES = 64 * 1024 * 1024


class ResourceLimitError(ValueError):
    """Raised when an input exceeds a bounded parser resource limit."""


def read_file_bounded(path: Path, *, max_bytes: int = MAX_SOURCE_BYTES) -> bytes:
    """Read one input only after enforcing a stable byte ceiling."""

    if path.stat().st_size > max_bytes:
        raise ResourceLimitError("source_size_limit_exceeded")
    with path.open("rb") as handle:
        payload = handle.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise ResourceLimitError("source_size_limit_exceeded")
    return payload


def decompress_bounded(
    payload: bytes,
    wbits: int,
    *,
    max_output_bytes: int = MAX_DECOMPRESSED_STREAM_BYTES,
) -> bytes:
    """Decompress one stream without allowing expansion past the ceiling."""

    decoder = zlib.decompressobj(wbits)
    output = decoder.decompress(payload, max_output_bytes + 1)
    if len(output) > max_output_bytes or decoder.unconsumed_tail:
        raise ResourceLimitError("decompressed_stream_limit_exceeded")
    output += decoder.flush()
    if len(output) > max_output_bytes:
        raise ResourceLimitError("decompressed_stream_limit_exceeded")
    return output

from __future__ import annotations

import re
from pathlib import Path


REQUIRED_WORKPACK_MARKERS = [
    "Reader Decision",
    "Reader Takeaway",
    "Core Question",
    "Required Answer Boundary",
    "Paragraph Plan",
    "Evidence Inputs",
    "Claim Register Links",
    "Counterarguments",
    "Required Visuals",
    "Forbidden Claims",
    "Completion Checklist",
]

WEAK_WORKPACK_PATTERNS = [
    r"-\s*chapter_id:\s*$",
    r"\|\s*\|\s*\|\s*\|",
    r"\|\s*1\s*\|\s*\|\s*\|\s*\|",
]


def workpack_quality_issues(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    issues: list[str] = []
    if len(text.strip()) < 900:
        issues.append("too short to guide rich chapter writing")
    missing = [marker for marker in REQUIRED_WORKPACK_MARKERS if marker.lower() not in text.lower()]
    if missing:
        issues.append("missing required workpack sections: " + ", ".join(missing[:6]))
    for pattern in WEAK_WORKPACK_PATTERNS:
        if re.search(pattern, text, flags=re.I | re.M):
            issues.append("contains unfilled template placeholders")
            break
    return issues

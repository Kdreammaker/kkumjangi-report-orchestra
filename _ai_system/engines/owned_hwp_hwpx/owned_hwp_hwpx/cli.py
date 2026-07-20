"""Command line interface for owned HWP/HWPX baseline tools."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .corpus import build_corpus_baseline
from .dry_run import build_dry_run_writer_report
from .rule_mining import build_rule_mining_report


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Owned HWP/HWPX baseline tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    corpus = subparsers.add_parser(
        "corpus-baseline",
        help="Build a public-safe exact-pair HWP/HWPX corpus baseline.",
    )
    corpus.add_argument("--pairs-root", required=True, help="Directory containing exact HWP/HWPX pairs.")
    corpus.add_argument("--output", help="Optional JSON output path.")
    corpus.add_argument("--limit", type=int, help="Optional maximum number of pairs to profile.")
    corpus.add_argument(
        "--recursive",
        action="store_true",
        help="Search for pairs recursively under the root.",
    )

    rules = subparsers.add_parser(
        "rule-mining",
        help="Mine public-safe structural HWP-to-HWPX rules from exact pairs.",
    )
    rules.add_argument("--pairs-root", required=True, help="Directory containing exact HWP/HWPX pairs.")
    rules.add_argument("--output", help="Optional JSON output path.")
    rules.add_argument("--limit", type=int, help="Optional maximum number of pairs to profile.")
    rules.add_argument(
        "--recursive",
        action="store_true",
        help="Search for pairs recursively under the root.",
    )

    dry_run = subparsers.add_parser(
        "dry-run-writer",
        help="Generate HWPX dry-run packages and structural snapshots from exact pairs.",
    )
    dry_run.add_argument("--pairs-root", required=True, help="Directory containing exact HWP/HWPX pairs.")
    dry_run.add_argument("--output-root", required=True, help="Output root for generated packages and snapshots.")
    dry_run.add_argument("--output", help="Optional JSON report path.")
    dry_run.add_argument("--limit", type=int, help="Optional maximum number of pairs to process.")
    dry_run.add_argument("--snapshot-limit", type=int, help="Optional maximum number of pairs to snapshot.")
    dry_run.add_argument(
        "--include-text",
        action="store_true",
        help="Carry owned HWP paragraph text into generated HWPX and compare text coverage.",
    )
    dry_run.add_argument(
        "--compatibility-profile",
        choices=("portable", "hancom", "oracle"),
        default="portable",
        help="Column-control profile; oracle is evaluation-only and follows paired HWPX producer metadata.",
    )
    dry_run.add_argument(
        "--recursive",
        action="store_true",
        help="Search for pairs recursively under the root.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "corpus-baseline":
        payload = build_corpus_baseline(
            Path(args.pairs_root),
            recursive=bool(args.recursive),
            limit=args.limit,
        )
        if args.output:
            _write_json(Path(args.output), payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.command == "rule-mining":
        payload = build_rule_mining_report(
            Path(args.pairs_root),
            recursive=bool(args.recursive),
            limit=args.limit,
        )
        if args.output:
            _write_json(Path(args.output), payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.command == "dry-run-writer":
        payload = build_dry_run_writer_report(
            Path(args.pairs_root),
            Path(args.output_root),
            recursive=bool(args.recursive),
            limit=args.limit,
            snapshot_limit=args.snapshot_limit,
            include_text=bool(args.include_text),
            compatibility_profile=args.compatibility_profile,
        )
        if args.output:
            _write_json(Path(args.output), payload)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

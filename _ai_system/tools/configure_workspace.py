from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from workspace_config import DEFAULT_CONFIG, _deep_merge, resolved_domain_profile, validate_config_schema


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    return workspace_root() / "_ai_system" / "workspace_config.json"


def load_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("workspace config must be a JSON object")
    return _deep_merge(DEFAULT_CONFIG, data)


def write_config_file(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def available_domains(config: dict[str, Any]) -> list[str]:
    presets = config.get("domain_presets", {})
    if not isinstance(presets, dict):
        return []
    return sorted(str(key) for key in presets.keys())


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Safely inspect or change workspace_config.json. "
            "This is a configuration wrapper, not a report-quality judge."
        )
    )
    parser.add_argument("--config", default=str(default_config_path()), help="Path to workspace_config.json.")
    parser.add_argument("--list-domains", action="store_true", help="List available preset_domain values.")
    parser.add_argument("--show", action="store_true", help="Print the resolved active domain profile.")
    parser.add_argument("--domain", help="Set preset_domain to an existing domain preset.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the proposed change without writing.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    try:
        config = load_config_file(config_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "config": str(config_path)}, ensure_ascii=False, indent=2))
        return 1

    domains = available_domains(config)
    if args.list_domains:
        print(json.dumps({"config": str(config_path), "domains": domains}, ensure_ascii=False, indent=2))
        return 0

    changed = False
    before_domain = str(config.get("preset_domain") or "general_report")
    if args.domain:
        requested = args.domain.strip()
        if requested not in domains:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "error": f"unknown preset_domain: {requested}",
                        "available_domains": domains,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
        config["preset_domain"] = requested
        changed = requested != before_domain

    errors = validate_config_schema(config)
    if errors:
        print(
            json.dumps(
                {
                    "status": "error",
                    "config": str(config_path),
                    "errors": errors,
                    "proposed_domain": config.get("preset_domain"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    payload: dict[str, Any] = {
        "status": "ok",
        "config": str(config_path),
        "dry_run": bool(args.dry_run),
        "changed": changed,
        "before_domain": before_domain,
        "active_profile": resolved_domain_profile(config),
        "notes": [
            "This tool changes workspace configuration only.",
            "It does not validate report content, source truth, or writing quality.",
        ],
    }

    if args.domain and not args.dry_run:
        write_config_file(config_path, config)
        payload["written"] = True
    elif args.domain:
        payload["written"] = False

    if args.show or args.domain or not (args.list_domains or args.show):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())


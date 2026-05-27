from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workspace_config import css_variable_block, load_config, resolved_domain_profile, validate_config_schema


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Resolve the active workspace domain preset.")
    parser.add_argument("--css", action="store_true", help="Print the CSS variable block for the active preset.")
    parser.add_argument(
        "--write-css",
        default="",
        help="Optional workspace-relative path where the resolved CSS variable block should be written.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    config = load_config(root)
    errors = validate_config_schema(config)

    if args.css:
        print(css_variable_block(config))
    else:
        print(
            json.dumps(
                {
                    "profile": resolved_domain_profile(config),
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    if args.write_css:
        output = root / args.write_css
        try:
            output.resolve().relative_to(root.resolve())
        except ValueError:
            print(json.dumps({"error": "write target must stay inside the workspace"}, ensure_ascii=False, indent=2))
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(css_variable_block(config) + "\n", encoding="utf-8", newline="\n")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

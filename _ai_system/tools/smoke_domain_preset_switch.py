from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from workspace_config import active_quality_profile, active_theme_tokens, css_variable_block, load_config, resolved_domain_profile


CONFIG = Path("_ai_system") / "workspace_config.local.json"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *command],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    original = CONFIG.read_text(encoding="utf-8") if CONFIG.exists() else None
    try:
        CONFIG.write_text(
            json.dumps({"preset_domain": "business_strategy"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        config = load_config()
        profile = resolved_domain_profile(config)
        quality = active_quality_profile(config)
        tokens = active_theme_tokens(config)
        css = css_variable_block(config)
        validation = run(["_ai_system/tools/validate_workspace_setup.py", "--skip-api"])
        passed = (
            profile.get("preset_domain") == "business_strategy"
            and int(quality.get("minimum_visuals", 0)) == 5
            and tokens.get("primary") == "#0B63CE"
            and "preset_domain: business_strategy" in css
            and validation.returncode == 0
        )
        print(
            json.dumps(
                {
                    "passed": passed,
                    "profile": profile,
                    "validation_exit_code": validation.returncode,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if passed else 1
    finally:
        if original is None:
            CONFIG.unlink(missing_ok=True)
        else:
            CONFIG.write_text(original, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())

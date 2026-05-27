from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path


REQUIREMENTS = Path("_ai_system") / "environment" / "requirements.txt"
VALIDATOR = Path("_ai_system") / "tools" / "validate_local_runtime.py"
RUNTIME = Path("_ai_system") / "runtime"

RUNTIME_ASSETS = {
    "echarts": [
        (
            "vendor/echarts/echarts.min.js",
            "https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js",
        ),
    ],
    "pretendard": [
        (
            "fonts/pretendard/Pretendard-Regular.woff2",
            "https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/woff2/Pretendard-Regular.woff2",
        ),
        (
            "fonts/pretendard/Pretendard-SemiBold.woff2",
            "https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/woff2/Pretendard-SemiBold.woff2",
        ),
        (
            "fonts/pretendard/Pretendard-Bold.woff2",
            "https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/woff2/Pretendard-Bold.woff2",
        ),
    ],
}


def run(args: list[str]) -> int:
    completed = subprocess.run(args, check=False)
    return completed.returncode


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 0:
        return
    with urllib.request.urlopen(url, timeout=30) as response:
        target.write_bytes(response.read())


def write_pretendard_css() -> None:
    css_path = RUNTIME / "fonts" / "pretendard" / "pretendard.css"
    css_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.write_text(
        """@font-face{font-family:Pretendard;src:url('Pretendard-Regular.woff2') format('woff2');font-weight:400;font-style:normal;font-display:swap;}
@font-face{font-family:Pretendard;src:url('Pretendard-SemiBold.woff2') format('woff2');font-weight:600;font-style:normal;font-display:swap;}
@font-face{font-family:Pretendard;src:url('Pretendard-Bold.woff2') format('woff2');font-weight:700;font-style:normal;font-display:swap;}
""",
        encoding="utf-8",
    )


def install_runtime_assets() -> int:
    try:
        for group in RUNTIME_ASSETS.values():
            for rel_path, url in group:
                download(url, RUNTIME / rel_path)
        write_pretendard_css()
        notices = RUNTIME / "THIRD_PARTY_RUNTIME_ASSETS.txt"
        notices.write_text(
            "Apache ECharts 5.5.1: Apache License 2.0, https://github.com/apache/echarts\n"
            "Pretendard 1.3.9: SIL Open Font License 1.1, https://github.com/orioncactus/pretendard\n",
            encoding="utf-8",
        )
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"runtime_asset_install_failed {type(exc).__name__}: {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Install and validate local runtime dependencies.")
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Only run the local runtime validator without installing packages.",
    )
    parser.add_argument(
        "--skip-assets",
        action="store_true",
        help="Skip downloading ECharts and Pretendard local runtime assets.",
    )
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        print(f"python_too_old version={sys.version.split()[0]} minimum=3.11")
        return 1
    if not REQUIREMENTS.exists():
        print(f"missing_requirements path={REQUIREMENTS.as_posix()}")
        return 1

    if not args.skip_install:
        code = run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        if code != 0:
            print(f"dependency_install_failed code={code}")
            return code
    if not args.skip_assets:
        code = install_runtime_assets()
        if code != 0:
            return code

    return run([sys.executable, str(VALIDATOR)])


if __name__ == "__main__":
    raise SystemExit(main())

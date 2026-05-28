from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


USER_WORKSPACE = Path("00_사용자_작업공간")
STANDARD_USER_DIRS = [
    USER_WORKSPACE,
]


README_TEXT = """# 사용자 작업공간

이 폴더는 사용자의 실제 프로젝트, 자료, 보고서 산출물이 들어가는 공간입니다.

처음에는 비어 있어도 정상입니다. 새 프로젝트는 AI에게 주제와 목적을 알려주고 세팅안을 먼저 받은 뒤 생성하세요.

중요:

- 이 폴더의 자료와 보고서는 system-core GitHub 패키지에 포함하지 않습니다.
- 외부 자료는 프로젝트의 `01_자료_넣는_곳/`에 넣고 AI에게 인테이크를 요청합니다.
- 작업환경 검증 통과는 보고서 내용 검증 통과가 아닙니다.
"""


def bootstrap(force: bool = False) -> dict[str, object]:
    created: list[str] = []
    skipped: list[str] = []

    for path in STANDARD_USER_DIRS:
        if path.exists():
            skipped.append(path.as_posix())
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(path.as_posix())

    readme = USER_WORKSPACE / "README.md"
    if readme.exists() and not force:
        skipped.append(readme.as_posix())
    else:
        readme.parent.mkdir(parents=True, exist_ok=True)
        readme.write_text(README_TEXT, encoding="utf-8")
        created.append(readme.as_posix())

    return {
        "ok": True,
        "created": created,
        "skipped_existing": skipped,
        "next_steps": [
            "Open START_HERE.html",
            "Run python _ai_system/tools/validate_workspace_setup.py --include-user-flow",
            "Ask the AI to propose a full setup brief before creating a new project",
        ],
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Bootstrap the user workspace folder for a fresh system-core install.")
    parser.add_argument("--force-readme", action="store_true", help="Overwrite 00_사용자_작업공간/README.md.")
    args = parser.parse_args()
    print(json.dumps(bootstrap(force=args.force_readme), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

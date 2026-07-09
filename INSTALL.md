# Install

이 문서는 설치를 맡은 AI 또는 사용자가 참고하는 세부 절차입니다.

일반 사용자는 저장소 링크와 함께 아래 문구만 AI에게 주면 됩니다.

```text
https://github.com/Kdreammaker/kkumjangi-report-orchestra 의 INSTALL.md를 보고 설치 및 세팅해 주세요.
```

GitHub 저장소는 시스템 코어를 받는 곳입니다. 실제 프로젝트 파일, 보고서, 참고자료, CSV/XLSX, 검증 산출물은 설치된 로컬 폴더의 `00_사용자_작업공간/` 아래에 만들어집니다.

## 1. 저장소 받기

```powershell
git clone https://github.com/Kdreammaker/kkumjangi-report-orchestra.git
cd kkumjangi-report-orchestra
```

Git을 쓰지 않으면 GitHub에서 ZIP을 내려받아 압축을 풉니다.

설치 폴더는 사용자가 계속 접근할 수 있는 로컬 드라이브 위치를 권장합니다. 임시 폴더나 AI 앱 내부 artifact 폴더에 설치하면 결과물을 찾기 어렵습니다.

## 2. Python과 로컬 런타임 준비

먼저 Python 3.11 이상이 있는지 확인합니다.

```powershell
python --version
python -m pip --version
```

Python이 없거나 3.11보다 낮으면 설치 AI는 Python 3.11 이상 설치를 먼저 안내해야 합니다. Python 설치가 확인되기 전에는 작업공간 검증을 완료했다고 말하지 않습니다.

로컬 문서 처리와 색인에 필요한 패키지와 런타임 asset을 설치하고 검증합니다.

```powershell
python _ai_system/tools/install_runtime_dependencies.py
```

이 단계는 `pypdf`, `docling`, `duckdb`, `python-docx`를 설치/검증하고, Apache ECharts와 Pretendard를 `_ai_system/runtime/` 아래 로컬 asset으로 내려받아 검증합니다.

주의: Docling은 OCR/문서구조 인식 관련 의존성을 함께 설치하므로 첫 설치 때 시간이 걸리고 디스크 용량을 더 사용할 수 있습니다. ECharts와 Pretendard는 최초 설치 때 인터넷 다운로드가 필요할 수 있습니다. 설치 후에는 상시 실행되는 프로그램이 아니라 참고자료 인테이크, 색인, DOCX export, 보고서 렌더링 때 로컬에서 쓰는 도구입니다.

## 3. 사용자 작업공간 만들기

```powershell
python _ai_system/tools/bootstrap_workspace.py
```

이미 `00_사용자_작업공간/`이 있으면 덮어쓰지 않습니다.

## 4. 설치 검증

```powershell
python _ai_system/tools/validate_workspace_setup.py --include-user-flow
```

통과하면 폴더 구조, Python, 로컬 런타임, 사용자용 HTML 흐름이 준비된 것입니다. 이 검증은 보고서 내용, 법률 해석, 출처 진위, 인용 정확성을 검증하지 않습니다.

설치 완료 보고에는 다음만 짧게 포함하세요.

- 설치 위치
- `00_사용자_작업공간/` 생성 또는 기존 유지 여부
- 로컬 검증기 실행 결과
- 저장소/channel
- Python과 필수 패키지 상태
- 로컬 구성 고지: Python 패키지와 ECharts/Pretendard 로컬 asset은 사용자 PC 안에서 참고자료 정리, 로컬 색인, 차트 렌더링, 한글 표시를 돕는 용도이며 상시 백그라운드로 실행되지 않음
- 인프라/구조 검증은 통과했지만 문서 내용, 출처 진위, 법률 해석, 인용 정확성 검증은 아직 아니라는 설명
- 설치된 시스템 버전과 배포일

설치 완료 채팅의 마지막에는 아래 블록을 별도 제목으로 출력하세요.

```text
다음 단계

1. 시스템 사용방법은 설치 폴더의 START_HERE.html에 정리되어 있습니다.
   START_HERE.html 경로: [설치 폴더]\START_HERE.html

2. 설치 직후에는 같은 환경 점검 프롬프트를 다시 보낼 필요가 없습니다.

3. 바로 시작하려면 AI에게 이렇게 요청하세요.
   새 프로젝트를 시작해 주세요.
   주제: [작성하고 싶은 문서 주제]
   한 줄 목적: [왜 작성하는지]
```

## 5. 시작

`START_HERE.html`을 열고 사용합니다.

새 프로젝트나 설치/재점검은 AI가 `AGENTS.md`로 라우팅하고, 이미 만들어진 프로젝트의 보고서 작업은 프로젝트 폴더의 `tasks/current_task.md`를 먼저 읽고 진행합니다.

## 6. 오픈소스 고지

설치 과정에서 준비되는 주요 구성요소는 다음과 같습니다.

| 구성요소 | 역할 | 라이선스 |
|---|---|---|
| pypdf | PDF 텍스트/메타데이터 처리 | BSD-style |
| Docling | 로컬 문서 변환과 구조 추출 | MIT |
| DuckDB | 로컬 프로젝트 색인 | MIT |
| python-docx | native DOCX export 패키지 생성 | MIT |
| Apache ECharts | 로컬 차트 렌더링 | Apache License 2.0 |
| Pretendard | 한글 UI/보고서 폰트 | SIL Open Font License 1.1 |

자세한 고지는 `docs/THIRD_PARTY_NOTICES.md`를 확인하세요. 기본 설정에서는 사용자 원본 파일을 외부 서버로 업로드하지 않습니다. 외부 OCR, 외부 이미지 해석, 클라우드 업로드는 별도 사용자 승인 없이는 사용하지 않습니다.

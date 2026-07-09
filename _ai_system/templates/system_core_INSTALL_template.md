# Install

이 문서는 설치를 맡은 AI 또는 사용자가 참고하는 세부 절차입니다.

## 1. 저장소 받기

```powershell
git clone https://github.com/Kdreammaker/kkumjangi-report-orchestra.git
cd kkumjangi-report-orchestra
```

Git을 쓰지 않으면 GitHub에서 ZIP을 내려받아 압축을 풉니다.

## 2. Python과 로컬 런타임 준비

Python 3.11 이상이 있는지 확인한 뒤 로컬 문서 처리와 보고서 렌더링에 필요한 구성요소를 설치/검증합니다.

```powershell
python _ai_system/tools/install_runtime_dependencies.py
```

이 단계는 `pypdf`, `docling`, `duckdb`, `python-docx`, Apache ECharts, Pretendard를 준비합니다.

## 3. 사용자 작업공간 만들기

```powershell
python _ai_system/tools/bootstrap_workspace.py
```

## 4. 설치 검증

```powershell
python _ai_system/tools/validate_workspace_setup.py --include-user-flow
```

이 검증은 설치와 실행 환경 검증입니다. 문서 내용, 법률 해석, 출처 진위, 인용 정확성을 검증하지 않습니다.

## 5. 설치 완료 후 안내

설치 완료 보고는 설치 위치, 작업공간 생성 여부, 검증 결과, 저장소/channel, Python/필수 패키지 상태, 시스템 버전만 짧게 요약하세요. 또한 아래 로컬 구성 고지문과 `다음 단계` 블록을 채팅 마지막에 별도 제목으로 출력하세요. 문서 유형 목록, 샘플 주제, style profile, 내부 workflow 설명은 설치 완료 채팅에 길게 쓰지 않습니다.

```text
로컬 구성 고지: Python 패키지(pypdf, docling, duckdb, python-docx)와 로컬 asset(Apache ECharts, Pretendard)을 설치/검증했습니다. 이 구성은 사용자 PC 안에서 참고자료 정리, 로컬 색인, DOCX export, 차트 렌더링, 한글 표시를 돕는 용도이며 상시 백그라운드로 실행되지 않습니다. 오픈소스 라이선스와 고지는 docs/THIRD_PARTY_NOTICES.md에서 확인할 수 있습니다.
```

```text
다음 단계

1. 사용 방법은 START_HERE.html에 정리되어 있습니다.
   START_HERE.html 경로: [설치 폴더]\START_HERE.html

2. 설치 직후에는 같은 환경 점검을 다시 요청할 필요가 없습니다.

3. 바로 시작하려면 AI에게 이렇게 요청하세요.
   새 프로젝트를 시작해 주세요.
   주제: [작성하고 싶은 문서 주제]
   한 줄 목적: [왜 작성하는지]
```

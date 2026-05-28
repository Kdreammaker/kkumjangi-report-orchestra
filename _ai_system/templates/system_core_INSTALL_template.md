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

이 단계는 `pypdf`, `docling`, `duckdb`, Apache ECharts, Pretendard를 준비합니다.

## 3. 사용자 작업공간 만들기

```powershell
python _ai_system/tools/bootstrap_workspace.py
```

## 4. 설치 검증

```powershell
python _ai_system/tools/validate_workspace_setup.py --include-user-flow
```

이 검증은 설치와 실행 환경 검증입니다. 보고서 내용, 법률 해석, 출처 진위, 인용 정확성을 검증하지 않습니다.

## 5. 설치 완료 후 안내

설치 완료 채팅의 마지막에는 아래 블록을 별도 제목으로 출력하세요.

```text
다음 단계

1. 시스템 사용방법은 설치 폴더의 START_HERE.html에 정리되어 있습니다.
   START_HERE.html 경로: [설치 폴더]\START_HERE.html
   가능하면 이 파일을 기본 브라우저로 열어 주세요.

2. 설치가 끝났다면 START_HERE.html을 먼저 확인해 주세요.

3. 설치 직후에는 같은 환경 점검 프롬프트를 다시 보낼 필요가 없습니다.

4. 이 시스템에 특히 적합한 문서 유형은 시장조사, 기업 비교분석, 전략 보고서, 정책/규제 검토, 서비스 기획/PRD, 기술 도입 검토입니다.

5. 바로 시작하려면 AI에게 이렇게 요청하세요.
   새 프로젝트를 시작해 주세요.
   주제: [작성하고 싶은 보고서 주제]
   한 줄 목적: [왜 작성하는지]
```

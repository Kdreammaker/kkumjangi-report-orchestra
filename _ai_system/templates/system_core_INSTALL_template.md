# Install

이 문서는 설치를 맡은 AI 또는 사용자가 참고하는 세부 절차입니다.

## 1. 저장소 받기

```powershell
git clone https://github.com/Kdreammaker/kkumjangi-report-orchestra.git
cd kkumjangi-report-orchestra
```

Git을 쓰지 않으면 GitHub에서 ZIP을 내려받아 압축을 풉니다.

## 2. 사용자 작업공간 만들기

```powershell
python _ai_system/tools/bootstrap_workspace.py
```

## 3. 설치 검증

```powershell
python _ai_system/tools/validate_workspace_setup.py --include-user-flow
```

이 검증은 보고서 내용, 법률 해석, 출처 진위, 인용 정확성을 검증하지 않습니다.

## 4. 시작

`START_HERE.html`을 열고 사용합니다.

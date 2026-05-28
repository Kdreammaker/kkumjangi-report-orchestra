# Report Integrity Orchestrator

AI가 고품질 보고서를 안정적으로 작성하도록 돕는 로컬 보고서 생산 시스템입니다.

## 설치

저장소 링크를 받은 뒤 AI에게 이렇게만 요청하면 됩니다.

```text
[Kdreammaker/kkumjangi-report-orchestra](https://github.com/Kdreammaker/kkumjangi-report-orchestra) 보고 설치 및 세팅해 주세요.
```

AI가 세부 절차가 필요하면 `INSTALL.md`와 `AGENTS.md`를 읽고 진행합니다.

## 설치 후 사용

설치가 끝나면 `START_HERE.html`을 열어 사용법을 봅니다.

## 무엇을 하는 시스템인가요?

큰 보고서를 바로 쓰지 않고 다음 생산라인으로 진행합니다.

`PRD -> 상세 목차 -> 주요 골조 -> 챕터 작업팩 -> 챕터 HTML -> 시각자료/CSV -> Chapter 0 -> 조립 -> 검수/교차검증 -> 승인된 고도화/재조립 -> 검증`

핵심 목표는 검증기 통과가 아니라, AI가 더 좋은 내용을 쓰도록 작업을 작게 나누고 필요한 근거만 주입하는 것입니다.

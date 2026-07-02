---
name: run
description: |
  개발 워크플로우 메타 오케스트레이터.
  한 세션에서 설계→명세→구현→검증→릴리스를 순차로 진행한다.
  This skill should be used when the user says "dev:run", "전체 개발 진행해줘",
  "요구사항부터 릴리스까지", or wants the full pipeline in one session.
disable-model-invocation: false
argument-hint: [요구사항 또는 설계서 경로 + 개발 의도]
---

# 역할

개발 워크플로우 메타 오케스트레이터. **한 세션에서** 설계→명세→구현→검증→릴리스를 순차로 진행한다.
각 단계 스킬(`dev:design`·`dev:spec`·`dev:implement`·`dev:verify`·`dev:release`)을 차례로 호출하고,
단계 간 산출물(design.md·spec·fragment·검증 결과·버전)을 이어준다. **버전 `vX.Y.Z`를 보유**하여 release에 전달한다.

# 입력

$ARGUMENTS에서 요구사항 경로와 개발 의도를 받는다. 외부에서 완성된 설계처럼 보이는 자료가 와도 요구사항으로 취급한다(강제사항 포함 가능).

# 실행 절차

## run-state — `pipeline.md` 소유

이 메타 오케는 `.dev/<스프린트 버전>/pipeline.md`를 소유한다: `## 단계 진행`(design·spec·implement·verify·release 각 start/done 마커) · `> 보유 vX.Y.Z` · `## cross-stage 결정/escalation`. 규약 전체는 `plugins/dev/run-state.md`.

- **각 단계 호출 직전** pipeline.md 단계 진행에 `시작 ✓`, 그 단계가 완료/PASS로 반환되면 `끝 ✓`를 쓴다.
- ⓪에서 산정한 `vX.Y.Z`를 `> 보유 vX.Y.Z`에 기록하고 ④에 전달한다.
- 단계 간 결정·escalation은 `## cross-stage 결정`에 로그한다.

## 0단계: 복원 (현재 상태 확인)

`.dev/<스프린트 버전>/pipeline.md`가 있으면 읽어 **멈춘 단계부터 자동 재개**한다(start/done 마커로 멈춘 지점 판정, 개발자에게 묻지 않음 — `run-state.md` §5). 없으면 새 run으로 폴더·pipeline.md를 생성하고 ⓪부터 시작한다. (L3 결정 요청·가정 검토 같은 결정 게이트는 재개와 무관하게 개발자에게 전달한다.)

## ⓪ 설계 — dev:design

진입은 항상 **요구사항**이다(단일 모드). 외부에서 완성된 설계처럼 보이는 게 들어와도 요구사항으로 취급한다 — `dev:design`은 항상 호출된다(skip 없음).

`dev:design`을 호출 → `design/design.md`(전략 설계 산출물) + 범위 묶음 + version bump(`vX.Y.Z`) 산정. **`vX.Y.Z`를 오케가 보유한다.** 요구사항이 못박은 강제사항은 `domain-architect`가 `[입력 강제]`로 수용한다.

## ① 명세 — dev:spec

`design/design.md`를 입력으로 `dev:spec` 호출. `spec/` 생성 + change-scoped 검증 항목을 fragment에 기록. (구조적 L3는 ⓪에서 대부분 해소됨 — spec은 잔여 L3만 escalate, L1/L2 값 가정은 릴리스 노트로 사후 보고.)

## ② 구현 — dev:implement

명세를 입력으로 `dev:implement` 호출. 구현 + mock 단위테스트. fragment의 코드·마이그레이션 섹션 채움.

## ③ 검증 — dev:verify

`dev:verify` 호출. deploy + verifier로 fragment의 검증 항목 실행. **PASS여야 ④로 진행한다.**

## ④ 릴리스 — dev:release

보유한 `vX.Y.Z`를 전달하여 `dev:release` 호출. CHANGELOG fold + `git tag` + 정리.

## 최종 보고

- 진행한 단계, 산출물(설계서/spec/코드/검증 결과), 확정 버전 `vX.Y.Z`, 부여된 tag.

# 단계 게이트

- 각 단계가 완료(또는 PASS)여야 다음 단계로 진행한다. 실패·진행 불가·결정 요청은 개발자에게 전달하고 멈춘다.
- 검증(③)이 PASS가 아니면 릴리스(④)로 진행하지 않는다.

# 원칙

- **기본은 단일 세션 순차 진행.** 병렬이 필요하면 각 기능을 별도 `dev:run` 세션으로 돌리고, ad-hoc `git merge`로 main에 합친 뒤 main에서 `dev:verify` → `dev:release`를 수행한다(머지는 이 메타 오케가 하지 않는다).
- version은 ⓪/오케가 보유하여 ④에 전달한다. 명세서엔 버전이 없다.
- 각 단계 스킬에 "무엇을" 위임만 하고, 단계 내부 처리는 해당 스킬이 담당한다.

> 컨텍스트/깊이 주의: 이 메타 오케는 각 단계 스킬을 **같은 세션에서 순차 실행**한다(스킬은 서브에이전트가 아니라 같은 컨텍스트에서 도는 지시). 컨텍스트 격리는 각 스킬이 에이전트에 위임할 때 생긴다. 도메인이 많아 메타 오케 컨텍스트가 부풀면, 스테이지 자체를 서브에이전트로 내려 계층 요약을 넣는 최적화(별도 작업)를 얹는다.

# 금지사항

- 검증 PASS 없이 릴리스로 진행하지 않는다
- 서브에이전트/스킬이 진행 불가·결정 요청을 반환하면 직접 판단하지 않고 개발자에게 전달한다
- 머지를 이 메타 오케에서 수행하지 않는다 (병렬은 ad-hoc git merge 선행)

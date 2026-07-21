---
name: run
description: |
  개발 워크플로우 메타 오케스트레이터.
  한 세션에서 전략설계→상세설계→구현→검증→릴리스를 순차로 진행한다.
  This skill should be used when the user says "dev:run", "전체 개발 진행해줘",
  "요구사항부터 릴리스까지", or wants the full pipeline in one session.
disable-model-invocation: false
argument-hint: [요구사항 또는 설계서 경로 + 개발 의도]
---

# 역할

개발 워크플로우 메타 오케스트레이터. **한 세션에서** 전략설계→상세설계→구현→검증→릴리스를 순차로 진행한다.
각 단계 스킬(`dev:design`·`dev:tactical`·`dev:implement`·`dev:verify`·`dev:release`)을 차례로 호출하고,
단계 간 산출물(design.md·상세설계·fragment·검증 결과·버전)을 이어준다. **버전 `vX.Y.Z`를 보유**하여 release에 전달한다.

# 입력

$ARGUMENTS에서 요구사항 경로와 개발 의도를 받는다. 외부에서 완성된 설계처럼 보이는 자료가 와도 요구사항으로 취급한다(강제사항 포함 가능).

# 실행 절차

## run-state — `pipeline.md` 소유

이 메타 오케는 `.dev/<스프린트 버전>/pipeline.md`를 소유한다: `## 단계 진행`(design·상세설계·implement·verify·release 각 start/done 마커) · `> 보유 vX.Y.Z` · `## cross-stage 결정/escalation` · `## 경계 대조`(각 경계 전환 전 실행한 `run_all.py --boundary <경계>`의 PASS/위반 결과). 규약 전체는 `plugins/dev/run-state.md`.

- **각 단계 호출 직전** pipeline.md 단계 진행에 `시작 ✓`, 그 단계가 완료/PASS로 반환되면 `끝 ✓`를 쓴다.
- **각 경계 전환 직전** 경계 대조 게이트를 발화하고(아래 "단계 게이트"), 그 결과(경계·PASS/위반 수)를 `## 경계 대조`에 기록한다. 위반 0이어야 다음 단계로 전진한다.
- ⓪에서 산정한 `vX.Y.Z`를 `> 보유 vX.Y.Z`에 기록하고 ④에 전달한다.
- 단계 간 결정·escalation은 `## cross-stage 결정`에 로그한다.

## 0단계: 복원 (현재 상태 확인)

`.dev/<스프린트 버전>/pipeline.md`가 있으면 읽어 **멈춘 단계부터 자동 재개**한다(start/done 마커로 멈춘 지점 판정, 개발자에게 묻지 않음 — `run-state.md` §5). 없으면 새 run으로 폴더·pipeline.md를 생성하고 ⓪부터 시작한다. (⓪설계 게이트의 L3 결정, 또는 하류에서 bubble-up된 blocker는 재개와 무관하게 처리한다 — L3는 설계 게이트에서, blocker는 한 칸 위 단계로.)

## ⓪ 설계 — dev:design

진입은 항상 **요구사항**이다(단일 모드). 외부에서 완성된 설계처럼 보이는 게 들어와도 요구사항으로 취급한다 — `dev:design`은 항상 호출된다(skip 없음).

`dev:design`을 호출 → `design/design.md`(전략 설계 산출물) + 범위 묶음 + version bump(`vX.Y.Z`) 산정. **`vX.Y.Z`를 오케가 보유한다.** 요구사항이 못박은 강제사항은 `domain-architect`가 `[입력 강제]`로 수용한다.

## ① 상세설계 — dev:tactical

`design/design.md`를 입력으로 `dev:tactical` 호출. `tactical/` 생성 + change-scoped 검증 항목을 fragment에 기록. (구조적 L3는 ⓪에서 대부분 해소됨 — 상세설계은 잔여 L3만 escalate, L1/L2 값 가정은 릴리스 노트로 사후 보고.)

## ② 구현 — dev:implement

상세설계를 입력으로 `dev:implement` 호출. 구현 + mock 단위테스트. fragment의 코드·마이그레이션 섹션 채움.

## ③ 검증 — dev:verify

`dev:verify` 호출. deploy + verifier로 검증 원장의 AC 단정 실행. **verify 종결 게이트(`run_all.py --boundary verify` — L6·L7)가 위반 0이어야 ④로 진행한다.**

## ④ 릴리스 — dev:release

보유한 `vX.Y.Z`를 전달하여 `dev:release` 호출. CHANGELOG fold + `git tag` + 정리.

## 최종 보고

- 진행한 단계, 산출물(설계서/tactical/코드/검증 결과), 확정 버전 `vX.Y.Z`, 부여된 tag.

# 단계 게이트 + bubble-up

- 각 단계가 완료(또는 PASS)여야 다음 단계로 진행한다. 도구/환경 등 **진행 불가**는 개발자에게 전달하고 멈춘다.
- **경계별 결정론 대조 게이트 (커밋된 산출물 검사)**: 각 경계 전환 직전, 오케가 커밋된 산출물(특히 원장 `tactical/verification-ledger.md`)에 대해 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py --project-root <프로젝트> --boundary <다음 경계>`를 실행하고 **위반 0일 때만** 다음 단계로 넘긴다. 경계값은 싼→비싼 순으로 `design | tactical | implement | verify | release`이며, 앞 단계까지 닫혀야 할 층을 누적 검사한다 — tactical(커버리지 COV + 원장 L1~L3), implement(+L5 코더 종결), verify(+L6 verifier 종결·L7 보류 승인 토큰), release(L1~L7 전량). **각 단계 실행자는 자기 칸을 계속 기록하되 스스로 경계를 닫지 못한다** — 닫힘은 이 스크립트의 위반 목록이 판정한다. 결과는 pipeline.md `## 경계 대조`에 남긴다. (`--boundary` 없이 실행하면 종결 게이트가 발화하지 않아 작성 시점 산출물을 손상시키지 않는다.)
- **bubble-up (모순은 한 칸씩 위로)**: 한 단계가 자기 층에서 해결 못 한 모순을 `{blocker}`로 반환하면, 설계로 직행하지 않고 **바로 위 단계로 한 칸만** 되돌린다 — ③검증→②구현→①상세설계(상세설계)→⓪전략설계(design). 각 층은 "내 산출물 문제인가 / 물려받은 입력 문제인가"를 판별해 고치거나 한 칸 더 위로 넘긴다. **사람 결정이 필요하면 최상위 ⓪설계 게이트에서만** 이뤄진다(mid-cycle로 개발자에게 직접 묻지 않는다).
- 검증(③)의 verify 종결 게이트(`--boundary verify`)가 위반 0이 아니면 릴리스(④)로 진행하지 않는다.

# 원칙

- **기본은 단일 세션 순차 진행.** 병렬이 필요하면 각 기능을 별도 `dev:run` 세션으로 돌리고, ad-hoc `git merge`로 main에 합친 뒤 main에서 `dev:verify` → `dev:release`를 수행한다(머지는 이 메타 오케가 하지 않는다).
- version은 ⓪/오케가 보유하여 ④에 전달한다. 상세설계서엔 버전이 없다.
- 각 단계 스킬에 "무엇을" 위임만 하고, 단계 내부 처리는 해당 스킬이 담당한다.

# 단계 간 컨텍스트 인계 (누적 방지)

이 메타 오케는 각 단계 스킬을 **같은 세션에서 순차 실행**한다 — 스킬은 서브에이전트가 아니라 같은 컨텍스트에서 도는 지시다. 컨텍스트 격리는 각 스킬이 *에이전트에 위임할 때만* 생기고, **스킬 자체는 격리되지 않는다.** 따라서 아무것도 하지 않으면 5개 단계 지시문과 그 아래 수십 개 위임의 반환 요약이 한 세션에 그대로 쌓인다.

**단계 경계에서는 파일로 인계하고, 앞 단계의 내부 detail을 끌고 가지 않는다:**

- 각 단계가 끝나면 그 단계의 **산출물 경로 + 게이트 판정(완료/PASS/blocker) + 다음 단계가 실제로 쓰는 값**(버전, 스프린트 키, 미해결/가정 건수)만 보유한다
- 단계 내부의 위임별 반환 상세·에이전트 보고 원문·중간 판단 근거는 **다음 단계로 넘기지 않는다**. 필요하면 그 단계가 소유한 run-state 파일(`.dev/<스프린트 버전>/{design,tactical,implement,verify}.md`)에서 다시 읽는다 — run-state가 단계 간 인계 매체다
- 다음 단계 스킬에는 **경로와 게이트 결과만** 전달한다. 앞 단계 산출물의 내용을 프롬프트로 옮겨 적지 않는다(각 단계 스킬의 위임 원칙과 동일한 규율)

**세션을 나눠야 하는 신호.** 아래 중 하나라도 해당하면 `dev:run` 한 세션으로 완주하지 말고, 단계별로 `dev:design` → `dev:tactical` → `dev:implement` → `dev:verify` → `dev:release`를 **별도 세션으로 나눠 호출**한다. run-state가 인계를 보장하므로 세션을 끊어도 이어진다:

- 도메인 수가 많다(대략 8개 이상) — 상세설계 단계만으로 위임이 수십 건이 된다
- 앞 단계에서 bubble-up 재사이클이 발생해 같은 단계를 두 번 이상 돌았다
- 한 단계라도 사용량 한도에 걸려 중단된 적이 있다

> 순차화·누적은 벽시계에 **증폭**으로 돌아온다. 실측(edutalk)에서 순차 실행이 활성 시간을 2배로 늘렸고, 그 결과 주간 사용량 한도에 걸려 9.3시간이 통째로 정지되면서 벽시계가 5.1시간에서 14.5시간으로 부풀었다. 컨텍스트를 아끼는 것이 곧 벽시계를 아끼는 경로다.

# 금지사항

- verify 종결 게이트(`run_all.py --boundary verify`) 위반이 0이 아닌 채로 릴리스로 진행하지 않는다
- 서브에이전트/스킬이 `{blocker}`를 반환하면 직접 판단하지 않고 **한 칸 위 단계로 bubble-up**한다(설계로 직행 아님). 사람 결정은 ⓪설계 게이트에서만. 도구/환경 진행 불가만 개발자에게 전달한다
- 머지를 이 메타 오케에서 수행하지 않는다 (병렬은 ad-hoc git merge 선행)

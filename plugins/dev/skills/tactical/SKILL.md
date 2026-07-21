---
name: tactical
description: |
  구현 상세설계서 생성 오케스트레이터.
  설계서를 분석하여 tactical/ 디렉토리의 구현 상세설계서를 생성하거나 갱신한다.
  This skill should be used when the user says "dev:tactical", "상세설계서 만들어줘",
  "스펙 작성해줘", "구현 상세설계서 생성해줘", or provides a design document for 상세설계 generation.
disable-model-invocation: false
argument-hint: [design/design.md 경로]
---

# 역할

구현 상세설계서 생성 오케스트레이터. 설계서를 분석하고 system-service-writer, entities-writer, rules-writer,
scenarios-writer, screens-writer, domain-api-writer, ui-design-writer, verification-criteria-writer 에이전트를 위임하여 tactical/ 구조를 완성한다. 위임 스케줄은 `harness-design.md` §6.3 공통 스케줄링 원리를 따른다 — **작업 단위 = 문서역할 × 도메인**, 매 시점의 프론티어(의존·배타가 풀린 독립 노드 집합)를 한 메시지에 동시 위임(프론티어 배치), 의존 엣지가 있는 노드만 순서.

**도메인 내부 의존 엣지는 4단 + 2갈래 분기다** — `entities → rules → scenarios → {screens, api}`(screens와 api는 서로 의존하지 않아 **동시 출발**), 그리고 `screens(d) → ui(d)`(**같은 도메인 안에서만** 걸리는 로컬 엣지). api는 scenarios·entities·rules·system/service를 권위로 삼고 screens를 참조하지 않으므로(domain-api-writer `입력 권위 분리` 표) screens 완료를 기다리지 않는다. ui(d)도 그 도메인 screens.md + service.md 디자인 정책만 있으면 되므로 **다른 도메인의 screens를 기다리지 않는다**.

**전역 배리어는 둘뿐이다** — 검증 원장 writer(완료기준+전 도메인 상세에 의존하는 cross-cutting 노드)와 전역 검증(9-B). 그 외에는 도메인 경계를 넘는 pipeline으로만 흐른다.

기본 모드는 **자율 진행**이다. 각 writer는 완결 사이클로 자율 범위를 다 쓰고, 못 정한 것은 데이터로 반환한다 — 상세설계 단계에서 사용자에게 mid-cycle로 묻지 않는다.

> **입력 = `design/design.md`(전략 설계 산출물).** 구조적 L3(도메인 경계·자금흐름 구조·보안 아키텍처 등)는 ⓪`dev:design` 게이트에서 대부분 해소됐다. 상세설계 단계는 전술 상세를 채우며, 못 정한 것은 두 갈래로 처리한다 — 되돌릴 수 있는 값은 **가정**(fragment 누적 → 릴리스 노트 사후 보고, `dev:release`), 가정조차 불가능한 필수 결정이나 물려받은 도메인 경계·관계의 모순은 **⓪`dev:design`으로 bubble-up**(한 칸 위). **개발자는 상세설계 산출물을 직접 검토하지 않으며**, 사람 검토 게이트는 ⓪설계 하나다.

# 설계 의도

- writer 8종(system-service · entities · rules · scenarios · screens · api · ui-design · verification-criteria)은 항목별로 결정 등급을 판별한다. L1(자율)/L2(가정)는 작성하고, L3(결정 요청)만 escalate 한다. 각 writer는 **반환 전 self-verify**로 자기 산출물의 결정론 위반을 스스로 해소한다(예방 — verify→fix 재사이클 최소화)
- system-service-writer를 워크플로우 가장 앞에 둔다. 컨벤션 결정 항목들이 L3로 escalate될 가능성이 높고, 여기서 받은 결정값이 후속 writer의 베이스가 된다. 특히 프론트엔드 디자인 정책(디자인 토큰·컴포넌트 파운데이션·상태·시각 위계·모션·a11y 컨벤션의 결정값)이 여기서 service.md에 박혀 ui-design-writer의 베이스가 된다
- **스케줄은 §6.3 의존성 그래프**다 — 작업 단위 = 문서역할 × 도메인. 도메인 내부 의존은 `entities → rules → scenarios → {screens, api}` (screens·api는 상호 무의존이라 scenarios 완료 시 **동시 출발**), 그리고 `screens(d) → ui(d)` (도메인 로컬 엣지). **매 시점의 프론티어(의존·배타가 모두 풀린 독립 노드 집합) 전체를 한 메시지에 동시 위임**(frontier fan-out)하고, 의존 엣지가 있는 노드만 순서를 지킨다. 프론티어는 **매 노드 완료마다 갱신**된다 — A 도메인 entities가 끝나면 A rules를 프론티어에 넣어 시작하며 동시에 B 도메인 entities가 계속 도는, 도메인 경계를 넘는 pipeline. **한 도메인은 다른 도메인을 기다리지 않고 entities부터 ui까지 끝까지 흘러간다.** 전역 배리어는 검증 원장(cross-cutting)과 전역 검증(9-B) 둘뿐이며, 그 외에는 프론티어 fan-out으로만 흐른다
- ui-design-writer(화면별 시각 상세설계 `ui.md`)는 **그 도메인의 screens.md가 끝나는 즉시** 프론티어에 편입한다(`screens(d)→ui(d)` — 도메인 로컬 엣지). ui.md가 필요로 하는 건 그 도메인 screens.md(행위) + service.md 디자인 정책뿐이므로 **다른 도메인의 screens나 cross-domain screens를 기다리지 않는다**. cross-domain ui만 cross-domain screens에 의존한다. 이 엣지를 전역 배리어로 승격하면 실측상 가장 오래 걸리는 단계가 통째로 임계 경로에 올라가므로 하지 않는다. 행위(screens.md)와 시각(ui.md)은 별도 파일·별도 writer로 분리한다. 외부 고정 디자인이 입력 강제로 들어오면 ui-design-writer가 *전달된 범위만 전사*하고 나머지는 자율 저술한다(부분 커버리지 — 7단계 라우팅)
- verification-criteria-writer(검증 원장 `tactical/verification-ledger.md`)는 **모든 도메인 writer + ui-design-writer가 끝난 뒤 마지막**에 둔다(완료기준+전 도메인 상세→원장 엣지 — ui-design의 `screens(d)→ui(d)`가 도메인 로컬 엣지인 것과 달리, 이건 전 도메인을 가로지르는 진짜 전역 배리어다). design.md `## 완료 기준`을 앵커로, 모든 도메인 상세(scenarios/rules/entities/api/screens/ui + cross-domain)·system/service 위에서 각 완료 기준을 **실행 가능한 3면(UI/UX·로직·데이터)에 걸친 면별 다중 단정**(절차→관측→기대·채널 1~5)으로 분해한다(원장 v2). cross-cutting 계층이라 자기 writer를 가진다 — 도메인 writer는 각자 도메인만 보므로 3면 완비·통합 seam 커버·누적 승계 같은 목표 수준 coherence를 소유할 수 없다. 원장은 커밋·누적 산출물이며, 이전 fragment `## 검증 항목`이 durable SoT였던 것을 **원장이 대체**한다(아래 11단계)
- 각 도메인의 writer가 끝나면 **그 도메인만 로컬 검증**(tactical-verifier 로컬 스코프)으로 조기·병렬 확인하고, 모든 writer 완료 후 **전역 검증**(도메인 간)으로 마무리한다 — 도메인 내부 결함을 국소에서 잡아 전역 재사이클을 줄인다

# 입력

$ARGUMENTS에서 `design/design.md`(전략 설계 산출물) 경로를 받는다. (이하 절차의 "설계서"는 이 design.md를 가리킨다.)

# 실행 절차

## run-state — `tactical.md` 소유

이 단계는 `.dev/<스프린트 버전>/tactical.md`를 소유한다(규약: `plugins/dev/run-state.md`). `## 계획`(§6.3 실행 shape — (문서역할 × 도메인) 노드·의존 엣지·**프론티어별 동시 N**(각 위상 레벨에서 한 메시지에 동시 위임할 독립 노드 수)) · `## 진행`(노드별 writer start/done 마커 + 도메인별 로컬 검증 마커 + **노드별 재위임 횟수** — 9단계 재사이클 상한 판정 근거) · `## escalation 로그`(L3 결정 요청·가정 — 과정)를 둔다. 위임은 **프론티어 배치 단위**로 마킹한다 — 배치를 던지기 직전 그 프론티어의 **모든 노드에 `시작 ✓`를 한꺼번에** 찍고, 한 메시지로 다 위임하고, **반환되는 대로 각 노드에 `끝 ✓`**를 찍는다("하나씩 시작→위임→끝" 원자 리듬이 아니라 배치 fan-out). 확정된 가정/결정 *값*은 fragment `## 가정/결정`으로 옮긴다(run-state.md §6).

## 0단계: 현재 상태 자동 감지 (복원 포함)

`.dev/<스프린트 버전>/tactical.md`가 있으면 먼저 읽어 **멈춘 도메인/writer부터 자동 재개**한다(start/done 마커 기준, 개발자에게 묻지 않음 — run-state.md §5). 이어서 기존 `tactical/` 존재 여부와 프로젝트 코드베이스 존재 여부를 자동으로 감지한다.

**A. 기존 `tactical/` 가 존재하는 경우 (기존 상세설계서가 있는 상황):**
- 기존 상세설계서를 읽어 현재 상태를 파악한다. 직전 릴리스 버전(forked-from)은 최신 git tag(`vX.Y.Z`)로 본다 (없으면 미릴리스 = `v0.0.0` base)
- 코드베이스 분석은 불필요하다 (기존 상세설계서 + 설계서만으로 충분)
- 1단계로 진행한다

**B. 기존 `tactical/` 가 없고 코드베이스가 존재하는 경우 (기존 프로젝트에 최초 상세설계서 생성):**
- 코드베이스를 분석하여 현재 프로젝트 상태를 파악한다 (최초 1회)
- 분석 결과를 가정 목록에 누적한다 (writer가 검증할 수 있도록)
- 1단계로 진행한다

**C. 기존 `tactical/` 도 코드베이스도 없는 경우 (신규 프로젝트):**
- 설계서에서 직접 1단계로 진행한다

자동 감지 후 진행한다. 다만 아래는 자체 판단으로 지어내지 않는다 — 스코프 판별은 결정론적으로 하고, 해소 불가한 것만 처리한다:
- 스프린트 버전(forked-from / 스프린트 키) 산정 충돌 또는 누락 → 규약(run-state·git tag)으로 결정론 산정한다. 그래도 불가하면 개발자에게 진행 불가로 보고
- 일부 도메인은 갱신, 일부는 신규로 보이는데 어느 케이스인지 불명확 → 설계서 델타로 판별한다. 그래도 불가하면 진행 불가로 보고
- 코드베이스의 기술 스택이 설계서와 충돌 → 상위(설계/요구사항)의 모순이므로 ⓪`dev:design`으로 **bubble-up** 한다 (mid-cycle로 사용자에게 묻지 않음)

## 1단계: 설계서 분석 및 범위 자동 식별

$ARGUMENTS와 설계서를 분석하여 아래를 자동으로 파악한다:
- 어떤 도메인이 관련되는가
- 사용자 인터랙션이 있는가
- 시스템 내부 동작이 있는가
- 여러 도메인을 관통하는 흐름이 있는가
- 어떤 서비스가 관련되는가
- 시스템 구조가 변경되는가

식별 결과는 가정 목록에 누적한다 (마지막 통합 가정 검토에서 사용자가 함께 검토). 추가 사용자 확인 없이 2단계로 진행한다.

## 2단계: system-service-writer 위임 (워크플로우 가장 앞)

이 단계가 워크플로우 가장 앞에 위치하는 이유: 컨벤션 결정 항목들이 L3로 escalate될 가능성이 높고, 여기서 받은 결정값이 후속 writer의 베이스가 되기 때문이다.

아래 템플릿대로만 전달한다. 템플릿 외의 내용을 추가하지 않는다:

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우)
모드: 자율
```

각 writer 호출은 **완결 사이클**이다 — 멈춰서 되묻지 않고, 못 정한 것을 데이터로 담아 반환한다. 반환에 따라 처리한다:
- **완결 (가정 포함)**: 자율 범위를 다 쓰고, 되돌릴 수 있는 값은 합리적 가정으로 마킹해 반환한다. 가정 목록을 누적하고(10단계 릴리스 fold) 다음 단계로 진행한다
- **bubble-up (설계 blocker)**: writer가 물려받은 것과의 모순(도메인 경계·관계) 또는 **가정조차 불가능한 필수 결정**(사람만 아는 값이 요구사항·설계에 없음)을 `{blocker}`로 반환하면, 상세설계 층에서 해결 불가한 전략설계/요구사항 문제다 — 사용자에게 직접 묻지 말고 **한 칸 위(⓪`dev:design`)로 되돌린다**. `dev:run`(또는 개발자)이 architect를 재호출해 재결정한 뒤 상세설계을 재개한다. (bubble-up은 run-state escalation 로그에 기록)
- **진행 불가**: 사용자에게 보고한다. 지시를 받아 처리한다

## 3단계: 도메인 지식 — entities-writer → rules-writer 위임

도메인 지식은 **entities.md → rules.md** 순으로 쓴다(§6.3 의존 엣지 `entities→rules` — rules가 entities의 필드/타입을 참조). entities는 선행 의존이 없으니 **모든 독립 도메인의 entities-writer Task를 한 메시지에 동시 위임(프론티어 배치)**한다. 한 도메인 entities가 끝나는 대로 그 도메인 rules를 프론티어에 편입하고(도메인 경계를 넘어 pipeline — A 도메인 entities 완료 시 A rules를 시작하며 동시에 B 도메인 entities 계속), 매 완료로 갱신된 프론티어에 준비된 노드가 여럿이면 역시 한 메시지에 동시 위임한다.

### 3-1. entities-writer 위임 (프론티어 배치 — 전 독립 도메인 동시)

지금 프론티어의 **모든 독립 도메인 entities 노드**마다 아래 템플릿을 채워 **한 메시지에 Task를 동시 위임**한다:

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상 도메인: {도메인명}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

### 3-2. rules-writer 위임 (프론티어 — entities 완료된 도메인부터)

entities가 끝난 도메인의 rules 노드를 프론티어에 편입해, 동시에 준비된 것들을 **한 메시지에 Task를 동시 위임**한다:

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상 도메인: {도메인명}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우 — 특히 방금 작성된 해당 도메인 entities.md)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

에이전트 반환 상태에 따라 2단계와 동일하게 처리한다. 프론티어는 매 완료마다 갱신되며 준비된 노드는 한 메시지에 동시 위임한다(참조되는 도메인이 먼저). 결정 요청이 발생하지 않은 도메인들은 사용자 개입 없이 진행한다.

## 4단계: 도메인 행위 — scenarios-writer → screens-writer 위임

도메인 행위는 **scenarios.md → screens.md** 순으로 쓴다(§6.3 의존 엣지 `scenarios→screens`). 해당 도메인 knowledge(rules/entities) 완료가 선행 조건이다(`knowledge→behavior`). screens.md는 프론트엔드가 있는 도메인에만 생성한다. **knowledge가 끝난 모든 도메인의 scenarios 노드를 한 메시지에 동시 위임(프론티어 배치)**하고, scenarios가 끝난 프론트엔드 도메인의 screens를 프론티어에 편입해 준비된 것끼리 동시 위임한다.

> **scenarios(d) 완료 시 프론티어에 들어가는 것은 screens(d)와 api(d) 둘 다다** — 두 노드는 서로 의존하지 않으므로 같은 메시지에 함께 위임한다(5단계 참조). screens.md가 없는 백엔드 전용 도메인은 api(d)만 편입된다.

### 4-1. scenarios-writer 위임 (프론티어 배치 — knowledge 완료 도메인 동시)

knowledge가 끝난 **모든 독립 도메인의 scenarios 노드**마다 아래 템플릿을 채워 **한 메시지에 Task를 동시 위임**한다:

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상 도메인: {도메인명}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우 — 특히 해당 도메인 rules.md·entities.md)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

### 4-2. screens-writer 위임 (프론티어 — scenarios 완료된 프론트엔드 도메인부터)

scenarios가 끝난 프론트엔드 도메인의 screens 노드를 프론티어에 편입해, 준비된 것들을 **한 메시지에 Task를 동시 위임**한다:

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상 도메인: {도메인명}
프론트엔드 여부: {해당 도메인에 프론트엔드가 있는지 여부}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우 — 특히 해당 도메인 scenarios.md)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

에이전트 반환 상태에 따라 2단계와 동일하게 처리한다.

## 5단계: 도메인 API — domain-api-writer 위임 (프론티어 배치 — screens와 동시 출발)

api의 선행 조건은 **그 도메인의 scenarios·entities·rules + system/service**다. **screens.md는 선행이 아니다** — domain-api-writer의 `입력 권위 분리` 표는 scenarios(무엇을 노출) · entities(필드 타입) · rules(분기) · service/system(공통 규약)만을 권위로 두며 screens를 참조하지 않는다. 따라서 **scenarios(d)가 끝나면 screens(d)와 api(d)를 같은 프론티어에 함께 넣어 한 메시지에 동시 위임**한다. api를 screens 뒤로 미루지 않는다 — 근거 없는 직렬 1홉이며, 그 비용이 도메인 수만큼 곱해진다.

**선행이 풀린 모든 도메인의 domain-api-writer Task를 한 메시지에 동시 위임(프론티어 배치)**한다. 각 도메인마다 아래 템플릿을 채워 전달한다(해당 도메인이 외부에 노출하는 endpoint를 상세설계화):

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상 도메인: {도메인명}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

에이전트 반환 상태에 따라 2단계와 동일하게 처리한다.

여러 도메인은 §6.3 공통 원리로 스케줄한다 — 준비된 도메인은 한 메시지에 동시 위임(프론티어 배치), 의존 엣지가 있으면 순서. 결정 요청이 발생하지 않은 도메인들은 사용자 개입 없이 진행한다.

## 6단계: cross-domain — scenarios-writer → screens-writer (cross-domain scope) 위임

여러 도메인을 관통하는 흐름이 식별된 경우, scenarios-writer·screens-writer를 cross-domain scope로 위임한다(cross-domain/{흐름}.md = scenarios-writer, cross-domain/screens.md = screens-writer). 흐름 scenarios가 screens보다 먼저다(`scenarios→screens`). **독립 흐름의 scenarios 노드는 한 메시지에 동시 위임(프론티어 배치)**하고, scenarios가 끝난 흐름의 screens를 프론티어에 편입해 준비된 것끼리 동시 위임한다.

**흐름 f의 선행은 f가 관통하는 참여 도메인의 상세뿐이다 — 전 도메인이 아니다.** 이 단계는 전역 배리어가 아니며, 단계 번호(6)는 서술 순서일 뿐 "3~5단계가 전부 끝나야 시작"을 뜻하지 않는다. 흐름 f가 도메인 {A,B}만 관통하면 A·B의 상세가 준비되는 즉시 f를 프론티어에 편입한다 — 무관한 도메인 C·D의 완료를 기다리지 않는다. 참여 도메인 집합은 1단계에서 식별한 흐름 정의에서 읽는다.

### 6-1. scenarios-writer (cross-domain scope)

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상: cross-domain
식별된 cross-domain 흐름: {흐름 목록}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

### 6-2. screens-writer (cross-domain scope — cross-domain/screens.md가 필요한 경우, 6-1 완료 후)

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상: cross-domain
식별된 cross-domain 흐름: {흐름 목록}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우 — 특히 cross-domain/{흐름}.md)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

에이전트 반환 상태에 따라 2단계와 동일하게 처리한다.

## 7단계: 프론트엔드 시각 상세설계 — ui-design-writer 위임

프론트엔드 레이어가 있는 각 도메인(screens.md가 생성된 도메인)과 cross-domain screens.md가 있으면 그 흐름에 대해, 화면별 시각 상세설계 `ui.md`를 작성하도록 ui-design-writer에 위임한다.

**이 단계는 배리어가 아니다.** `screens(d) → ui(d)`는 **도메인 로컬 엣지**이므로, 한 도메인의 screens.md가 끝나면 **그 즉시** 그 도메인 ui 노드를 프론티어에 편입해 위임한다 — 다른 도메인의 screens나 cross-domain screens 완료를 기다리지 않는다. ui(d)가 읽는 것은 그 도메인 screens.md와 service.md 디자인 정책뿐이기 때문이다(ui-design-writer `입력 — 무엇 위에 얹는가`). cross-domain ui만 cross-domain screens(6-2) 완료에 의존한다.

따라서 실제 위임 리듬은 "모든 screens가 끝난 뒤 ui 일괄"이 아니라, **A 도메인 ui가 도는 동안 B 도메인 screens가 계속 도는 pipeline**이다. 매 완료로 갱신된 프론티어에 ui 노드가 여럿 준비되면 한 메시지에 동시 위임한다.

> 이 엣지를 전역 배리어로 승격하지 않는다 — 실측상 ui가 가장 오래 걸리는 단계이며, 전역 배리어로 두면 그 소요가 통째로 임계 경로에 올라간다.

> 프론트엔드 화면이 없는 프로젝트(screens.md 0건)면 이 단계는 건너뛴다.

> **고정 디자인(입력 강제) 라우팅**: design.md `## 설계 결정과 근거`에 **디자인 SoT = 외부 고정 산출물([입력 강제])**이 있으면, 그 출처를 아래 템플릿의 `고정 디자인(입력 강제)` 필드로 전달한다. ui-design-writer는 *전달된 범위만 전사*하고 나머지는 자율 저술한다(부분 커버리지 — 모든 화면/상태를 덮지 않음). 고정 디자인이 없으면 이 필드를 비운다.

도메인 scope 위임 템플릿(프론트엔드 도메인마다):

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상 도메인: {도메인명}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
고정 디자인(입력 강제): {design.md 디자인 SoT 출처 — 해당 도메인 화면 범위. 없으면 비움}
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록 — 특히 해당 도메인 screens.md, service/{프론트엔드 서비스}.md}
모드: 자율
```

cross-domain scope 위임 템플릿(cross-domain screens.md가 있는 경우):

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로}
설계서 참조 범위: {design.md 내 이 작업 범위에 해당하는 섹션 앵커 — 도메인 절·관련 핵심 흐름·공통 결정값 절. 특정 불가면 비움}
대상: cross-domain
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
고정 디자인(입력 강제): {design.md 디자인 SoT 출처 — cross-domain 화면 범위. 없으면 비움}
기존 상세설계서 경로: {tactical/ 디렉토리 경로} (존재하는 경우)
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록 — 특히 cross-domain/screens.md, service/{프론트엔드 서비스}.md}
모드: 자율
```

에이전트 반환 상태에 따라 2단계와 동일하게 처리한다. 여러 프론트엔드 도메인은 §6.3 공통 원리로 스케줄한다 — 준비된 도메인의 ui 노드는 한 메시지에 동시 위임(프론티어 배치), 의존 엣지가 있으면 순서. 결정 요청이 없는 도메인은 사용자 개입 없이 진행한다.

## 8단계: 검증 원장 — verification-criteria-writer 위임 (cross-cutting·최후미 배리어)

모든 도메인 writer + ui-design-writer가 끝나면(§6.3 `완료기준+전 도메인 상세→원장` 엣지 — ui-design의 `screens(d)→ui(d)`가 도메인 로컬 엣지인 것과 달리, 이건 전 도메인을 가로지르는 진짜 전역 배리어다), 검증 원장 `tactical/verification-ledger.md`를 작성하도록 verification-criteria-writer에 위임한다. 이 단계는 프론티어 fan-out이 아니라 **모든 writer 완료를 기다리는 배리어**다. 이 writer는 도메인별 반복이 아니라 **cross-cutting 단일 위임**이다 — design.md `## 완료 기준`을 앵커로 전 도메인 상세를 한 번에 보고 각 완료 기준을 3면(UI/UX·로직·데이터)에 걸친 **면별 다중 단정**(절차→관측→기대, 채널 태그 1~5)으로 분해한다(원장 v2). 도메인 writer는 각자 도메인만 보므로 3면 완비·통합 seam 커버·누적 승계 coherence를 소유할 수 없어, 이 계층은 전용 writer가 소유한다.

> **AC 블록 메타에 `> 요구사항: R-n` 강제**: `design/requirements.md`(R-n 목록)를 채택한 경우, 원장의 각 AC 블록 메타에 그 AC가 앵커된 요구사항 식별자 `> 요구사항: R-n`을 기록하도록 위임한다 — design.md 완료 기준 표의 R-n 앵커를 원장 AC로 승계해, 하류 커버리지 대조(요구사항→완료기준→AC)가 원장에서 닫히게 한다. requirements.md가 없으면 이 메타는 no-op(레거시 하위호환).

> design.md에 `## 완료 기준`이 없으면 writer가 `{blocker}`로 ⓪`dev:design`에 bubble-up 한다(완료 기준은 설계 소유·사람 게이트 대상). 원장은 완료 기준을 상향식으로 지어내지 않는다.

위임 템플릿:

```
프로젝트 경로: {프로젝트 절대 경로}
설계서 경로: {설계서 경로 — design.md, 특히 ## 완료 기준}
설계서 참조 범위: {## 완료 기준 + 각 완료 기준이 실제로 가리키는 도메인 절. 그 밖의 도메인 절은 읽지 않아도 된다}
결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
직전 archive 원장: {tactical-archive/<직전 버전>/verification-ledger.md — 존재하는 경우 (보류/미결 승계 근거)}
기존 상세설계서 경로: {tactical/ 디렉토리 경로 — 전 도메인 상세 + system/service + 기존 verification-ledger.md}
생성된 상세설계서: {이전 에이전트들이 보고한 파일 목록}
모드: 자율
```

에이전트 반환 상태에 따라 2단계와 동일하게 처리한다. 상태 칸(PASS/보류/해소 증거)은 writer가 채우지 않는다 — 검증 항목·기준만 작성하고 상태는 초기 미착수(승계 항목은 이월값)로 두며, 나중에 `dev:verify`의 verifier가 실행 결과로 갱신한다.

## 9단계: 상세설계서 검증 (tactical-verifier 위임 — 로컬 → 전역)

검증은 §6.3에 따라 **두 스코프**로 나뉜다(tactical-verifier `검증 범위`). writer self-verify가 결정론 위반을 이미 예방하므로, 이 단계는 그 위에서 의미 정합을 본다.

- **9-A 로컬(도메인) 검증 — 조기·병렬**: 한 도메인의 writer들(entities/rules/scenarios/screens/api/ui)이 끝나면 그 도메인만 즉시 로컬 스코프로 검증한다. 다른 도메인 작성과 겹쳐 병렬로 돈다. 도메인 *내부* 정합(rules↔entities↔scenarios↔api)을 국소에서 잡아 전역 재사이클을 줄인다.
- **9-B 전역 검증 — 최종 1회(배리어)**: 모든 writer(원장 writer 포함) + 로컬 검증이 끝나면 전역 스코프로 *도메인 간* 정합(컨텍스트맵·공유 엔티티·cross-domain 흐름·system/service↔도메인)과 **검증 원장 감사**(면별 다중 단정 완비·완료 기준 커버리지·통합 seam·계약 미결·누적 승계·**채널 하향 정당성**(채널5 과이월 탐지) — 결정론 4종 + LLM judge 차원)를 본다. 로컬이 통과시킨 도메인 내부는 다시 의심하지 않는다. 원장 위반 시 verification-criteria-writer를 재위임한다.

각 스코프에서 tactical-verifier가 Stage 1(deterministic) → Stage 2(LLM judge)로 본다.

| 단계 | 성격 | 흡수 항목 |
|------|------|----------|
| Stage 1 (deterministic) | 외부 스크립트 기반 무결성 검증. ID/필드 일치, 카탈로그 기준 위반 | cross-domain [도메인] 태그, api ↔ scenarios 트리거, api 필드 ↔ entities 속성(이름·타입), api 인증 ↔ rules 역할, 검증 원장 4종(면별 다중 단정 완비·PASS 해소증거·계약 미결 0·누적 승계 — 전역) |
| Stage 2 (LLM judge) | 의미적 정합성 검증 | rules ↔ scenarios 기대 결과, scenarios ↔ entities 의미 일치, system/service ↔ 도메인 정합, api ↔ system/service 결정값, cross-domain 참조 정합, 검증 원장(완료 기준 커버리지·단정 적절성·채널 하향 정당성 — 전역) |

위임 템플릿 (9-A 로컬 — 도메인마다, writer 완료 즉시):

```
프로젝트 경로: {프로젝트 절대 경로}
검증 범위: 로컬(도메인) — {도메인명}
모드: 자율
```

위임 템플릿 (9-B 전역 — 최종 1회):

```
프로젝트 경로: {프로젝트 절대 경로}
검증 범위: 전역
검증 대상: tactical/ 전체
모드: 자율
```

에이전트 반환에 따른 처리:
- **PASS**: 다음 단계(10단계 통합 가정 검토)로 진행한다
- **Stage 1 FAIL**: 위반 사항 목록을 받아 권장 조치(어느 writer를 재호출할지)에 따라 해당 writer를 **재위임(새 호출)**한다 — 위반 항목 + 상세설계 경로를 템플릿에 담아 전달하면 writer가 자신이 쓴 상세설계 파일에서 맥락을 회복한다. 갱신 후 tactical-verifier 재호출 (결정론 신호 → 재사이클, 사용자 개입 아님)
- **Stage 2 FAIL**: 의미적 결함은 **상세설계 내부 문제**이므로 사용자에게 묻지 않고 해당 writer를 **재위임(새 호출)**해 고친다 → tactical-verifier 재호출로 재검증. 단 결함이 **도메인 경계·관계에서 비롯돼** 상세설계 층에서 고칠 수 없으면 ⓪`dev:design`으로 **bubble-up** 한다
- **진행 불가**: 사용자에게 보고한다

**재사이클 상한 (종료 보장):**

재위임 루프는 무한히 돌 수 없다. 같은 노드(문서역할 × 도메인)에 대한 재위임은 **최대 2회**까지다. run-state `## 진행`에 노드별 재위임 횟수를 기록하고, 매 재위임 전에 확인한다.

- **1·2회차**: 위반 항목을 담아 해당 writer를 재위임한다 (결정론 재사이클)
- **3회차 진입 시**: 재위임하지 않는다. 그 노드의 잔여 위반을 **`미해결[]`로 확정**하고 run-state escalation 로그에 `재사이클 상한 도달 — {노드} / {잔여 위반 목록}`으로 남긴 뒤, **나머지 노드의 검증을 계속 진행한다**(한 노드의 상한 도달이 전체를 멈추지 않는다)
- 상한에 도달한 노드가 있으면 12단계 최종 보고에 **별도 항목으로 반드시 보고**한다 — 은폐하지 않는다
- 같은 노드가 **서로 다른 위반**으로 재지적되는 경우도 횟수에 합산한다(위반 종류별 카운터를 따로 두지 않는다 — 그러면 상한이 무력화된다)
- 9-B가 **도메인 경계·관계 문제**로 판정하면 재위임 대상이 아니라 ⓪`dev:design` bubble-up이다(상한과 무관 — 애초에 상세설계 층에서 고칠 수 없음)

> 상한을 두는 이유: Stage 2는 LLM judge라 비결정적이며, 한 번에 모든 결함을 잡지 못할 수 있다. 상한이 없으면 "고칠 때마다 새 지적이 나오는" 루프가 종료 보장 없이 돌고, 실무적으로는 사용량 한도에 먼저 부딪혀 세션이 조각난다. 미해결로 확정해 원장·릴리스 노트로 넘기는 편이 무한 재사이클보다 낫다.

검증이 PASS이거나 사용자 결정으로 의미적 결함이 수용되면 다음 단계로 진행한다.

## 9.5단계: 경계 대조 게이트 (tactical 종결 — 결정론)

전역 검증(9-B)까지 통과하면, 커밋될 상태의 원장·완료 기준에 대해 tactical 경계 종결 게이트를 실행한다:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py --project-root {프로젝트 절대 경로} --boundary tactical
```

`--boundary tactical`은 **커버리지 COV(요구사항→완료기준→AC) + 원장 L1~L3**을 검사한다 — 각 완료 기준이 원장 AC로 분해됐고(COV), AC 블록이 3면 완비(L1)·상태 칸/해소 증거 형식(L2)·`계약 미결` 0(L3)인지를 결정론으로 본다. **위반 0이어야 tactical 단계가 완료(닫힘)로 판정된다** — 스킬은 원장에 자기 산정을 기록하되 스스로 경계를 닫지 못하며, 닫힘은 이 스크립트의 위반 목록이 판정한다.

- **커버리지(COV) 위반**(완료 기준이 원장 AC로 안 덮임·AC가 완료 기준/요구사항에 앵커 안 됨): verification-criteria-writer를 **재위임**(9단계 재사이클 상한 내)해 누락 AC·앵커를 채운다. 갱신 후 게이트 재실행.
- **완료 기준 자체가 부재**(요구사항에 대응하는 완료 기준이 design.md에 없어 원장이 덮을 앵커가 없음): 상세설계 층에서 지어낼 수 없으므로 ⓪`dev:design`으로 **bubble-up** 한다(완료 기준은 설계 소유·사람 게이트 대상).
- **L1~L3 위반**: 9-B의 원장 감사와 동일 처리 — verification-criteria-writer 재위임(상한 내).

위반 0이면 10단계로 진행한다.

## 10단계: 가정 누적 (비차단 — 릴리스 노트 fold 대상)

모든 writer가 누적한 가정 목록을 통합하여 **fragment `## 가정/결정`에 기록**한다. **개발자에게 검토 게이트를 걸지 않는다** — 상세설계 단계부터 개발자는 산출물을 직접 검토하지 않는다(사람 게이트는 ⓪설계 하나). L1/L2 값 가정은 모두 되돌릴 수 있는 값이므로, `dev:release`가 이 가정 목록을 **릴리스 노트의 "가정한 값" 섹션으로 fold**하고, 개발자는 원하는 값만 다음 개발 사이클에 수정한다.

> 예외 — **가정 불가 필수 결정 / 상위 모순**: writer가 가정조차 불가능한 필수 결정이나 도메인 경계·관계의 모순을 `{blocker}`로 반환하면, 그건 상세설계 층에서 해결 불가하므로 개발자에게 mid-cycle로 묻지 않고 ⓪`dev:design`으로 **bubble-up** 한다(2~7단계 처리와 동일). 사람 게이트는 ⓪설계 하나이며, 필요한 사람 결정은 거기서 이뤄진다.

가정 분류(릴리스 노트 가독성용 태깅, 검토 게이트 아님):
- **비즈니스/UX 영향**: 개발자가 다르게 정할 여지가 있는 항목 (UX 톤, 일반 디폴트값 등)
- **기술적 디폴트**: 표준 컨벤션에 가까운 항목 (timestamp 컬럼명 등)

## 11단계: fragment 생산 + 상세설계서 스냅샷

상세설계서 작성과 가정 검토가 모두 끝나면, 스킬이 직접 (1) **스프린트 fragment** `changelog.d/<스프린트 버전>.md`를 생성/갱신하고, (2) 이번 변경에 대한 **change-scoped 검증 항목**을 도출해 fragment의 `## 검증 항목` 섹션에 기록하고, (3) 갱신된 상세설계서 파일들을 `tactical-archive/<스프린트 버전>/`에 그대로 스냅샷한다. **버전·tag·`CHANGELOG.md`는 이 단계에서 다루지 않는다** — 릴리스(`dev:release`)가 fragment를 fold하고 tag한다. fragment의 코드 변경·마이그레이션 섹션은 `dev:implement` 종료 단계가 채운다. (설계: `docs/stages/release-stage.md`)

스프린트 버전 산정 (자동):
- **스프린트 키** = 현재 워크트리 식별자. 메인 트리면 `main`, linked 워크트리면 그 워크트리명. (런타임 자원 격리 키와 동일 — `plugins/dev/agents/local-service-deployer.md` 인스턴스 격리)
- **forked-from** = 직전 릴리스 버전. 최신 git tag(`vX.Y.Z`)를 기준으로 한다. tag가 없으면(미릴리스) `v0.0.0`을 base로 본다
- **스프린트 버전** = `{forked-from의 X.Y.Z}-{스프린트 키}` (예: `1.4.0-add-discount`)
- 갱신된 상세설계서 목록과 각 파일의 버전 (각 writer가 보고한 파일 목록과 메타데이터의 `> 버전`을 그대로 종합)
- 스프린트 목표: 설계서에서 추출. 추출 불가 시 결정 요청

**검증 항목 도출 (change-scoped):**

이번 변경에서 검증할 항목을 도출하여 fragment의 `## 검증 항목` 섹션에 기록한다. **이번 스프린트에서 갱신된 상세설계서**("갱신된 상세설계서" 표의 도메인/흐름)에 한정해 도출한다 — 전체 scenarios.md가 아니라 *이번 버전에서 바뀐* 시나리오/흐름만 대상이다. 그래야 검증이 변경 범위에 집중되고, 나중에 `dev:verify`가 `tactical-archive`와 diff하지 않아도 "이 버전에서 무엇을 검증하는지"가 fragment에 박혀 있다.

> **durable 권위는 검증 원장이다.** 8단계에서 verification-criteria-writer가 작성한 `tactical/verification-ledger.md`가 완료 기준 × 면별 다중 단정(절차→관측→기대·채널) × 코더/verifier 상태 × 해소 증거의 **커밋·누적·상태보유 SoT**다(fragment처럼 릴리스에서 산문으로 fold되어 사라지지 않는다). 예전에 fragment `## 검증 항목`이 durable SoT 역할을 했으나, 이제 **원장이 이를 대체**한다 — fragment의 `## 검증 항목`은 이번 스프린트 델타를 가리키는 포인터로 축소될 수 있으며, 권위·누적·승계는 원장이 보유한다. 원장은 `tactical/` 파일이므로 아래 "상세설계서 스냅샷" 규칙에 따라 "갱신된 상세설계서" 표에 포함되어 `tactical-archive/<스프린트 버전>/verification-ledger.md`로 버전별 스냅샷이 자동 확보된다(누적 승계의 근거).

| 검증 유형 | 도출 기준 | 정보 출처 |
|----------|----------|----------|
| 도메인 검증 | 갱신된 scenarios.md가 있는 도메인 | domain/{도메인}/scenarios.md |
| cross-domain 검증 | 갱신된 cross-domain 파일 | domain/cross-domain/{흐름}.md |

각 검증 항목은 **검증 대상(시나리오/흐름) · 기대 결과 · 채널(UI/API/시스템 트리거/혼합) · 전제조건**으로 구성한다. 프론트엔드 레이어가 있는 도메인은 채널을 `UI`로 한다. (이 체크리스트는 `dev:verify`가 실행한다.)

fragment 형식 (필수 섹션·메타):

```markdown
# 스프린트: {스프린트 키}

> forked-from: v{forked-from}
> 스프린트 버전: {스프린트 버전}
> 최종 수정: {YYYY-MM-DD}

## 스프린트 목표

{스프린트 목표}

## 갱신된 상세설계서

| 파일 | 파일 버전 | 변경 |
|------|----------|------|
| tactical/{경로}.md | v{N.M.K} | {한 줄 변경 요약} |
| tactical/{삭제경로}.md | v{N.M.K} | 삭제 — {사유 한 줄} |

## 가정/결정 (dev:tactical 통합 가정 검토)

| 항목 | 가정값 | 추론 근거 |
|------|--------|----------|

## 검증 항목

| 검증 대상(시나리오/흐름) | 기대 결과 | 채널 | 전제조건 |
|------|------|------|------|
| {이번 변경에서 검증할 시나리오/흐름} | {기대 결과} | {UI/API/시스템 트리거/혼합} | {전제조건} |

<!-- 아래 두 섹션은 dev:implement가 채운다. 비워둔 채로 두며, 자리 표시만 한다. -->

## 코드 변경

(dev:implement가 채움)

## 마이그레이션

(dev:implement가 채움)
```

fragment 작성 규칙:
- 메타데이터 `> forked-from`·`> 스프린트 버전`은 필수다 (sot-catalog `file_kinds.fragment.required_metadata`). 누락 시 `check_template` FAIL.
- `## 스프린트 목표`·`## 갱신된 상세설계서`는 필수 섹션이다 (`required_sections`).
- "갱신된 상세설계서" 표의 "파일 버전" 칸은 해당 상세설계 파일 메타데이터(`> 버전`)와 정확히 같아야 한다. 불일치 시 `tactical-verifier` cross_refs `fragment_file_version_matches`가 FAIL을 낸다.
- 파일이 이번 스프린트에서 deprecated되어 tactical/ 에서 제거된 경우, "변경" 칸은 `삭제 — {사유}` 형식으로 시작한다. 삭제 행은 archive 복사 대상에서 제외되고, `fragment_lists_updated_files` / `fragment_file_version_matches` / `fragment_archive_exists` 검증 모두 자동 스킵된다. "파일 버전" 칸은 삭제 직전 마지막 파일 버전을 그대로 적는다.
- "검증 항목" 섹션은 이 단계(`dev:tactical`)가 change-scoped로 채운다. "코드 변경"·"마이그레이션" 섹션은 비워두되 헤더는 만들어 둔다 (`dev:implement`가 채울 자리).
- fragment 파일이 이미 존재하면(같은 스프린트 키) 새로 만들지 않고 "갱신된 상세설계서"·가정·검증 항목 표를 갱신한다 — 같은 스프린트의 연속 작업.

상세설계서 스냅샷 규칙:
- 대상: "갱신된 상세설계서" 표의 행 중 "변경" 칸이 `삭제`로 시작하지 않는 모든 상세설계 파일
- 위치: 각 파일을 `tactical/{나머지경로}` → `tactical-archive/{스프린트 버전}/{나머지경로}`로 그대로 복사. 디렉토리 구조 보존 (예: `tactical/domain/order/rules.md` → `tactical-archive/1.4.0-add-discount/domain/order/rules.md`)
- 시점: fragment를 파일에 쓰기 직전 또는 직후 (한 단계 안에서 함께 수행). 한 스프린트 버전 폴더는 한 번 만들고, 갱신 시 변경된 파일만 덮어쓴다
- 본문: 상세설계 파일을 그대로 복사한다. 메타데이터(`> 버전`)도 그대로 옮겨진다. archive 안의 파일은 read-only 자료로 취급하며 이후 수정하지 않는다
- 검증: 누락 시 `tactical-verifier` cross_refs `fragment_archive_exists`가 FAIL을 낸다 (archive 파일 존재 + 메타 `> 버전`이 fragment의 "파일 버전"과 일치하는지)

## 12단계: 최종 보고

모든 상세설계서 생성이 완료되면 아래 내용을 보고한다.

- 생성/갱신된 상세설계서 전체 목록 (검증 원장 `tactical/verification-ledger.md` 포함)
- 도메인별 요약 (규칙 수, 엔티티 수, 시나리오 수, 화면 수)
- cross-domain 흐름 목록
- 검증 원장 요약 (AC블록 수 = design.md 완료 기준 1:1 커버, 면별 단정 수·채널 분포(1~5)·N-A 수, 통합 seam 커버, 누적 승계 항목 수, `계약 미결` 마커 수)
- 통합 가정 검토 결과 (확정된 가정 수, 사용자 수정으로 결정된 항목 수)
- **재사이클 상한 도달 노드** (있으면 노드명 + 잔여 위반 목록. 없으면 "없음"으로 명시 — 생략하지 않는다)
- **실제 관측 동시성** (프론티어별 계획 동시 N 대비 실제로 한 메시지에 동시 위임된 노드 수. 계획보다 낮게 흘렀으면 그 사유)
- 적용된 컨벤션 목록과 상세설계서에 박힌 결정값 요약
- fragment 기록 내용 (스프린트 버전, `changelog.d/` 경로, 스냅샷한 `tactical-archive/<스프린트 버전>/`)
- 사용자 결정 요청 호출 횟수 (자율 모드 효과 확인용)

# 원칙

- 에이전트가 반환될 때마다 다음 순서를 따른다: (1) 현재 단계의 결과를 기록한다 (2) 워크플로우상 다음 행동을 판단한다 (3) 실행한다. 진행 상태는 사용자가 항상 확인할 수 있어야 한다
- 에이전트에 다시 일을 시킬 때는 **새 호출(재spawn)**로 진행한다 — "같은 에이전트를 이어서"가 아니다(세션 기반 resume에 의존하지 않음). 잃으면 안 되는 맥락(답변·결정·FAIL 항목)은 run-state escalation 로그 + 상세설계 경로를 템플릿에 담아 전달하고, 에이전트는 tactical/ 파일에서 맥락을 회복한다
- 이 스킬은 오케스트레이션만 담당한다. 상세설계서를 직접 작성하지 않는다
- 모든 상세설계서 작성은 전문 에이전트에 위임한다
- 에이전트에게 위임할 때 반드시 템플릿을 사용한다. 템플릿 외의 내용을 추가하지 않는다
- 설계서의 **내용**을 프롬프트에 포함하지 않는다. 경로와 **참조 범위(섹션 앵커)**만 전달한다 — 앵커는 "어디를 보라"는 좌표이지 내용의 사본이 아니다. 요약·발췌를 실어 보내면 그 요약이 권위 문서를 대체하기 시작해 SoT가 무너지므로 하지 않는다. 앵커를 특정할 수 없으면 비워 보내고, writer가 전체를 훑게 둔다
- 각 writer 위임 템플릿에 `결정론 체크 스크립트: ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py`를 포함한다 — writer가 반환 전 self-verify(자기 도메인 `--domain` 스코프)로 결정론 위반을 스스로 해소하게 한다(예방 → 9단계 검증 재사이클 최소화)
- 자율 진행을 우선한다. 상세설계 단계에서 사용자에게 mid-cycle로 묻지 않는다 — 못 정한 것은 가정(릴리스 사후) 또는 ⓪설계 bubble-up이다

# 상세설계 단계의 흐름 이탈 지점 (참고)

- 작성 중: writer가 가정 불가 필수 결정/상위 모순을 `{blocker}`로 반환하면 사용자가 아니라 **⓪`dev:design`으로 bubble-up**한다 (사람 결정이 필요하면 거기 설계 게이트에서)
- 8단계: 검증 원장 writer가 완료 기준 부재/상위 모순을 `{blocker}`로 반환하면 ⓪`dev:design`으로 bubble-up (완료 기준은 설계 소유)
- 9단계: tactical-verifier 위반은 **결정론 재사이클**이다 (Stage 1·Stage 2 FAIL 모두 writer 재위임으로 자동 수정, 원장 위반이면 verification-criteria-writer 재위임, 경계 문제면 ⓪설계 bubble-up)
- 10단계: **없음** — 가정은 비차단 누적(릴리스 노트 fold). 개발자 검토 게이트 아님
- 11단계: 버전/스프린트 목표가 자동 결정 불가일 때만
- 모든 단계: 진행 불가 반환 시

도메인 N개에서 bubble-up이 0건이면, 상세설계 단계는 사용자 호출 없이 완주한다 (사람 검토 게이트는 ⓪설계 하나).

# 금지사항

- 작성 호출 시점에 사용자에게 미리 확인을 받지 않는다 (자율 모드의 본질을 깨는 행위)
- 에이전트가 자율로 결정 가능한 것을 bubble-up으로 강제하지 않는다
- 서브에이전트가 `{blocker}`(상위 모순/가정 불가 필수 결정)를 반환하면 직접 답하거나 자체 판단하지 않고 **⓪`dev:design`으로 bubble-up**한다. 진행 불가 반환은 사용자에게 보고한다
- 설계서를 해석하여 상세설계서 세부사항을 결정하지 않는다
- 에이전트에게 구체적인 상세설계서 내용을 지시하지 않는다
- 가정 누적(10단계)을 생략하지 않는다 — 가정은 fragment `## 가정/결정`에 기록되어야 릴리스 노트로 fold된다 (단, 개발자 검토 게이트는 걸지 않는다)
- 정합성 검증 단계를 생략하지 않는다

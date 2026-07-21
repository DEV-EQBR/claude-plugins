# run-state 규약 (오케스트레이터 외부 상태 저장소)

오케스트레이터의 **작업 상태**(plan·진행·결정 로그·보유 버전)를 컨텍스트가 아니라 파일에 두어, 컴팩션·세션 종료를 넘어 **이어서 진행**할 수 있게 한다. 각 단계 스킬(`dev:run`·`design`·`상세설계`·`implement`·`verify`·`release`)이 이 규약을 따른다.

> 설계 배경: 산출물(tactical/·fragment·tactical-archive)은 외부화돼 있었으나 오케 *작업 상태*는 컨텍스트에만 있었다. run-state는 그 빈자리를 메운다. (`docs/harness-design.md` §6)

## 1. 위치 · 키 · 수명

- 위치: **`.dev/<스프린트 버전>/`** (워크트리당 1개). 키 = `<forked-from>-<워크트리키>` — fragment·tactical-archive와 동일 좌표(시작 시점에 결정론적으로 알려짐).
- gitignore 대상(working 상태, deliverable 아님). 같은 머신 세션 간에는 디스크에 남아 재개에 쓰인다.
- 수명: run 시작 시 생성 → **해당 스프린트가 릴리스되면 폴더째 정리**(consolidate 없이 삭제 — outcome은 fragment·CHANGELOG에 이미 남음).

### env-state — deployer 소유, 인스턴스 레벨 (run-state와 구분)

배포 환경 상태는 오케 진행 상태(run-state)와 **별개**다:

| | run-state | env-state |
|---|---|---|
| 위치 | `.dev/<스프린트 버전>/` | **`.dev/env-state.md`** (인스턴스=워크트리당 1개) |
| 담는 것 | 오케 단계/단위 진행 | 떠 있는 인프라·서비스·포트·검증DB·health·**개발 진단 로그 조회 명령** |
| 키 | 스프린트 버전(per-sprint) | 인스턴스=워크트리(per-instance, 스프린트 넘어 지속) |
| 소유 | 각 단계 오케 | **deployer** (쓰고, 다음 deploy가 읽어 재사용 판단) |
| 수명 | 스프린트 릴리스 시 정리 | 워크트리 teardown 시 정리 |

같은 워크트리의 여러 스프린트가 같은 인프라를 재사용하므로 env-state는 인스턴스 레벨이다. deployer 동작은 `plugins/dev/agents/local-service-deployer.md` "환경 SoT 소비 + 재사용".

## 2. 소유 = 오케스트레이션 소유 (재귀)

각 오케스트레이터는 **자기가 관장하는 것의 상태만** 소유·기록한다. 소유 = 파일 경계.

```
.dev/<스프린트 버전>/
├─ pipeline.md      ← dev:run 소유 (큰 줌: 단계 진행 · 보유 vX.Y.Z · cross-stage 결정)
├─ design.md        ← dev:design 소유
├─ tactical.md          ← dev:tactical 소유
├─ implement.md     ← dev:implement 소유
├─ verify.md        ← dev:verify 소유
└─ release.md       ← dev:release 소유
```

**중첩(nesting)**: 한 단계 오케가 하위 오케로 나뉘면 하위 폴더로 재귀한다 — 하위 오케가 자기 파일을 소유.

```
├─ implement.md           ← dev:implement (이 단계 큰 줌)
└─ implement/
    ├─ order.md           ← order 하위 오케 소유
    └─ payment.md         ← payment 하위 오케 소유
```

**실행 shape(병렬/중첩)는 그 단계 오케가 판단**해 `## 계획`에 기록한다(고정 설계 아님). run-state는 어떤 shape든 위 재귀 구조로 담는다.

## 3. 파일 틀 — 계획 → 추적

각 파일은 고정 스키마가 아니라 **"오케가 시작 시 결론낸 계획 + 그 계획의 진행 추적"**이다.

```markdown
# <단계> run-state
> 소유: dev:implement
> 최종 갱신: <갱신 시 stamp>

## 계획            (이 단계 오케가 시작 시 결론낸 것)
- 실행 shape: 병렬 (order·payment 독립) | 중첩 | 순차   ← 병렬이면 프론티어 배치(§6.3)
- 프로세스·단위: order×be, order×fe, payment×be (의존: order→payment)
- 프론티어별 동시 N: F1 = 2 동시(order×be, payment×be) → F2 = 1(order×fe)   ← 매 프론티어 = 한 메시지에 동시 위임할 노드 수

## 진행            (start/done 마커 — §4)
- order×be:   시작 ✓  끝 ✓
- order×fe:   시작 ✓           ← 끝 없음 = 진행 중(멈춘 지점)
- payment×be: (미시작)

## escalation 로그  (결정 요청·FAIL의 과정 — 값이 아니라 과정)
| # | 시점 | 질문/FAIL | 받은 답변/조치 | 반영 |
```

`pipeline.md`(dev:run)는 `## 계획` 대신 `## 단계 진행`(design·상세설계·implement·verify·release 각각 start/done) + `> 보유 vX.Y.Z` + `## cross-stage 결정` + `## 경계 대조`.

**`## 경계 대조`(pipeline.md 전용)**: `dev:run`이 각 경계 전환 직전 실행한 결정론 대조 게이트(`run_all.py --boundary <경계>`)의 결과를 경계별로 기록한다 — 경계(tactical/implement/verify/release) · 실행 시점 · PASS/위반 수 · (위반 시) 위반 요약. 이는 "각 경계가 닫혔나"의 신뢰되는 체크포인트다(진행 상태의 권위 — §6). 게이트가 검사하는 *내용*의 권위는 커밋된 원장(`tactical/verification-ledger.md`)이며, 여기엔 게이트 발화 결과만 둔다.

```markdown
## 경계 대조   (각 경계 전환 전 run_all.py --boundary <경계> 결과)
| 경계 | 시점 | 결과 | 위반 요약 |
|------|------|------|-----------|
| tactical  | <stamp> | PASS(위반 0) | — |
| implement | <stamp> | 위반 2 | AC-3 T4·T5 코더 미종결(L5) |
```

## 4. 쓰기 규율 — start/done 마커

신뢰성은 런타임이 아니라 **이 규율**이 보장한다. 마커는 **진행 추적용이지 순차 강제용이 아니다** — 아래는 배치(프론티어) 위임을 허용한다.

- **위임하기 직전**: `시작 ✓` 마커를 쓴다. 프론티어를 한 메시지에 동시 위임할 때는 **그 프론티어의 모든 노드에 `시작 ✓`를 한꺼번에** 찍고 → 한 메시지로 다 위임한다.
- **완료·확인된 직후**: `끝 ✓` 마커를 쓴다. 배치로 던진 노드는 **반환되는 대로 개별로** 끝 ✓(먼저 돌아온 것부터).
- per-node "시작 → 하나 위임 → 대기 → 끝 → 다음 하나"의 원자 리듬을 **강제하지 않는다** — 그 리듬이 병렬 가능한 노드를 순차(동시성 1)로 흘려보내므로, 프론티어 배치에서는 시작 ✓를 묶어 찍고 fan-out한다(§6.3 프론티어 배치, `docs/harness-design.md`).
- 단계 경계(단계 전체 완료): `dev:run`이 `pipeline.md`의 단계 진행을 전진시킨다.
- escalation 발생 시 질문을 즉시, 답변 수령 시 즉시 로그에 쓴다.

→ "시작 있고 끝 없음" = 그 작업이 멈춘 지점. 작고 원자적으로 쓰되, **배치 시작 ✓는 fan-out을 막지 않게 한꺼번에** 쓴다.

## 5. 복원 — 마커로 자동 재개

각 스킬의 **0단계(현재 상태 확인)**가 수행한다:

1. 자기 소유 파일을 읽는다(없으면 새 run → 생성).
2. **start/done 마커로 멈춘 지점을 판정**:
   - 모든 항목 `끝 ✓` → 다음 항목/다음 단계로.
   - `시작 ✓` 있고 `끝` 없음 → 그 항목을 **재실행**(재위임). 재위임 handoff 팩 = escalation 로그의 답변 + 파일 경로(에이전트가 tactical/·코드에서 맥락 회복).
3. **멈춘 지점이 확인되면 개발자에게 묻지 않고 그대로 재개한다.** (마커가 모순·손상돼 *모호*할 때만 예외로 보고.)
4. 단, **결정 게이트(L3 결정 요청·가정 검토)는 재개와 무관하게 개발자에게** — 이건 resume이 아니라 본래 의사결정이다.

## 6. 권위 경계

- run-state는 **진행 상태의 권위**("어디까지 왔나" — 신뢰되는 체크포인트)다.
- **내용의 권위는 아티팩트**(tactical/·fragment·코드·git·tag)다. run-state는 내용을 담지 않는다.
- 따라서 **결정 *과정*은 run-state(escalation 로그), 결정된 *값*은 fragment**(`## 가정/결정`)에 — `dev:tactical`이 outcome을 fragment로 옮긴다.
- **검증 원장은 run-state가 아니라 커밋된 아티팩트다.** 검증 원장(`tactical/verification-ledger.md` — 완료 기준 × 3면 검증 항목·상태·해소 증거)은 검증 *내용의 권위*라 `tactical/`에 산다(살아있는 누적 산출물, 커밋·`tactical-archive/<버전>/`로 스냅샷). run-state(`.dev/<스프린트 버전>/verify.md`)에는 이 run의 *진행 상태*(어느 AC까지 실행했나)만 두며, 원장 자체는 두지 않는다 — `.dev`는 gitignore·릴리스 시 삭제이므로 원장을 거기 두면 보류/미결 AC행이 스프린트마다 소실돼 누적 승계가 깨진다. 진행(transient, `.dev`)과 내용(durable, `tactical/`)을 이렇게 나눈다.

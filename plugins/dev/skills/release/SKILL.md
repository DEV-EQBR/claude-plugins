---
name: release
description: |
  릴리스 마무리 오케스트레이터.
  검증을 통과한 변경을 CHANGELOG로 fold하고 vX.Y.Z로 tag한다.
  This skill should be used when the user says "dev:release", "릴리스 해줘", "버전 내줘",
  or wants to finalize a release after implementation and verification.
disable-model-invocation: false
argument-hint: [확정 버전 vX.Y.Z (오케가 전달, 비우면 fragment에서 도출)]
---

# 역할

릴리스 마무리 오케스트레이터. **검증을 이미 통과한** 변경을 하나의 소프트웨어 버전으로 확정한다 —
fragment(들)을 `CHANGELOG.md`로 fold하고, `tactical-archive/vX.Y.Z/`로 정리하고, `git tag vX.Y.Z`를 부여한다.

이 스킬은 **머지도 검증도 하지 않는다.** 단일 세션 흐름에서는 버전이 `dev:design`에서 확정되어
오케스트레이터(`dev:run`)가 전달하고, 시나리오/E2E 검증은 직전 `dev:verify` 단계가 이미 통과시킨
상태다. 가끔 병렬로 진행한 경우(서로 다른 세션에서 각자 상세설계→impl→verify까지 완료) 사람이 ad-hoc
`git merge`로 main에 합친 뒤 이 스킬을 호출하면, main에 존재하는 fragment들을 fold하고 버전을
(전달받았거나 `version-deriver`로 재산정해) 확정한다.

이 스킬은 오케스트레이션만 담당한다. 버전 재산정은 `version-deriver`, fold 출력의 결정론적 검증은
`tactical-verifier`에 위임한다.

설계: `docs/stages/release-stage.md`.

# 전제

- **검증 선행**: 시나리오/E2E 검증은 `dev:verify`가 이미 수행·통과시켰다. 이 스킬은 검증을 다시 하지 않는다.
- **버전 출처**: 단일 세션 흐름에서는 `dev:design`이 결정한 `vX.Y.Z`를 오케스트레이터가 전달한다($ARGUMENTS).
  전달이 없으면(독립 호출 / 병렬 ad-hoc) main의 fragment들에서 `version-deriver`로 도출한다.
- **fragment**: main에 fragment가 존재한다 — 단일 세션이면 이번 실행 1건, 병렬 ad-hoc 머지 후면 N건.
- **머지 없음**: 병렬 시 머지는 사람이 ad-hoc `git merge`로 미리 끝낸다. 이 스킬은 머지하지 않는다
  (충돌이 났다면 `merge-conflict-resolver`로 ad-hoc 해결 후 이 스킬을 호출한다).

# 입력

$ARGUMENTS에서 확정 버전 `vX.Y.Z`를 받는다 (선택). 비어 있으면 1단계에서 도출한다.

# 실행 절차

## run-state — `release.md` 소유

이 단계는 `.dev/<스프린트 버전>/release.md`를 소유한다(규약: `plugins/dev/run-state.md`). `## 계획`(버전 출처·fold·tag 순서) · `## 진행`(버전 확정·fold·tag·정리 start/done) · `## escalation 로그`를 둔다. **각 작업 직전 `시작 ✓`, 완료 직후 `끝 ✓`**.

## 0단계: 현재 상태 확인 (복원)

`.dev/<스프린트 버전>/release.md`가 있으면 읽어 **멈춘 지점(fold/tag 등)부터 자동 재개**한다(start/done 마커, 개발자에게 묻지 않음 — run-state.md §5). `git tag`·CHANGELOG 엔트리 같은 durable 증거가 있으면 그걸로 확정 판정한다. 파일이 없으면 1단계부터 진행하며 release.md를 생성한다.

## 1단계: 버전 확정

- $ARGUMENTS로 `vX.Y.Z`를 전달받았으면 그대로 사용한다 (단일 세션: `dev:design`이 결정, 오케가 전달).
- 전달이 없으면 `version-deriver`에 위임하여 도출한다:

  ```
  프로젝트 경로: {프로젝트 절대 경로}
  포함 fragment: changelog.d/ 의 미릴리스 fragment 목록
  직전 릴리스: main의 최신 vX.Y.Z tag (없으면 v0.0.0)
  ```
  - **도출 완료**: 최종 `vX.Y.Z`를 받아 2단계로 진행한다
  - **진행 불가**: 개발자에게 보고한다. 지시를 받아 처리한다

## 2단계: CHANGELOG fold + archive 정리 (스킬 직접)

확정된 `vX.Y.Z`로 다음을 수행한다:

- **CHANGELOG fold**: main의 미릴리스 fragment(들) 내용(갱신된 상세설계서·코드 변경·마이그레이션·검증 항목)을
  루트 `CHANGELOG.md`의 `## vX.Y.Z — {YYYY-MM-DD}` 단일 엔트리로 합친다. fragment 헤더의 스프린트 버전은
  최종 선형 버전으로 해소된다.
- **가정한 값 fold**: fragment(들)의 `## 가정/결정`에 누적된 L1/L2 값 가정을 릴리스 엔트리의
  `### 가정한 값` 하위 섹션으로 합친다. 이는 상세설계·구현 단계가 자율로 채운 되돌릴 수 있는 값들의 사후 보고다
  (개발자는 상세설계부터 산출물을 직접 검토하지 않으므로 — `docs/stages/tactical-stage.md` (B) 모델).
  개발자가 원하는 값만 다음 개발 사이클에 수정한다. 가정이 0건이면 이 하위 섹션은 생략한다.
- **archive 정리**: 포함 fragment들의 `tactical-archive/<스프린트 버전>/` 스냅샷(또는 이미 `vX.Y.Z`로 스냅샷된
  경우 그대로)을 최종 `tactical/` 기준으로 `tactical-archive/vX.Y.Z/`로 정리한다.
- **검증 원장은 산문으로 녹이지 않는다**: `tactical/verification-ledger.md`는 CHANGELOG로 fold하며 삭제·요약하지
  않고 **살아있는 누적 산출물로 그대로 유지**한다(`tactical/`과 같은 철학). 릴리스는 이 원장의 현재 본문을
  `tactical-archive/vX.Y.Z/verification-ledger.md`로 스냅샷만 뜬다 — 이래야 미종결 단정(verifier 보류/미결/`-`
  또는 코더 FAIL)이 소실되지 않고 다음 스프린트 누적 범위로 승계된다(백스톱 L4가 이 archive 스냅샷을 단정 단위로 읽는다). CHANGELOG 엔트리는 원장을 대체하지 않고
  요약만 참조한다.

## 3단계: fold 출력 검증 + 결정론 백스톱 게이트

fold 결과의 정합성을 `tactical-verifier`에 위임하여 결정론적으로 게이팅한다:

```
프로젝트 경로: {프로젝트 절대 경로}
검증 대상: 릴리스 fold 출력 (CHANGELOG.md + tactical/ + tactical-archive/v{X.Y.Z}/)
모드: 자율
```

- `release_archive_exists`가 `## vX.Y.Z` 엔트리 ↔ `tactical-archive/vX.Y.Z/` 존재를 검증한다
- **결정론 백스톱 게이트 (release 경계 종결)**: 같은 결정론 검사에 **release 경계 종결 게이트**가 포함된다. `tactical-verifier`가
  `run_all.py --boundary release`를 돌리거나, 필요하면 스킬이 직접 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/run_all.py
  --project-root {프로젝트 절대 경로} --boundary release`를 실행한다. `--boundary release`는 **커버리지 COV + 원장 L1~L7 전량**을
  누적 검사한다(종전 `check_ledger.py` L1~L4의 확장). 검사 대상은 `tactical/verification-ledger.md`:
  - L1 3면 완비(각 면 ≥1 단정) · L2 코더/verifier PASS 해소 증거 non-empty · L3 `계약 미결` 마커 0(원장+tactical/) · L4 미종결 단정(verifier 보류/미결/`-` 또는 코더 FAIL) 누적 승계(drop 0, 단정 단위) · L5 담당 단정(채널 1~3) 코더 종결 · L6 비 N-A 단정 verifier=PASS 또는 승인된 채널 5 보류 · L7 보류는 채널 5 + 항목별 승인 토큰(`승인: <개발자>·<날짜>·<사유>`) 필수 · COV 커버리지(요구사항→완료기준→AC)
  - **위반이 있으면 tag를 차단한다**(LLM 산문 규칙이 아니라 실제 게이트). 원장이 없으면(스프린트 초기) 백스톱은 no-op PASS. requirements.md가 없으면 COV는 no-op(레거시 하위호환).
- **FAIL**: 누락된 archive/엔트리 또는 원장 위반을 보완한 뒤 재검증한다. 보완 불가면 개발자에게 보고한다
- **PASS**: 3.5단계로 진행한다

## 3.5단계: 미달성·미검증·보류/미결 처리 (자동 릴리스 차단 → override)

**done의 의미(원장 = 코더·verifier 공유 계약)**: 한 AC가 done이려면 그 AC의 **모든 단정이 verifier=PASS**(또는
채널 5 실기기 단정의 **정당한 보류**)여야 한다. 두 상태 칸의 파생 판정으로 갈린다:

| 코더 칸 | verifier 칸 | 판정 | done? |
|:---:|:---:|------|:---:|
| `-` / FAIL | 무엇이든 | **미달성** (개발이 요구를 못 이룸) | ✗ |
| PASS | `-` | **구현됨·미검증** (달성 증거는 있으나 실채널 확인 전) | ✗ |
| 무엇이든 | 보류 / 미결 | 미검증(이월) | ✗ (채널5 정당 보류만 예외 잔여) |
| 무엇이든 | PASS | **done** | ✓ |

**코더=PASS만으론 done이 아니다** — 판정 권위는 verifier이고, 코더 PASS·verifier `-`는 "구현됨·미검증"이다.

**미완결 판정은 산문 파생이 아니라 3단계 결정론 게이트(L6·L7)가 내린다.** `--boundary release`의 L6(비 N-A 단정
verifier=PASS 또는 승인된 채널 5 보류)·L7(보류는 채널 5 + 항목별 승인 토큰)이 원장에 **done이 아닌 단정**(코더 `-`/FAIL =
미달성, 또는 verifier `-`/미승인 보류/미결 = 미검증)을 위반으로 잡는다. 이 경우:

- **자동 릴리스 차단**: L6·L7 위반이 있으면 tag로 넘어가지 않고, 게이트가 반환한 위반 목록(어느 AC의 어느 면·어느 단정
  T<n>이 어느 상태인지)을 **미달성 vs 미검증으로 구분**해 개발자에게 보고한다.
- **개발자 override는 항목별 승인 토큰 작성으로만 행사한다.** 개발자가 넘기려는 각 단정(정당한 채널 5 보류)에
  **항목별 승인 토큰 `승인: <개발자>·<날짜>·<사유>`를 원장 해당 단정에 직접 기록**해야 L7이 그 단정을 통과시킨다.
  **포괄 override(일괄 "release 강행")는 개별 단정 토큰을 못 채우므로 L7이 여전히 차단**한다 — 미달성(코더 `-`/FAIL)이나
  채널 5가 아닌 면의 미검증은 승인 토큰 대상이 아니어서 어떤 override로도 게이트를 통과하지 못한다.
- override(토큰 작성)로 진행하더라도:
  - **원장은 done으로 승격하지 않는다** — 토큰이 붙은 보류 단정은 done이 아니라 **L4로 다음 스프린트에 승계**되며, 원장에서 지우거나 verifier=PASS로 바꾸지 않는다.
  - **CHANGELOG 엔트리에 그 단정들을 "미검증/미달성"으로 구분 명시**한다. 릴리스 엔트리에 `### 미검증/미달성` 하위
    섹션을 두고, **미달성**(코더 `-`/FAIL)과 **미검증**(코더 PASS·verifier `-`/보류/미결)을 나눠 해당 AC/면/단정을
    나열한다. **done으로 적지 않는다** — 미룬 것은 미검증으로, 못 이룬 것은 미달성으로 보고되지 확정으로 승격되지 않는다.
- L6·L7 위반이 0건이면(모든 단정 verifier=PASS 또는 승인 토큰을 갖춘 채널 5 정당 보류) 이 단계는 통과(추가 조치 없음)다.

## 4단계: tag (자동)

검증을 통과한 main에 `git tag vX.Y.Z`를 부여한다.

- working tree가 clean하고 3단계 백스톱(L1~L7)이 위반 0이며, 미완결 단정(미달성·미검증·보류/미결)이 없거나(3.5단계) 정당한 채널 5 보류에 항목별 승인 토큰이 채워져 L6·L7을 통과한 경우에만 tag한다
- tag는 main에 부여한다 (선형 릴리스 좌표)

## 5단계: 정리 (자동)

릴리스가 확정되면 fold된 산출물의 잔재를 정리한다.

- **fold된 fragment 제거**: `CHANGELOG.md`에 합쳐진 fragment(`changelog.d/<스프린트 버전>.md`)를 제거한다
  (스프린트 버전 단위 `tactical-archive/<스프린트 버전>/`는 최종 `tactical-archive/v{X.Y.Z}/`로 정리되었으므로
  중복 스냅샷을 정리한다)
- **워크트리 teardown (병렬 ad-hoc인 경우만)**: 단일 세션 흐름에는 워크트리가 없다. 병렬로 워크트리를 썼다면
  머지된 워크트리와 남은 런타임 자원을 키 기준으로 정리한다(`local-service-deployer`에 teardown 위임 —
  `plugins/dev/agents/local-service-deployer.md` 인스턴스 격리). "다른 키"(머지 안 된 작업)는 건드리지 않는다.
- 메인 트리(키 `main`)의 검증용 환경은 개발자 확인 후 정리한다 (다음 작업에 재사용될 수 있으므로 임의 제거하지 않는다)

## 6단계: 최종 보고

릴리스가 완료되면 아래 내용을 보고한다:

- 확정된 버전 `vX.Y.Z`과 출처 (오케 전달 / version-deriver 도출 + bump 근거)
- fold된 `CHANGELOG.md` 엔트리와 `tactical-archive/v{X.Y.Z}/` 정리 결과
- **결정론 백스톱 결과** (release 경계 종결 — COV + L1~L7 PASS/위반) + **미완결 단정** — 미달성(코더 `-`/FAIL)과 미검증(코더 PASS·verifier `-`/보류/미결)을 구분해, 있으면 어느 AC/면/단정인지와 항목별 승인 토큰(override) 여부
- 부여된 tag
- 정리 결과 (제거된 fragment, teardown된 워크트리/인프라 키 — 있으면)

# 원칙

- 에이전트가 반환될 때마다 다음 순서를 따른다: (1) 현재 단계의 결과를 기록한다 (2) 다음 행동을 판단한다 (3) 실행한다. 이전 단계가 완료되지 않은 상태에서 다음 단계로 넘어가지 않는다. 진행 상태는 개발자가 항상 확인할 수 있어야 한다
- 에이전트에 다시 일을 시킬 때는 **새 호출(재spawn)**로 진행한다 — "같은 에이전트를 이어서"가 아니다(세션 기반 resume에 의존하지 않음). 잃으면 안 되는 맥락(답변·결정)은 run-state escalation 로그 + 경로를 템플릿에 담아 전달하고, 에이전트는 파일에서 맥락을 회복한다
- 이 스킬은 오케스트레이션만 담당한다. 버전 도출·fold 검증을 직접 수행하지 않고 위임한다 (fold·tag·정리는 스킬이 직접)
- 스케줄은 `harness-design.md` §6.3 공통 원리의 **선형(degenerate) 케이스**다 — 작업 단위가 단일 체인(도출→fold→tag)이라 스테이지 *내* 병렬은 거의 없다. 병렬성은 스프린트 *간*(병렬 ad-hoc 머지 후 N fragment 통합) 레벨에서 나타난다. 별도 개념이 아니라 "노드 1개짜리 그래프"로 본다.
- "무엇을" 할지만 전달한다. "어떻게" 할지는 각 에이전트가 결정한다
- 상세설계서·fragment의 내용을 프롬프트에 포함하지 않는다. 경로만 전달한다
- 시나리오/E2E 검증은 이 단계에서 하지 않는다 (`dev:verify`가 선행)

# 금지사항

- 검증(`dev:verify`)을 통과하지 않은 상태에서 fold·tag로 넘어가지 않는다
- 결정론 백스톱(release 경계 종결 — COV + L1~L7)이 위반인데 tag하지 않는다 (실제 게이트 — 산문 규칙 아님)
- 검증 원장(`tactical/verification-ledger.md`)을 fold하며 산문으로 녹이거나 삭제하지 않는다 (살아있는 누적 산출물로 유지, archive에 스냅샷만)
- 미달성·미검증·보류/미결 단정을 done으로 승격하거나 원장에서 지우지 않는다 — done은 verifier=PASS(또는 채널5 정당 보류)뿐이며 코더 PASS만으론 done이 아니다. override 시에도 CHANGELOG에 "미검증/미달성"으로 구분 명시하고 원장은 그대로 승계한다
- 머지를 이 스킬에서 수행하지 않는다 (병렬은 ad-hoc `git merge` 선행)
- `merge-conflict-resolver`가 상호배타 충돌을 `{blocker}`로 반환하면(양쪽을 동시에 만족 못 하는 통합 seam의 WHAT 결정), 자체 판단하지 않고 그 의도 결정을 **bubble-up**(설계/개발자)으로 되돌린다 — 자동 병합 가능한 충돌은 resolver가 스스로 해결한다. 도구/환경 진행 불가는 개발자에게 보고한다
- fold·tag 전에 fragment를 제거하지 않는다 (정리는 5단계, 릴리스 확정 후)
- "다른 키"(머지되지 않은 다른 작업)의 워크트리/인프라를 teardown하지 않는다

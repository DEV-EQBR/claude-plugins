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
fragment(들)을 `CHANGELOG.md`로 fold하고, `spec-archive/vX.Y.Z/`로 정리하고, `git tag vX.Y.Z`를 부여한다.

이 스킬은 **머지도 검증도 하지 않는다.** 단일 세션 흐름에서는 버전이 `dev:design`에서 확정되어
오케스트레이터(`dev:run`)가 전달하고, 시나리오/E2E 검증은 직전 `dev:verify` 단계가 이미 통과시킨
상태다. 가끔 병렬로 진행한 경우(서로 다른 세션에서 각자 spec→impl→verify까지 완료) 사람이 ad-hoc
`git merge`로 main에 합친 뒤 이 스킬을 호출하면, main에 존재하는 fragment들을 fold하고 버전을
(전달받았거나 `version-deriver`로 재산정해) 확정한다.

이 스킬은 오케스트레이션만 담당한다. 버전 재산정은 `version-deriver`, fold 출력의 결정론적 검증은
`spec-verifier`에 위임한다.

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

- **CHANGELOG fold**: main의 미릴리스 fragment(들) 내용(갱신된 명세서·코드 변경·마이그레이션·검증 항목)을
  루트 `CHANGELOG.md`의 `## vX.Y.Z — {YYYY-MM-DD}` 단일 엔트리로 합친다. fragment 헤더의 스프린트 버전은
  최종 선형 버전으로 해소된다.
- **가정한 값 fold**: fragment(들)의 `## 가정/결정`에 누적된 L1/L2 값 가정을 릴리스 엔트리의
  `### 가정한 값` 하위 섹션으로 합친다. 이는 명세·구현 단계가 자율로 채운 되돌릴 수 있는 값들의 사후 보고다
  (개발자는 명세부터 산출물을 직접 검토하지 않으므로 — `docs/stages/input-stage.md` (B) 모델).
  개발자가 원하는 값만 다음 개발 사이클에 수정한다. 가정이 0건이면 이 하위 섹션은 생략한다.
- **archive 정리**: 포함 fragment들의 `spec-archive/<스프린트 버전>/` 스냅샷(또는 이미 `vX.Y.Z`로 스냅샷된
  경우 그대로)을 최종 `spec/` 기준으로 `spec-archive/vX.Y.Z/`로 정리한다.

## 3단계: fold 출력 검증 (결정론적)

fold 결과의 정합성을 `spec-verifier`에 위임하여 결정론적으로 게이팅한다:

```
프로젝트 경로: {프로젝트 절대 경로}
검증 대상: 릴리스 fold 출력 (CHANGELOG.md + spec/ + spec-archive/v{X.Y.Z}/)
모드: 자율
```

- `release_archive_exists`가 `## vX.Y.Z` 엔트리 ↔ `spec-archive/vX.Y.Z/` 존재를 검증한다
- **FAIL**: 누락된 archive/엔트리를 보완한 뒤 재검증한다. 보완 불가면 개발자에게 보고한다
- **PASS**: 4단계로 진행한다

## 4단계: tag (자동)

검증을 통과한 main에 `git tag vX.Y.Z`를 부여한다.

- working tree가 clean하고 3단계 검증이 PASS인 경우에만 tag한다
- tag는 main에 부여한다 (선형 릴리스 좌표)

## 5단계: 정리 (자동)

릴리스가 확정되면 fold된 산출물의 잔재를 정리한다.

- **fold된 fragment 제거**: `CHANGELOG.md`에 합쳐진 fragment(`changelog.d/<스프린트 버전>.md`)를 제거한다
  (스프린트 버전 단위 `spec-archive/<스프린트 버전>/`는 최종 `spec-archive/v{X.Y.Z}/`로 정리되었으므로
  중복 스냅샷을 정리한다)
- **워크트리 teardown (병렬 ad-hoc인 경우만)**: 단일 세션 흐름에는 워크트리가 없다. 병렬로 워크트리를 썼다면
  머지된 워크트리와 남은 런타임 자원을 키 기준으로 정리한다(`local-service-deployer`에 teardown 위임 —
  `plugins/dev/agents/local-service-deployer.md` 인스턴스 격리). "다른 키"(머지 안 된 작업)는 건드리지 않는다.
- 메인 트리(키 `main`)의 검증용 환경은 개발자 확인 후 정리한다 (다음 작업에 재사용될 수 있으므로 임의 제거하지 않는다)

## 6단계: 최종 보고

릴리스가 완료되면 아래 내용을 보고한다:

- 확정된 버전 `vX.Y.Z`과 출처 (오케 전달 / version-deriver 도출 + bump 근거)
- fold된 `CHANGELOG.md` 엔트리와 `spec-archive/v{X.Y.Z}/` 정리 결과
- 부여된 tag
- 정리 결과 (제거된 fragment, teardown된 워크트리/인프라 키 — 있으면)

# 원칙

- 에이전트가 반환될 때마다 다음 순서를 따른다: (1) 현재 단계의 결과를 기록한다 (2) 다음 행동을 판단한다 (3) 실행한다. 이전 단계가 완료되지 않은 상태에서 다음 단계로 넘어가지 않는다. 진행 상태는 개발자가 항상 확인할 수 있어야 한다
- 에이전트에 다시 일을 시킬 때는 **새 호출(재spawn)**로 진행한다 — "같은 에이전트를 이어서"가 아니다(세션 기반 resume에 의존하지 않음). 잃으면 안 되는 맥락(답변·결정)은 run-state escalation 로그 + 경로를 템플릿에 담아 전달하고, 에이전트는 파일에서 맥락을 회복한다
- 이 스킬은 오케스트레이션만 담당한다. 버전 도출·fold 검증을 직접 수행하지 않고 위임한다 (fold·tag·정리는 스킬이 직접)
- "무엇을" 할지만 전달한다. "어떻게" 할지는 각 에이전트가 결정한다
- 명세서·fragment의 내용을 프롬프트에 포함하지 않는다. 경로만 전달한다
- 시나리오/E2E 검증은 이 단계에서 하지 않는다 (`dev:verify`가 선행)

# 금지사항

- 검증(`dev:verify`)을 통과하지 않은 상태에서 fold·tag로 넘어가지 않는다
- 머지를 이 스킬에서 수행하지 않는다 (병렬은 ad-hoc `git merge` 선행)
- 서브에이전트가 결정 요청·진행 불가를 반환한 경우, 직접 답변하거나 자체 판단하지 않고 개발자에게 전달한다
- fold·tag 전에 fragment를 제거하지 않는다 (정리는 5단계, 릴리스 확정 후)
- "다른 키"(머지되지 않은 다른 작업)의 워크트리/인프라를 teardown하지 않는다

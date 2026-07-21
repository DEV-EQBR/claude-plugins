# SoT 카탈로그 해설

이 문서는 `sot-catalog.json`의 사람용 해설이다. 카탈로그 자체는 JSON이라 코멘트를 담을 수 없으므로, 의도·제약·결정 근거는 본 파일에 둔다.

> 카탈로그를 수정할 때는 본 README도 함께 갱신한다. 둘은 plugin 갱신 단위로 같이 움직인다.

## 카탈로그의 역할

`tactical-verifier` 에이전트가 상세설계서를 deterministic하게 검증할 때 참조하는 **검증 기준 데이터**다. 작성과 검증을 무상관으로 분리하는 것이 패턴의 핵심이고, 카탈로그는 그 무상관성을 보장하는 외부 기준이다.

## 메타 원칙: 검증 룰은 작성 가이드와 1:1 정렬되어야 한다

> **새 검증 룰을 추가하거나 기존 룰을 수정할 때, 대응하는 작성 가이드(컨벤션·writer 에이전트 정의·템플릿)의 강제 수준이 같아야 한다.** 작성 가이드가 형식을 강제하지 않는데 검증만 형식을 강제하면, 의미적으로 정합인 상세설계서가 false positive로 떨어진다 — 이 비대칭은 패턴의 무상관성을 깨뜨린다.

구체 운용 원칙:

- 작성 가이드에 표기 형식이 명시되지 않은 항목은 검증도 형식을 강제하지 않는다. (예: `> 버전:` 값 — 컨벤션에 `v` 접두사 강제가 없으면 정규식 강제 금지)
- 작성 에이전트가 의미 매핑(예: `entities.md X.Y` 같은 권위 참조)으로 정합성을 확보하는 항목은, 검증도 의미 매핑 추적으로 검증한다. 권위 매핑이 가리키는 대상이 실재하는지만 본다 — 문자열 비교(타입 표기 alias 매칭 등)는 작성 추상화 수준과 다르므로 금지.
- 작성 가이드에 enum이 정의되지 않은 항목은 검증도 enum 매칭을 강제하지 않는다. enum이 있어야 한다면 먼저 작성 가이드 보강 → 그 다음 검증 도입.
- 단/복수형·자연어 변형 같은 패턴은 작성 가이드에 룰이 없으면 검증도 자연어 동치를 인정한다.
- 본질이 다른 항목(예: hotfix vs 정기 엔트리)은 같은 룰로 일률 강제하지 않는다 — 본질별 분기 또는 본질별 면제.

이 원칙을 따르지 않은 룰을 발견하면 그 룰의 폐지·완화·작성 가이드 보강 중 하나로 정렬해야 한다 (위반을 통과시키기 위한 카탈로그 변경은 별개 — 그건 여전히 금지).

검증 범주는 8가지로 잡혀 있고, 각 범주가 카탈로그의 특정 키 묶음을 사용한다:

| 범주 | 사용 키 | 현재 구현 |
|------|---------|----------|
| (1) 템플릿 적합성 | `file_kinds.*.required_sections`, `required_metadata` | check_template.py |
| (2) 링크 무결성 | `links` | 미구현 |
| (3) Cross-reference 정합성 | `cross_refs` | 미구현 |
| (4) 용어 일관성 | `glossary` | 미구현 |
| (5) 스키마 유효성 | `metadata_schemas` | 미구현 |
| (6) 타입·포맷 정합성 | `type_consistency` | 폐지 — cross_refs.api_field_authority_entity로 일원화 |
| (7) 커버리지 | `coverage` | 미구현 |
| (8) 유일성 | `uniqueness` | 미구현 |
| (9) 검증 원장 백스톱 (L1~L4) + 경계 종결 게이트 (L5~L7) | `verification_ledger` | check_ledger.py |
| (12) 경계 커버리지 (요구사항→완료기준→원장 AC) | `traceability` | check_traceability.py |
| (13) 개발 진단 로그 선언 (system.md 검증 환경 컨벤션 ↔ "개발 진단 로그" 결정 항목) | `dev_diagnostic_log` | check_dev_log.py |

## file_kinds 작성 규약

상세설계서 파일 종류별 정의. 각 항목은 다음 키를 갖는다.

| 키 | 설명 |
|----|------|
| `path` | 단일 경로 (`tactical/system.md` 같은 단일 파일 케이스) |
| `path_glob` | 경로 패턴 (`tactical/domain/*/rules.md` 같은 반복 케이스) |
| `excluded_subdirs` | path_glob 매칭 시 제외할 하위 디렉토리 이름 (예: `cross-domain`) |
| `excluded_files` | path_glob 매칭 시 제외할 파일명 (예: `screens.md`) |
| `optional` | true 면 파일이 없어도 위반 아님 (선택적 파일) |
| `required_sections` | `## ` 레벨 섹션 제목 목록. 순서는 강제하지 않음 |
| `required_metadata` | 파일 상단 인용 블록(`> 키: 값`)의 키 목록 |
| `sot_for` | 이 파일이 SoT인 사실 도메인 (다른 체크가 cross-reference 시 참조) |

## 단일 path vs path_glob

- 단일 `path`: 파일이 항상 1개 존재해야 함을 의미한다 (optional이 아닐 때). 예: `system.md` (루트 단일).
- `path_glob` (스프린트 fragment 등): 매칭된 파일들에 대해 검사한다. 예: `fragment` = `changelog.d/*.md`.
- `path_glob`: 매칭된 파일들에 대해 검사한다. 0건 매칭 자체는 위반이 아니며, 이는 (7) 커버리지 영역에서 별도 처리한다.

## fragment (스프린트 변경 SoT)

스프린트는 변경 내용을 `CHANGELOG.md`(릴리스 전용)가 아니라 **스프린트 fragment** `changelog.d/<스프린트 버전>.md`에 쌓는다. 스프린트마다 분리 파일이라 동시(병렬) 워크플로우에서도 충돌하지 않는다. 최종 버전·`CHANGELOG.md` fold·tag는 릴리스(`dev:release`)가 fragment(들)을 fold하여 수행한다(단일 세션이면 1건, 병렬 ad-hoc 머지 후면 N건). (설계: `docs/stages/release-stage.md`)

스프린트 버전 = `<forked-from>-<스프린트 키>` (예 `1.4.0-add-discount`). forked-from = 직전 릴리스(최신 git tag), 스프린트 키 = 워크트리명(메인=`main`).

fragment 표준:

```
# 스프린트: add-discount

> forked-from: v1.4.0
> 스프린트 버전: 1.4.0-add-discount
> 최종 수정: 2026-05-01

## 스프린트 목표
...

## 갱신된 상세설계서
| 파일 | 파일 버전 | 변경 |
| tactical/domain/approval/rules.md | v1.3.0 | ... |
| tactical/domain/legacy/old.md | v0.5.2 | 삭제 — deprecated, approval로 통합 |

## 가정/결정 (dev:tactical 통합 가정 검토)
| 항목 | 가정값 | 추론 근거 |

## 검증 항목
| 검증 대상(시나리오/흐름) | 기대 결과 | 채널 | 전제조건 |

<!-- 아래는 dev:implement가 채움 -->

## 코드 변경
- backend/...: ...

## 마이그레이션
- 1743900000000-UpdateApprovalDuplicateIndex.ts
```

작성·확장 규칙:

- **필수 메타**: `> forked-from`·`> 스프린트 버전`. 누락 시 `check_template`이 FAIL (`file_kinds.fragment.required_metadata`)
- **필수 섹션**: `## 스프린트 목표`·`## 갱신된 상세설계서` (`file_kinds.fragment.required_sections`)
- **상세설계 섹션 채움**: `dev:tactical` 9단계가 메타·스프린트 목표·갱신된 상세설계서·가정/결정·검증 항목(change-scoped) 섹션을 작성한다
- **code 섹션 채움**: `dev:implement` 종료 단계가 코드 변경·마이그레이션 섹션을 같은 fragment에 추가한다 (헤더·상세설계 섹션·검증 항목 섹션은 그대로 둔다). 버전·tag·`CHANGELOG.md`는 다루지 않는다 (릴리스 영역). 검증은 `dev:verify`가 같은 세션에서 검증 항목을 실행한다
- **갱신된 상세설계서 표의 "파일 버전"**: 해당 상세설계 파일 상단 메타데이터의 `> 버전` 값과 정확히 같아야 한다. `cross_refs.fragment_file_version_matches`가 검증
- **갱신된 상세설계서 표의 "파일" 경로**: 실제 존재해야 한다. `cross_refs.fragment_lists_updated_files`가 검증
- **삭제 행**: 파일이 이번 스프린트에서 deprecated되어 tactical/ 에서 제거된 경우, "변경" 칸은 `삭제 — {사유}` 형식으로 시작한다. 삭제 행은 archive 스냅샷 대상이 아니며, `fragment_lists_updated_files` / `fragment_file_version_matches` / `fragment_archive_exists` 검증이 모두 자동 스킵된다. "파일 버전" 칸은 삭제 직전 마지막 파일 버전을 그대로 적는다. 삭제 마커는 `cross_refs.fragment_archive_exists.deletion_marker_prefix`에 정의되어 있다
- **버전 문자열 정규화**: `fragment_file_version_matches` / `fragment_archive_exists`의 버전 비교는 `v` 접두사를 무시하고 동치 판단한다 (`1.50.0` ↔ `v1.50.0`). 작성 가이드가 `v` 접두사를 강제하지 않으므로 검증도 강제하지 않는다 (메타 원칙: 검증↔작성 1:1 정렬)

## tactical-archive (파일별 버전 본문 보관소)

각 상세설계 파일의 과거 본문은 tactical/ 자체에는 남지 않는다 (항상 HEAD만 보관). 대신 `dev:tactical` 9단계가 **스프린트 버전 단위**로 "그 시점에 갱신된 파일들"의 본문을 그대로 복사하여 `tactical-archive/<스프린트 버전>/` 트리에 둔다. fragment가 (스프린트 버전 ↔ 파일 버전) 인덱스 역할을 하므로, 어떤 파일의 어떤 파일 버전이 어느 archive 폴더에 있는지는 fragment에서 역추적할 수 있다. (릴리스 시 최종 버전 `tactical-archive/v{X.Y.Z}/`로 정리하는 것은 `dev:release` 영역)

레이아웃:

```
tactical/
  domain/approval/rules.md            > 버전: v1.3.0   (현재)

tactical-archive/
  1.4.0-add-discount/
    domain/approval/rules.md          > 버전: v1.3.0   (이 스프린트에서 박힌 본문)
  1.4.0-fix-auth/
    domain/auth/rules.md              > 버전: v1.2.1
```

규칙:

- **경로 매핑**: 상세설계 파일 `tactical/{나머지경로}` → archive `tactical-archive/<스프린트 버전>/{나머지경로}`. 디렉토리 구조 그대로 유지
- **복사 시점·대상**: `dev:tactical` 9단계, fragment의 "갱신된 상세설계서" 표 작성과 같은 단계에서 수행. 표의 행 중 "변경" 칸이 `삭제`로 시작하는 행은 복사 대상에서 제외 (마지막 본문은 그 직전 archive 폴더에 남아 있는 셈)
- **갱신**: 한 스프린트 버전 폴더는 한 번 만들고, 갱신 시 변경된 파일만 덮어쓴다. archive 안의 파일은 read-only 자료로 취급하며 이후 수정하지 않는다
- **스냅샷 본문 메타**: archive 본문 상단의 `> 버전:` 메타데이터는 상세설계 파일을 그대로 복사한 결과이므로, fragment 표의 "파일 버전" 칸과 자동으로 일치한다. 불일치 시 `cross_refs.fragment_archive_exists`가 FAIL을 낸다
- **검증 영향 없음**: `file_kinds.*` 의 path/path_glob은 `tactical/...` 또는 `changelog.d/...`를 가리키므로 `tactical-archive/...` 트리는 자연 제외된다. 별도 excluded_subdirs 지정 불필요

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| fragment 필수 섹션·메타 | `file_kinds.fragment.required_sections` / `required_metadata` | `check_template.py` |
| 갱신된 상세설계서 경로 존재 | `cross_refs.fragment_lists_updated_files` | `check_cross_refs.py` |
| 갱신된 상세설계서 파일 버전 일치 | `cross_refs.fragment_file_version_matches` | `check_cross_refs.py` |
| tactical-archive 스냅샷 존재 + 메타 일치 | `cross_refs.fragment_archive_exists` | `check_cross_refs.py` |

## release_changelog (릴리스 fold SoT) — 검증의 sprint/release 분리

스프린트와 릴리스는 검증 시점이 다르다. 스프린트 시점엔 fragment를, 릴리스 시점엔 fold된 `CHANGELOG.md`를 본다. (설계: `docs/stages/release-stage.md` §5)

| 시점 | 검증 | 카탈로그 |
|------|------|---------|
| **sprint** (tactical-verifier) | fragment의 "갱신된 상세설계서 ↔ 각 상세설계 파일 버전" 일치 + 스프린트 버전 키 archive 존재 | `fragment_lists_updated_files` / `fragment_file_version_matches` / `fragment_archive_exists` |
| **release** | fold된 `CHANGELOG.md` 릴리스 엔트리(`## v{X.Y.Z}`)마다 최종 `tactical-archive/v{X.Y.Z}/` 존재 | `release_archive_exists` |

- `dev:release`이 선택 스프린트들을 머지하고 fragment들을 `CHANGELOG.md`에 fold하면서 `tactical-archive/<스프린트 버전>/`을 `tactical-archive/v{최종}/`으로 정리한다. `release_archive_exists`는 그 결과물(엔트리 ↔ 최종 archive)의 정합성을 릴리스 시점에 게이팅한다.
- **CHANGELOG.md는 optional**이다 (`file_kinds.release_changelog.optional=true`). 스프린트 진행 중인 프로젝트엔 아직 `CHANGELOG.md`가 없으므로, release 체크는 자연히 no-op이 되고 `check_template`도 파일 부재를 위반으로 보지 않는다. 첫 릴리스 후부터 검증이 활성화된다.
- **버전 헤더 추출**은 `cross_refs.release_archive_exists.version_header_pattern`(첫 캡처 그룹이 `X.Y.Z`)으로 한다. 패턴에 매칭되지 않는 `##` 헤더(예 `Unreleased`)는 릴리스 엔트리가 아니므로 검증 대상에서 제외된다.
- **버전 디렉토리 정규화**: `tactical-archive/v{X.Y.Z}/`와 `tactical-archive/{X.Y.Z}/`(v 접두사 없음)를 모두 인정한다. 작성 가이드가 `v` 접두사를 강제하지 않으므로 검증도 강제하지 않는다 (메타 원칙: 검증↔작성 1:1 정렬).

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| fold 엔트리 ↔ 최종 archive 존재 | `cross_refs.release_archive_exists` | `check_cross_refs.py` |

## requirements (요구사항 추적 산출물) — 커버리지 상류

요구사항 추적 산출물 `design/requirements.md`은 `design.md`의 형제로 커밋되는 **살아있는 누적 문서**다. `domain-architect`가 `design/_input/`의 개발자 원본(요구사항 서술)을 소화해 각 요구사항에 `R-<n>` ID를 부여하고 `### R-<n>: <서술>` + `> 상태: {active | 승계 vX.Y.Z | released}`로 적는다. 이것이 경계 커버리지 체인(요구사항 → 완료 기준 → 원장 AC)의 **상류**다.

- **file_kind**: `file_kinds.requirements`(`path`=`design/requirements.md`, `optional=true`). 부재 시 `check_template`이 위반으로 보지 않고 **traceability·종결 게이트가 전부 no-op**이 된다(레거시·초기 스프린트 하위호환).
- **채택 스위치**: `requirements.md`가 **존재하면** 팀이 추적을 채택한 것으로 보고, `design.md` `## 완료 기준` 표에 **AC·요구사항 칼럼을 요구**한다(없으면 `check_traceability` 위반).
- **라이브 규율**: `requirements.md`도 **현재 상태만** 담는다 — 릴리스로 그 요구사항의 전 AC가 done되면 본문에서 **제거(졸업)**하고 이력은 `tactical-archive/<버전>/` 스냅샷이 보유한다. 델타 이력·취소선을 본문에 쌓지 않는다(`design.md`·원장과 동일 철학).
- **유일성**: `uniqueness`에 `R-<n>` 스코프(`requirement_id`, 패턴 `\bR-\d+\b`, `in: requirements`)가 있어 R-n ID 중복을 막는다.

## verification_ledger (검증 원장 백스톱) — 릴리스 게이트

검증 원장 `tactical/verification-ledger.md`은 **커밋된 살아있는 누적 아티팩트**다(`tactical/`과 같은 철학 — `.dev`가 아니라 커밋된 SoT). 스프린트마다 델타로 항목을 쌓되 릴리스에서 산문으로 녹여 없애지 않고, `tactical-archive/<버전>/verification-ledger.md`로 버전 스냅샷된다. 보류·미결 항목이 다음 스프린트로 승계되는 근거가 여기 산다. (근거: `docs/요구사항-집행-수정안.md` §4 백스톱·§5)

원장 스키마 (v2 — 면별 다중 단정 + 코더/verifier 2칸):

- AC블록 = `## AC-<n>: ...` (level 2 헤더)
- 각 AC블록에 면별 다중 단정 테이블 `| 면 | 단정 | 채널 | 코더 | verifier | 해소 증거 |`
- 면 ∈ {`UI/UX`, `로직`, `데이터`}, 각 면 ≥1행 (해당없으면 단정 칸 `N-A + 사유`)
- 단정 = `T<n>` + 절차→관측→기대(사용자가 보는 결과 기준·관찰 가능). 채널 ∈ {`1 정적구조`, `2 로직단위`, `3 계약API`, `4 정적스크린샷`, `5 실기기`}(싼→비싼 사다리)
- 코더 칸 = 코더 달성 상태 ∈ {`PASS`, `FAIL`, `-`, `N/A`}(채널 4·5=코더 `N/A` 구현시점 불가, `-`=미착수). verifier 칸 = verifier 확인 상태 ∈ {`PASS`, `FAIL`, `보류`, `미결`, `-`}
- 파생 판정(칸 아님, 두 칸의 조합): 코더=`-`/`FAIL`→미달성 / 코더=`PASS`·verifier=`-`→구현됨·미검증 / verifier=`PASS`→done / verifier=`FAIL`→회귀
- 경계 계약 타입 미확정은 단정/상태 칸에 `계약 미결` 마커
- **하위호환**: 옛 5컬럼 `| 면 | 검증 항목 | 채널 | 상태 | 해소 증거 |`(단일 상태) 원장도 파싱한다 — 헤더에 `코더` 컬럼이 없으면 옛 스키마로 보고 단일 `상태` 칸을 verifier 칸으로 매핑, 코더 칸은 생략. 컬럼 라벨 감지 + 위치 폴백

`check_ledger.py`가 7개 결정론 불변식을 게이트로 검사한다. **L1~L4는 항상**(릴리스 태그 게이트) 발화하고, **종결 게이트 L5~L7은 `run_all.py --boundary {implement|verify|release}`에서만** 발화한다(작성 시점 빈 칸 오탐 방지 — `--boundary` 없이 돌리면 L1~L4만). 미달성·미검증·미결/보류가 명시적 해소 증거 없이 조용히 "됨"으로 승격되는 걸 구조로 차단한다.

| 룰 | 레벨 | 발화 | 검사 |
|----|------|------|------|
| `verification_ledger_facets_complete` | L1 완비 | 항상 | 각 AC블록에 UI/UX·로직·데이터 3면이 전부(각 면 ≥1행) 존재. 면이 N-A인 행은 단정 칸에 `N-A` 뒤 사유 텍스트가 있어야(빈 N-A 금지 — 프론트 통과로 백엔드·데이터를 추론하는 드리프트 차단) |
| `verification_ledger_pass_evidence` | L2 PASS 무결성 | 항상 | 코더 또는 verifier 칸이 PASS인 행은 해소 증거 칸이 non-empty. 빈칸/`-`이면 위반 — "초록 숫자"가 증거 없이 done으로 집계되는 걸 막는다 |
| `contract_unresolved_zero` | L3 계약미결 0 | 항상 | 원장 **및 `tactical/` 트리** 어디에도 `계약 미결` 마커가 남아 있지 않음. 경계 계약 타입은 확정 또는 escalate하되 암묵 방치 금지(A-3) |
| `verification_ledger_carryforward` | L4 누적 승계 | 항상 | 직전 버전 archive 원장에서 미종결이던 단정(verifier ∈ {`보류`, `미결`, `-`} 또는 코더 = `FAIL`)이 현재 원장에 여전히 존재(drop 0). 단정 단위(`T<n>`) 판정, 옛 스키마는 `(AC-<n>, 면)` 단위 폴백. 미해소 단정이 릴리스에서 조용히 사라지는 걸 막는다 |
| `verification_ledger_coder_closure` | L5 코더 종결 | implement 이상 | 코더가 닫는 채널(1 정적구조·2 로직단위·3 계약API)이고 N-A가 아닌 단정의 코더 칸이 미착수(`-`)·보류로 남으면 위반. 미구현 항목이 구현 경계를 조용히 통과하는 걸 차단. 채널4(정적스크린샷)·5(실기기)는 코더 면제 — verifier가 L6로 닫는다. 직전 스프린트 승계 블록(승계≠신규)은 면제 |
| `verification_ledger_verifier_closure` | L6 verifier 종결 | verify 이상 | N-A가 아닌 단정의 verifier 칸이 PASS(+증거)이거나 승인된 채널5 보류가 아니면(=`-`·미결·FAIL) 위반. 미검증이 release로 통과하는 걸 차단. 승계 블록은 PASS 강제 면제(부채는 L4·L7) |
| `verification_ledger_hold_approved_debt` | L7 보류=승인된 부채 | verify 이상 | verifier=`보류`인 단정은 (채널5 실기기) ∧ (사유 텍스트) ∧ (해소 증거 칸에 **항목별 승인 토큰** `승인: <개발자>·<날짜>·<사유>`) 셋을 모두 만족해야 통과. 포괄 사전승인이 개별 단정 토큰을 못 채우면 여전히 차단 — 통째 면제 통로를 막는다 |

운용 규약:

- **원장 부재 시 no-op PASS**: 스프린트 초기엔 원장이 없을 수 있다. 원장 파일이 없으면 L1~L4 전체가 위반 없는 PASS로 처리된다(`file_kinds`에는 등록하지 않아 `check_template`이 부재를 위반으로 보지 않는다).
- **전역 전용(GLOBAL_ONLY)**: 원장은 전역 산출물이라 도메인별 위반으로 나눌 수 없다. `run_all.py --domain {도메인}` 로컬 스코프에선 이 체크를 skip한다(전량 필터링돼 무의미하므로).
- **직전 버전 판정**: `tactical-archive/` 하위 **순수 semver 디렉토리**(`v?X.Y.Z`)의 최신값을 직전 버전으로 본다. `1.4.0-add-discount` 같은 스프린트 버전 키 디렉토리는 대상이 아니다(`release_archive_exists`와 같은 v 접두사 무관 규약). semver 디렉토리가 없거나 그 안에 원장 스냅샷이 없으면 L4는 no-op.
- **단정 생성은 writer, 상태 갱신은 코더·verifier**: 원장의 단정(무엇을 검증)은 설계·상세설계(verification-criteria-writer)가 소유하고 초기 코더/verifier 칸을 `-`로 둔다. **코더**는 채널 1~3 단정을 구현시점에 통과 증명하며 코더 칸 + 증거를 갱신하고(채널 4·5는 코더 N/A로 verify에 넘김), `dev:verify`의 **verifier**는 독립 실채널 확인으로 verifier 칸(PASS/보류/증거)을 갱신한다(판정 권위는 verifier). 원장 = 코더·verifier 공유 계약. 이 체크는 그 원장의 결정론 불변식만 게이팅한다.
- **라벨 SoT**: 면·컬럼(`면`·`단정`·`채널`·`코더`·`verifier`·`해소 증거`)·코더/verifier 상태·채널 라벨과 `계약 미결` 마커는 카탈로그의 `verification_ledger`에 SoT로 두고, 원장 writer 템플릿과 정확히 같아야 한다(메타 원칙: 검증↔작성 1:1 정렬). writer가 다른 라벨을 쓰면 카탈로그도 함께 갱신한다.

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| 3면 완비 + N-A 사유 | `verification_ledger.checks.verification_ledger_facets_complete` (L1) | `check_ledger.py` |
| PASS 해소 증거 non-empty | `verification_ledger.checks.verification_ledger_pass_evidence` (L2) | `check_ledger.py` |
| 계약 미결 마커 0 (원장+tactical/) | `verification_ledger.checks.contract_unresolved_zero` (L3) | `check_ledger.py` |
| 보류/미결 누적 승계 (drop 0) | `verification_ledger.checks.verification_ledger_carryforward` (L4) | `check_ledger.py` |
| 코더 종결 (채널1~3 미착수·보류 0, `--boundary implement` 이상) | `verification_ledger.checks.verification_ledger_coder_closure` (L5) | `check_ledger.py` |
| verifier 종결 (비N-A 단정 PASS·증거 또는 승인 보류, `--boundary verify` 이상) | `verification_ledger.checks.verification_ledger_verifier_closure` (L6) | `check_ledger.py` |
| 보류=항목별 승인 토큰 (`--boundary verify\|release`) | `verification_ledger.checks.verification_ledger_hold_approved_debt` (L7) | `check_ledger.py` |

## traceability (경계 커버리지) — 상류 전항목이 하류 목록이 됐는가

`check_traceability.py`(범주 12, GLOBAL_ONLY)는 라이브 워크플로의 세 산출물을 **ID로 조인**해 "상류 항목이 하나도 안 빠지고 하류 목록이 됐는가"를 결정론으로 강제한다. 기존 `check_cross_refs`가 "하류가 참조한 ID가 상류에 존재하나"(dangling 방지, 방향 반대)만 보던 사각을 메운다.

체인: `R-n`(요구사항, `design/requirements.md`) → 완료 기준 표(`design/design.md` `## 완료 기준`, AC·요구사항 칼럼) → `AC-n` 블록(원장 `tactical/verification-ledger.md` `## AC-n`).

| 룰 | 불변식 |
|----|--------|
| `traceability_requirement_covered` | COV-1 요구사항 커버: 상태 ∈ {`active`, `승계`}인 모든 R-n이 완료 기준 표 요구사항 칸에서 ≥1회 참조돼야 한다(미참조 = 완료 기준 없는 요구사항 = 위반) |
| `traceability_acceptance_req_exists` | COV-1b(dangling): 완료 기준 표가 참조한 R-n이 requirements.md에 실재해야 한다 |
| `traceability_acceptance_covered_by_ac` | COV-2 완료기준 커버: 완료 기준 표의 모든 AC-n이 원장에 `## AC-n` 블록으로 존재해야 한다. 원장 부재(상세설계 전)면 no-op |
| `traceability_ac_traces_to_acceptance` | COV-2b(dangling): 원장의 모든 `## AC-n`이 완료 기준 표에 존재해야 한다(원장이 완료 기준 없는 AC 발명 금지). 직전 스프린트 승계 블록(승계≠신규)은 타이밍 스큐 방지로 면제 |

운용 규약:

- **하위호환**: `requirements.md` 부재 → 전체 no-op PASS(초기·레거시 스프린트). `design.md` 부재 → no-op(`check_design`가 소유).
- **채택 스위치**: `requirements.md` 존재 = 팀 채택 = 완료 기준 표에 AC·요구사항 칼럼 필수(없으면 위반).
- **AC 소유**: `AC-n`은 **완료 기준(`domain-architect`)이 소유·부여**한다 — 하류 검증 원장은 이 ID를 **그대로 재사용**하고 새로 mint하지 않는다. 원장이 완료 기준에 없는 AC를 발명하면 COV-2b가 잡는다.
- **라이브 규율 덕의 무오탐**: 활성+승계만 보므로 릴리스된 요구사항은 라이브 집합에 없어 change-scoped 스프린트에서 오탐이 0이다.
- **의미는 사람 게이트**: R-n itemization·완료 기준이 요구사항을 진짜 담는가는 ⓪ 사람 게이트(의미)가 본다. 여기선 **ID 존재·집합 대응**만 본다.
- **설정**: 카탈로그 `traceability` 키(경로·정규식·상태·칼럼 라벨).

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| 요구사항→완료기준→원장 AC 커버리지 (COV-1/1b/2/2b) | `traceability.checks.*` | `check_traceability.py` |

## dev_diagnostic_log (개발 진단 로그 선언) — 검증 빌드가 실패를 삼키지 않는가

`check_dev_log.py`(범주 13, GLOBAL_ONLY)는 `conventions/system/local-verification.md`의 **개발 진단 로그** 결정 항목이 `tactical/system.md`의 `## 검증 환경 컨벤션`에 선언됐는지 결정론으로 확인한다. 검증 빌드는 실패를 소리 없이 삼키지 않아야 한다 — 실패 취약 이음매의 관찰 사실을 구조화 로그(`diag:<이음매> level=<lvl> …`, **사실만·판정 없음·검증 빌드 한정**, 모션 프로브와 같은 채널/조회 규약)로 관측 가능하게 해, 검증 실패 시 coder·verifier가, 개발자 실행 시 사용자가 같은 로그로 원인을 즉시 국소화하게 한다. 이 검사는 그 앞단 — **스펙이 로그를 선언했는지**만 본다(실제 코드 계측은 coder 상시 의무·verifier 소비로 강제 — 모션 프로브와 동형, 코드 계측은 결정론으로 못 잡음).

| 항목 | 내용 |
|------|------|
| **트리거 (self-consistent)** | system.md에 `## 검증 환경 컨벤션`(또는 `검증 환경 컨벤션 …` 추가분) 섹션이 있으면 = 컨벤션 적용 프로젝트 = 진단 로그 선언 필수. 그 섹션(들) 본문에 라벨 `개발 진단 로그`가 없으면 위반 (`dev_diagnostic_log_declared`) |
| **라벨/설정** | 카탈로그 `dev_diagnostic_log`(`system_path`=`tactical/system.md` · `convention_section_prefix`=`검증 환경 컨벤션` · `declaration_label`=`개발 진단 로그`). 키 부재 시 내장 기본값 |
| **하위호환 (no-op PASS)** | system.md 부재(스프린트 초기) → PASS · 검증 환경 컨벤션 섹션 부재(서비스 없는 프로젝트 등) → PASS |
| **GLOBAL_ONLY** | system.md는 전역 산출물이라 도메인별로 나눌 수 없다(ledger/traceability와 동일). `run_all.py --domain {도메인}` 로컬 스코프에선 skip |

> 제품 기능으로서의 에러 관측(사용자/어드민 대상·DB 영속·프라이버시 불변식)과는 목적·거처가 분리된다 — 후자는 제품 도메인(tactical/domain)에 살고, 전자는 이 검증 인프라 컨벤션이 소유한다.

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| 검증 환경 컨벤션에 "개발 진단 로그" 선언 존재 | `dev_diagnostic_log` (트리거·라벨·경로) | `check_dev_log.py` |

## 메타데이터 인용 블록

상세설계서 파일은 다음 형식의 인용 블록을 상단에 둔다.

```markdown
# 제목

> 버전: v1.0.0
> 최종 수정: 2026-04-01
```

`required_metadata`에 적힌 키가 인용 블록에 모두 존재해야 한다. 키 형식과 값 형식의 추가 검증은 (5) 스키마 유효성 체크 영역에서 본다.

## 카탈로그 변경 원칙

- 검증 통과를 위해 카탈로그를 수정하지 않는다. 카탈로그는 plugin 갱신 단위로만 변경한다.
- file_kinds에 새 파일 종류를 추가하면 dev:tactical의 writer 출력과 정합해야 한다 — writer 산출물에 없는 섹션을 required로 두면 모든 검증이 실패한다.
- regex 패턴은 JSON 이스케이프 규칙을 따른다 (`\\d`, `\\.` 등 백슬래시 두 번).

## 향후 확장

- 사용자 프로젝트별 오버라이드: 미래에 `tactical/.sot-overrides.json` 같은 형태로 일부 항목을 프로젝트가 보강할 수 있게 한다 (현재 미지원).
- 카탈로그 분할: 8개 영역이 커지면 영역별 파일로 분리하고 메인 카탈로그가 include 한다.

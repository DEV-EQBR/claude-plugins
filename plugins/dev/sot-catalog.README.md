# SoT 카탈로그 해설

이 문서는 `sot-catalog.json`의 사람용 해설이다. 카탈로그 자체는 JSON이라 코멘트를 담을 수 없으므로, 의도·제약·결정 근거는 본 파일에 둔다.

> 카탈로그를 수정할 때는 본 README도 함께 갱신한다. 둘은 plugin 갱신 단위로 같이 움직인다.

## 카탈로그의 역할

`spec-verifier` 에이전트가 명세서를 deterministic하게 검증할 때 참조하는 **검증 기준 데이터**다. 작성과 검증을 무상관으로 분리하는 것이 패턴의 핵심이고, 카탈로그는 그 무상관성을 보장하는 외부 기준이다.

## 메타 원칙: 검증 룰은 작성 가이드와 1:1 정렬되어야 한다

> **새 검증 룰을 추가하거나 기존 룰을 수정할 때, 대응하는 작성 가이드(컨벤션·writer 에이전트 정의·템플릿)의 강제 수준이 같아야 한다.** 작성 가이드가 형식을 강제하지 않는데 검증만 형식을 강제하면, 의미적으로 정합인 명세서가 false positive로 떨어진다 — 이 비대칭은 패턴의 무상관성을 깨뜨린다.

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

## file_kinds 작성 규약

명세서 파일 종류별 정의. 각 항목은 다음 키를 갖는다.

| 키 | 설명 |
|----|------|
| `path` | 단일 경로 (`spec/system.md` 같은 단일 파일 케이스) |
| `path_glob` | 경로 패턴 (`spec/domain/*/rules.md` 같은 반복 케이스) |
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

## 갱신된 명세서
| 파일 | 파일 버전 | 변경 |
| spec/domain/approval/rules.md | v1.3.0 | ... |
| spec/domain/legacy/old.md | v0.5.2 | 삭제 — deprecated, approval로 통합 |

## 가정/결정 (dev:spec 통합 가정 검토)
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
- **필수 섹션**: `## 스프린트 목표`·`## 갱신된 명세서` (`file_kinds.fragment.required_sections`)
- **spec 섹션 채움**: `dev:spec` 9단계가 메타·스프린트 목표·갱신된 명세서·가정/결정·검증 항목(change-scoped) 섹션을 작성한다
- **code 섹션 채움**: `dev:implement` 종료 단계가 코드 변경·마이그레이션 섹션을 같은 fragment에 추가한다 (헤더·spec 섹션·검증 항목 섹션은 그대로 둔다). 버전·tag·`CHANGELOG.md`는 다루지 않는다 (릴리스 영역). 검증은 `dev:verify`가 같은 세션에서 검증 항목을 실행한다
- **갱신된 명세서 표의 "파일 버전"**: 해당 spec 파일 상단 메타데이터의 `> 버전` 값과 정확히 같아야 한다. `cross_refs.fragment_file_version_matches`가 검증
- **갱신된 명세서 표의 "파일" 경로**: 실제 존재해야 한다. `cross_refs.fragment_lists_updated_files`가 검증
- **삭제 행**: 파일이 이번 스프린트에서 deprecated되어 spec/ 에서 제거된 경우, "변경" 칸은 `삭제 — {사유}` 형식으로 시작한다. 삭제 행은 archive 스냅샷 대상이 아니며, `fragment_lists_updated_files` / `fragment_file_version_matches` / `fragment_archive_exists` 검증이 모두 자동 스킵된다. "파일 버전" 칸은 삭제 직전 마지막 파일 버전을 그대로 적는다. 삭제 마커는 `cross_refs.fragment_archive_exists.deletion_marker_prefix`에 정의되어 있다
- **버전 문자열 정규화**: `fragment_file_version_matches` / `fragment_archive_exists`의 버전 비교는 `v` 접두사를 무시하고 동치 판단한다 (`1.50.0` ↔ `v1.50.0`). 작성 가이드가 `v` 접두사를 강제하지 않으므로 검증도 강제하지 않는다 (메타 원칙: 검증↔작성 1:1 정렬)

## spec-archive (파일별 버전 본문 보관소)

각 spec 파일의 과거 본문은 spec/ 자체에는 남지 않는다 (항상 HEAD만 보관). 대신 `dev:spec` 9단계가 **스프린트 버전 단위**로 "그 시점에 갱신된 파일들"의 본문을 그대로 복사하여 `spec-archive/<스프린트 버전>/` 트리에 둔다. fragment가 (스프린트 버전 ↔ 파일 버전) 인덱스 역할을 하므로, 어떤 파일의 어떤 파일 버전이 어느 archive 폴더에 있는지는 fragment에서 역추적할 수 있다. (릴리스 시 최종 버전 `spec-archive/v{X.Y.Z}/`로 정리하는 것은 `dev:release` 영역)

레이아웃:

```
spec/
  domain/approval/rules.md            > 버전: v1.3.0   (현재)

spec-archive/
  1.4.0-add-discount/
    domain/approval/rules.md          > 버전: v1.3.0   (이 스프린트에서 박힌 본문)
  1.4.0-fix-auth/
    domain/auth/rules.md              > 버전: v1.2.1
```

규칙:

- **경로 매핑**: spec 파일 `spec/{나머지경로}` → archive `spec-archive/<스프린트 버전>/{나머지경로}`. 디렉토리 구조 그대로 유지
- **복사 시점·대상**: `dev:spec` 9단계, fragment의 "갱신된 명세서" 표 작성과 같은 단계에서 수행. 표의 행 중 "변경" 칸이 `삭제`로 시작하는 행은 복사 대상에서 제외 (마지막 본문은 그 직전 archive 폴더에 남아 있는 셈)
- **갱신**: 한 스프린트 버전 폴더는 한 번 만들고, 갱신 시 변경된 파일만 덮어쓴다. archive 안의 파일은 read-only 자료로 취급하며 이후 수정하지 않는다
- **스냅샷 본문 메타**: archive 본문 상단의 `> 버전:` 메타데이터는 spec 파일을 그대로 복사한 결과이므로, fragment 표의 "파일 버전" 칸과 자동으로 일치한다. 불일치 시 `cross_refs.fragment_archive_exists`가 FAIL을 낸다
- **검증 영향 없음**: `file_kinds.*` 의 path/path_glob은 `spec/...` 또는 `changelog.d/...`를 가리키므로 `spec-archive/...` 트리는 자연 제외된다. 별도 excluded_subdirs 지정 불필요

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| fragment 필수 섹션·메타 | `file_kinds.fragment.required_sections` / `required_metadata` | `check_template.py` |
| 갱신된 명세서 경로 존재 | `cross_refs.fragment_lists_updated_files` | `check_cross_refs.py` |
| 갱신된 명세서 파일 버전 일치 | `cross_refs.fragment_file_version_matches` | `check_cross_refs.py` |
| spec-archive 스냅샷 존재 + 메타 일치 | `cross_refs.fragment_archive_exists` | `check_cross_refs.py` |

## release_changelog (릴리스 fold SoT) — 검증의 sprint/release 분리

스프린트와 릴리스는 검증 시점이 다르다. 스프린트 시점엔 fragment를, 릴리스 시점엔 fold된 `CHANGELOG.md`를 본다. (설계: `docs/stages/release-stage.md` §5)

| 시점 | 검증 | 카탈로그 |
|------|------|---------|
| **sprint** (spec-verifier) | fragment의 "갱신된 명세서 ↔ 각 spec 파일 버전" 일치 + 스프린트 버전 키 archive 존재 | `fragment_lists_updated_files` / `fragment_file_version_matches` / `fragment_archive_exists` |
| **release** | fold된 `CHANGELOG.md` 릴리스 엔트리(`## v{X.Y.Z}`)마다 최종 `spec-archive/v{X.Y.Z}/` 존재 | `release_archive_exists` |

- `dev:release`이 선택 스프린트들을 머지하고 fragment들을 `CHANGELOG.md`에 fold하면서 `spec-archive/<스프린트 버전>/`을 `spec-archive/v{최종}/`으로 정리한다. `release_archive_exists`는 그 결과물(엔트리 ↔ 최종 archive)의 정합성을 릴리스 시점에 게이팅한다.
- **CHANGELOG.md는 optional**이다 (`file_kinds.release_changelog.optional=true`). 스프린트 진행 중인 프로젝트엔 아직 `CHANGELOG.md`가 없으므로, release 체크는 자연히 no-op이 되고 `check_template`도 파일 부재를 위반으로 보지 않는다. 첫 릴리스 후부터 검증이 활성화된다.
- **버전 헤더 추출**은 `cross_refs.release_archive_exists.version_header_pattern`(첫 캡처 그룹이 `X.Y.Z`)으로 한다. 패턴에 매칭되지 않는 `##` 헤더(예 `Unreleased`)는 릴리스 엔트리가 아니므로 검증 대상에서 제외된다.
- **버전 디렉토리 정규화**: `spec-archive/v{X.Y.Z}/`와 `spec-archive/{X.Y.Z}/`(v 접두사 없음)를 모두 인정한다. 작성 가이드가 `v` 접두사를 강제하지 않으므로 검증도 강제하지 않는다 (메타 원칙: 검증↔작성 1:1 정렬).

검증 책임:

| 항목 | 키 | 검사 주체 |
|------|-----|----------|
| fold 엔트리 ↔ 최종 archive 존재 | `cross_refs.release_archive_exists` | `check_cross_refs.py` |

## 메타데이터 인용 블록

명세서 파일은 다음 형식의 인용 블록을 상단에 둔다.

```markdown
# 제목

> 버전: v1.0.0
> 최종 수정: 2026-04-01
```

`required_metadata`에 적힌 키가 인용 블록에 모두 존재해야 한다. 키 형식과 값 형식의 추가 검증은 (5) 스키마 유효성 체크 영역에서 본다.

## 카탈로그 변경 원칙

- 검증 통과를 위해 카탈로그를 수정하지 않는다. 카탈로그는 plugin 갱신 단위로만 변경한다.
- file_kinds에 새 파일 종류를 추가하면 dev:spec의 writer 출력과 정합해야 한다 — writer 산출물에 없는 섹션을 required로 두면 모든 검증이 실패한다.
- regex 패턴은 JSON 이스케이프 규칙을 따른다 (`\\d`, `\\.` 등 백슬래시 두 번).

## 향후 확장

- 사용자 프로젝트별 오버라이드: 미래에 `spec/.sot-overrides.json` 같은 형태로 일부 항목을 프로젝트가 보강할 수 있게 한다 (현재 미지원).
- 카탈로그 분할: 8개 영역이 커지면 영역별 파일로 분리하고 메인 카탈로그가 include 한다.

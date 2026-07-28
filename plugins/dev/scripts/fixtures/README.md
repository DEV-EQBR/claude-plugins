# check 스크립트 회귀 fixture

deterministic check 스크립트를 검증하기 위한 최소 타겟 프로젝트들이다. 두 상태를 분리해 둔다.

- `sample-project/` — **스프린트 상태** (fragment 모델). fragment cross-ref / template 검증.
- `released-project/` — **릴리스 상태** (fold 후). `release_archive_exists` 검증.
- `traceability-adopted/` — **경계 대조 게이트** (requirements.md 채택) + **개발 진단 로그** 선언. 커버리지(COV)·종결 게이트(L5~L7)·`dev_log` 정상통과 정본.

## sample-project (스프린트 상태)

```
sample-project/
  tactical/domain/order/{rules,entities}.md   ← 상세설계 파일 (메타 '> 버전')
  changelog.d/1.4.0-add-discount.md       ← fragment (forked-from + 스프린트 버전 + '갱신된 상세설계서' 표)
  tactical-archive/1.4.0-add-discount/...      ← 스프린트 버전 키 archive 스냅샷
```

## 검증 대상 (fragment 모델)

- `fragment_lists_updated_files` — fragment '갱신된 상세설계서' 표의 상세설계 경로가 실제 존재
- `fragment_file_version_matches` — 표의 '파일 버전' ↔ 상세설계 파일 메타 '버전' 일치
- `fragment_archive_exists` — 표 행마다 `tactical-archive/<스프린트 버전>/<경로>` 존재 + 메타 일치

## 실행 / 기대 결과

```
python3 plugins/dev/scripts/check_cross_refs.py --project-root plugins/dev/scripts/fixtures/sample-project
# → status: pass, violations: []  (fragment 체크 3종 모두 통과)
```

`sample-project/` 는 **fragment 체크(`check_cross_refs`의 `fragment_*`)가 통과(violations 0)** 하도록 구성돼 있다. 실패 검출은 fragment 표의 '파일 버전'을 일부러 틀리게 하거나 `tactical-archive/` 파일을 지워서 확인할 수 있다.

이 fixture의 검증 범위는 **fragment 모델**이다. 상세설계 파일(rules/entities)은 최소 구성이라 `check_template`·`check_coverage` 등은 *fragment와 무관한* 섹션/커버리지 위반을 보고한다(system.md 부재, rules.md 필수 섹션 등) — fragment 검증 범위 밖이며 정상이다. fragment 파일 자체는 `check_template`의 required_sections/required_metadata도 통과한다. CHANGELOG.md가 없으므로 `release_archive_exists`는 no-op(릴리스 전 상태)다.

## released-project (릴리스 상태)

④`dev:release`가 fragment들을 `CHANGELOG.md`에 fold하고 `tactical-archive/v{최종}/`로 정리한 *릴리스 후* 상태다.

```
released-project/
  CHANGELOG.md                              ← fold된 릴리스 엔트리 '## v1.5.0 — ...'
  tactical/domain/order/rules.md                ← 상세설계 파일 (HEAD)
  tactical-archive/v1.5.0/domain/order/rules.md ← 최종 버전 archive 스냅샷
```

### 검증 대상 (release 모델)

- `release_archive_exists` — `CHANGELOG.md`의 `## v{X.Y.Z}` fold 엔트리마다 `tactical-archive/v{X.Y.Z}/` (또는 v 접두사 없는 `{X.Y.Z}/`) 디렉토리가 존재

```
python3 plugins/dev/scripts/check_cross_refs.py --project-root plugins/dev/scripts/fixtures/released-project
# → cross_refs: status pass  (release_archive_exists 통과)
```

실패 검출은 `tactical-archive/v1.5.0/`를 지우면 확인된다. `check_template`·`check_coverage`의 상세설계 최소구성 위반(system.md 부재 등)은 sample-project와 마찬가지로 release 검증 범위 밖이며 정상이다.

## traceability-adopted (경계 대조 게이트)

`design/requirements.md`를 채택한 상태에서 커버리지(요구사항→완료기준→원장 AC)와 종결 게이트(L5 코더·L6 verifier·L7 승인 보류)가 **정상통과**하도록 구성한 정본이다.

```
traceability-adopted/
  design/requirements.md            ← R-1·R-2 active, R-9 released(라이브 제외)
  design/design.md                  ← 완료 기준 표 | AC | 요구사항 | 완료 기준 | 3면 | (AC-1·AC-2, R-n 참조)
  tactical/verification-ledger.md   ← AC-1·AC-2 전종결(코더·verifier PASS+증거), 채널5 승인 보류 1건, AC-3 승계(v0.9.0) 면제
  tactical/system.md                ← 검증 환경 컨벤션에 '개발 진단 로그' 선언(check_dev_log 정상통과용)
```

### 검증 대상 / 기대 결과

- `check_traceability` — COV-1(요구사항 커버)·COV-2(완료기준→AC)·dangling 역검사 통과
- `check_design` — 완료 기준 AC-n·R-n·3면 셀 통과
- `check_ledger --boundary {implement|verify|release}` — 종결 게이트 통과(승인된 채널5 보류 + 승계 블록 면제)
- `check_dev_log` — system.md 검증 환경 컨벤션에 '개발 진단 로그' 선언 존재 → 통과(선언 줄을 지우면 FAIL)

```
python3 plugins/dev/scripts/check_ledger.py --project-root plugins/dev/scripts/fixtures/traceability-adopted --boundary release
python3 plugins/dev/scripts/check_traceability.py --project-root plugins/dev/scripts/fixtures/traceability-adopted
# → 둘 다 status: pass (오탐 0)
```

실패 검출: 원장 어느 단정의 verifier 칸을 `-`로 바꾸면 L6, 채널5 보류의 `승인:` 토큰을 지우면 L7, design.md 완료 기준에서 `R-2` 참조를 지우면 COV-1이 잡는다. `check_template`·`check_coverage`의 상세설계 최소구성 위반은 이 fixture 검증 범위 밖이다.

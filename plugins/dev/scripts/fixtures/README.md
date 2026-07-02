# check 스크립트 회귀 fixture

deterministic check 스크립트를 검증하기 위한 최소 타겟 프로젝트들이다. 두 상태를 분리해 둔다.

- `sample-project/` — **스프린트 상태** (fragment 모델). fragment cross-ref / template 검증.
- `released-project/` — **릴리스 상태** (fold 후). `release_archive_exists` 검증.

## sample-project (스프린트 상태)

```
sample-project/
  spec/domain/order/{rules,entities}.md   ← spec 파일 (메타 '> 버전')
  changelog.d/1.4.0-add-discount.md       ← fragment (forked-from + 스프린트 버전 + '갱신된 명세서' 표)
  spec-archive/1.4.0-add-discount/...      ← 스프린트 버전 키 archive 스냅샷
```

## 검증 대상 (fragment 모델)

- `fragment_lists_updated_files` — fragment '갱신된 명세서' 표의 spec 경로가 실제 존재
- `fragment_file_version_matches` — 표의 '파일 버전' ↔ spec 파일 메타 '버전' 일치
- `fragment_archive_exists` — 표 행마다 `spec-archive/<스프린트 버전>/<경로>` 존재 + 메타 일치

## 실행 / 기대 결과

```
python3 plugins/dev/scripts/check_cross_refs.py --project-root plugins/dev/scripts/fixtures/sample-project
# → status: pass, violations: []  (fragment 체크 3종 모두 통과)
```

`sample-project/` 는 **fragment 체크(`check_cross_refs`의 `fragment_*`)가 통과(violations 0)** 하도록 구성돼 있다. 실패 검출은 fragment 표의 '파일 버전'을 일부러 틀리게 하거나 `spec-archive/` 파일을 지워서 확인할 수 있다.

이 fixture의 검증 범위는 **fragment 모델**이다. spec 파일(rules/entities)은 최소 구성이라 `check_template`·`check_coverage` 등은 *fragment와 무관한* 섹션/커버리지 위반을 보고한다(system.md 부재, rules.md 필수 섹션 등) — fragment 검증 범위 밖이며 정상이다. fragment 파일 자체는 `check_template`의 required_sections/required_metadata도 통과한다. CHANGELOG.md가 없으므로 `release_archive_exists`는 no-op(릴리스 전 상태)다.

## released-project (릴리스 상태)

④`dev:release`가 fragment들을 `CHANGELOG.md`에 fold하고 `spec-archive/v{최종}/`로 정리한 *릴리스 후* 상태다.

```
released-project/
  CHANGELOG.md                              ← fold된 릴리스 엔트리 '## v1.5.0 — ...'
  spec/domain/order/rules.md                ← spec 파일 (HEAD)
  spec-archive/v1.5.0/domain/order/rules.md ← 최종 버전 archive 스냅샷
```

### 검증 대상 (release 모델)

- `release_archive_exists` — `CHANGELOG.md`의 `## v{X.Y.Z}` fold 엔트리마다 `spec-archive/v{X.Y.Z}/` (또는 v 접두사 없는 `{X.Y.Z}/`) 디렉토리가 존재

```
python3 plugins/dev/scripts/check_cross_refs.py --project-root plugins/dev/scripts/fixtures/released-project
# → cross_refs: status pass  (release_archive_exists 통과)
```

실패 검출은 `spec-archive/v1.5.0/`를 지우면 확인된다. `check_template`·`check_coverage`의 spec 최소구성 위반(system.md 부재 등)은 sample-project와 마찬가지로 release 검증 범위 밖이며 정상이다.

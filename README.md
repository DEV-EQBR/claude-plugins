# EQBR Claude Plugins

EQBR의 Claude Code 플러그인 마켓플레이스입니다.

## 워크플로우

워크플로우는 하나의 `dev` 플러그인에서 **한 세션에 순차로** 동작합니다. 메타 오케스트레이터 `dev:run`이 ⓪설계→①명세→②구현→③검증→④릴리스를 차례로 진행합니다.

| 단계 | 내용 | 담당 (dev 스킬) |
|------|------|------|
| ⓪ 설계 (필수) | 요구사항 → `design/design.md`(전략 설계 7섹션) + 범위 묶음 + version bump. **외부 인입도 요구사항으로 취급(skip 없음)**, 강제사항 수용. **유일한 사람 검토 게이트** | `design` (+`domain-architect`) |
| ① 명세 작성 | `design/design.md` → 구현 가능한 명세 (`spec/`) + fragment(`changelog.d/`, change-scoped 검증 항목 포함) | `spec` |
| ② 구현 (+ 단위 테스트) | 명세 → 코드 + mock 단위 테스트 | `implement` |
| ③ 검증 | 구현 직후 **같은 세션**에서 deploy + 시나리오/E2E 검증 | `verify` |
| ④ 릴리스 | `CHANGELOG.md` fold · `git tag` (버전은 ⓪/오케가 보유) | `release` |

기본은 **단일 세션 순차**입니다. 가끔 병렬이 필요하면 각 기능을 별도 `dev:run` 세션으로 돌리고 ad-hoc `git merge`로 합친 뒤 main에서 ③검증·④릴리스를 수행합니다. **검증 항목은 ①명세가 생산**(change-scoped)하고 ③검증이 실행하며, **버전은 ⓪설계가 정해 오케가 보유**합니다(명세서엔 버전 없음). ⓪의 "설계"는 아키텍처 설계입니다 — **별도의 UI/UX 디자인 스테이지는 두지 않되, 시각 디자인은 ①명세(프론트 디자인 컨벤션 → service.md 디자인 정책 + 화면별 `ui.md`)와 ③검증(UI 시각 품질 게이트)에 임베드**되어 있습니다.

## 플러그인 설치

Claude Code 터미널에서 아래 명령어를 순서대로 실행합니다.

### 1단계: 마켓플레이스 등록

```bash
/plugin marketplace add DEV-EQBR/claude-plugins
```

### 2단계: 플러그인 설치

설치 범위(scope)를 선택하여 `dev` 플러그인을 설치합니다. 기본값은 user입니다.

#### 유저 단위 설치 (기본)

내 모든 프로젝트에서 플러그인을 사용합니다. 설정이 개인 환경에 저장됩니다.

```bash
/plugin install dev@eqbr-plugins --scope user
```

#### 프로젝트 단위 설치

특정 프로젝트에서만 플러그인을 사용합니다. `.claude/settings.json`에 저장되어 팀원과 공유됩니다.

```bash
/plugin install dev@eqbr-plugins --scope project
```

#### 로컬 단위 설치

특정 프로젝트에서만 플러그인을 사용하되, 설정을 공유하지 않습니다. `.claude/settings.local.json`에 저장되며 gitignore 대상입니다.

```bash
/plugin install dev@eqbr-plugins --scope local
```

### 어떤 걸 선택해야 하나요?

| 설치 범위 | 저장 위치                     | 공유 여부         | 적합한 경우                                                |
| --------- | ----------------------------- | ----------------- | ---------------------------------------------------------- |
| user      | `~/.claude/settings.json`     | 개인              | 내가 참여하는 모든 프로젝트에서 일관되게 사용하고 싶을 때  |
| project   | `.claude/settings.json`       | 팀 공유 (git)     | 팀 프로젝트에서 팀원 모두 동일한 플러그인을 사용해야 할 때 |
| local     | `.claude/settings.local.json` | 개인 (gitignored) | 특정 프로젝트에서만 개인적으로 사용하고 싶을 때            |

## 사용 가능한 플러그인

### dev

명세 작성(spec)·구현(implement)·검증(verify)·릴리스(release)를 하나로 통합한 개발 워크플로우 플러그인입니다. **한 세션에서** ⓪설계→①명세→②구현→③검증→④릴리스를 진행합니다.

#### 사용법

```bash
/dev:run [요구사항 경로 + 개발 의도]   # 전체 파이프라인 (메타 오케)
```

단계별 개별 호출도 가능합니다:

```bash
/dev:design [요구사항]        # ⓪ 설계 (요구사항 → design/design.md + version bump)
/dev:spec   [design.md 경로]   # ① 명세 (+ change-scoped 검증 항목)
/dev:implement [명세 경로]     # ② 구현 + 단위테스트
/dev:verify                   # ③ 검증 (deploy + 시나리오/E2E)
/dev:release [vX.Y.Z]          # ④ 릴리스 (CHANGELOG fold + tag)
```

#### 워크플로우

```
dev:run (메타 오케 · 한 세션 · vX.Y.Z 보유)
├─ ⓪ dev:design  [필수]  요구사항 → design/design.md + 범위 묶음 + version bump   (외부 인입도 요구사항·강제사항으로 처리, skip 없음 · 사람 검토 게이트)
├─ ① dev:spec            design/design.md → spec/ + fragment(검증 항목) + spec-archive
├─ ② dev:implement       명세 → 코드 + mock 단위테스트 (fragment 코드·마이그레이션)
├─ ③ dev:verify          deploy(local-service-deployer) + 검증(verifier) — fragment 검증 항목 실행
└─ ④ dev:release         CHANGELOG fold + git tag vX.Y.Z + 정리
```

- **검증 항목**: ①명세가 change-scoped로 생산 → fragment 기록 → ③검증이 실행
- **버전**: ⓪설계가 bump 결정 → 오케 보유 → ④릴리스 tag (명세서엔 없음)
- **병렬**: 기본은 단일 세션. 가끔 병렬은 별도 `dev:run` 세션 → ad-hoc `git merge` → main에서 ③·④
- **시각 디자인**: 별도 UI/UX 스테이지는 없음. 시각 디자인은 ①명세(프론트 디자인 컨벤션 → 디자인 정책 + 화면별 `ui.md`)와 ③검증(UI 시각 품질 게이트)에 임베드. ⓪의 "설계"는 아키텍처 설계. **외부 고정 디자인이 입력 강제로 들어오면** `ui-design-writer`가 *전달된 범위만 전사(`[입력 강제]`)*하고 나머지는 자율 저술(부분 커버리지) — 산출물 스키마는 그대로, 바뀌는 건 내용의 출처뿐

#### 구성

| 종류 | 이름 | 단계 | 역할 |
|------|------|------|------|
| Skill | run | 전체 | 파이프라인 메타 오케스트레이터 |
| Skill | design | ⓪ | 요구사항 → design/design.md + version bump (필수, 사람 게이트) |
| Agent | domain-architect | ⓪ | 전략 설계 작성 (도메인 카탈로그·컨텍스트맵·핵심흐름) |
| Skill | spec | ① | 명세 생성 오케 (+ 검증 항목 생산, 프론트 도메인은 화면별 ui.md 포함) |
| Skill | implement | ② | 구현·단위테스트 오케 |
| Skill | verify | ③ | 검증 단계 오케 (deploy + verifier) |
| Skill | release | ④ | 릴리스 오케 (fold + tag) |
| Skill | verify-run | ③ (helper) | 검증 실행 절차 + 템플릿 (verifier가 사용; 서비스 단위 성능 지표 수집·보고 포함) |
| Agent | system-service-writer · domain-knowledge-writer · domain-behavior-writer · domain-api-writer · ui-design-writer · spec-verifier | ① | 명세 작성·검증 (ui-design-writer = 화면별 시각 명세 ui.md) |
| Agent | coder · unit-tester | ② | 구현·단위테스트 (coder는 디자인 정책·ui.md 기반 시각 구현 + 모션 계측 프로브·결정론적 재생 모드 동반 구현 포함) |
| Agent | local-service-deployer · verifier | ③ | 기동·시나리오 검증 (verifier는 UI 시각 품질 게이트 — 상태·a11y·시각 정합 + 모션 불변식 프로브 실측 — 포함) |
| Agent | version-deriver | ④ | 버전 재산정 (병렬 fallback) |
| Agent | merge-conflict-resolver | ad-hoc | 병렬 머지 충돌 해결 |

컨벤션 카탈로그(`plugins/dev/conventions/`)·SoT 검증 스크립트(`plugins/dev/scripts/` + `sot-catalog.json`)는 dev에 포함됩니다.

#### run-state (세션 중단·재개) + 환경 SoT

- **run-state**: 오케 작업 상태(plan·진행·결정 로그·보유 버전)를 `.dev/<스프린트 버전>/`에 외부화 → 컨텍스트 컴팩션·세션 종료(같은 머신이면 컴퓨터 종료 포함)를 넘어 **멈춘 지점부터 자동 재개**. 소유=오케 레벨(재귀 폴더), start/done 마커. (`plugins/dev/run-state.md`)
- **환경 SoT**: 배포 환경 상태는 `.dev/env-state.md`(인스턴스 레벨)에 두어 deployer가 매 검증마다 재발견하지 않고 **인프라·서비스 재사용 / fresh는 검증 DB 데이터에 한정**. 검증 환경 사실(포트맵·연결·health·도구·로그)은 `spec/system.md` 검증 환경 컨벤션에 선언(카탈로그 `plugins/dev/conventions/system/local-verification.md`).
- `.dev/`는 gitignore (working 상태, 릴리스 시 정리).

#### 결정 등급 (L1/L2/L3)

명세 단계(①)에서 writer가 값을 결정할 때 사용하는 등급입니다.

| 등급 | 정의 | 처리 |
|------|------|------|
| L1 자율 | 설계서/컨벤션에서 결정값이 명확 | 그대로 작성 |
| L2 가정 | 합리적 디폴트 있음, 비즈니스/보안 영향 작음 | 작성 + 가정 마킹 → 통합 검토 |
| L3 결정 요청 | 사용자만 알 수 있는 정보, 비즈니스/보안/아키텍처 의사결정 | 즉시 개발자 호출 |

**L3 화이트리스트** (가정 금지, 무조건 호출): 시드 데이터, 비즈니스 보존/만료 정책, 권한/역할 정책, 자금·결제 비즈니스 룰, 컴플라이언스, 보안 정책, 인증/인가 정책, 외부 시스템 인증, 비기능 요구사항, 컨벤션 적용 조건이 모호한 항목.

#### 컨벤션 카탈로그

`plugins/dev/conventions/` 디렉토리에 명세서 작성 시 검토할 표준 컨벤션을 함께 제공합니다. system-service-writer가 명세서 작성 시 카탈로그를 자동 검토하여 적용 가능한 컨벤션의 결정 항목을 식별하고, 사용자만 결정할 수 있는 항목은 L3 결정 요청으로 개발자에게 escalate, 답변을 명세서에 인라인으로 박습니다.

```
plugins/dev/conventions/
├── _template.md
├── system/                  # system.md 차원에 박힐 컨벤션
│   └── source-layout.md     # 서비스 소스 구조: services/{backend|frontend}/{서비스}/ (배포 단위 = 폴더 1개)
└── service/
    ├── frontend/            # service/{프론트 서비스}.md 디자인 정책 — 포맷팅(date/number/phone) +
    │                        #   typography · screen-layout · design-tokens · component-foundation ·
    │                        #   component-states · visual-hierarchy · motion · a11y-baseline
    └── backend/             # service/{백엔드 서비스}.md HTTP 통신 컨벤션
```

> 프론트 디자인 정책(색 토큰·컴포넌트 파운데이션·상태 커버리지·시각 위계·모션·a11y)도 컨벤션으로 결정값이 service.md에 박히고, `ui-design-writer`가 그 위에서 화면별 `ui.md`를 작성합니다 — 시각 품질이 명세의 일부가 됩니다. 외부 고정 디자인이 입력 강제로 들어온 화면/축은 `ui-design-writer`가 그 디자인 시스템 대신 *주어진 값을 전사*(`[입력 강제]`)하고, 디자인이 덮지 않는 부분만 디자인 정책 위에서 자율 저술합니다(부분 커버리지).

> **모션은 검증 가능한 문장으로만 명세됩니다** (`service/frontend/motion.md`의 모션 불변식): "자연스럽게" 같은 형용사는 번역 카탈로그를 대조해 **횟수·기하·시간 불변식**으로 전개되고(감성 품질은 "사람 확인 항목"으로 분리), coder가 **모션 계측 프로브**(`probe:<이벤트> key=value` 로그, 검증 빌드 한정)와 **결정론적 UI 재생 모드**를 동반 구현하며(`system/local-verification.md` 결정 항목), verifier가 프로브 로그 실측으로만 판정합니다 — 소스 대조·프레임 눈 판독 PASS 금지. 모션이 시간축 속성이라 정적 확인으로 판정될 수 없기 때문입니다.

> 소스 코드 레이아웃은 `system/source-layout.md` 가 SoT입니다. 서비스 = 배포 단위 = 폴더 1개이며, system.md "서비스 구성"의 서비스 식별자가 곧 코드 폴더 경로(`services/{layer}/{서비스}`)가 되어 명세↔코드가 1:1로 고정됩니다(coder가 이 경로를 그대로 따름).

상세는 `plugins/dev/conventions/README.md` 참조.

#### 명세서 검증 (spec-verifier)

명세서 작성과 별도로, SoT 카탈로그 기준 검증을 위한 spec-verifier 에이전트를 제공합니다. 작성과 검증을 무상관으로 분리하여 writer 산출물의 무결성을 게이팅합니다. 두 단계로 동작합니다.

| 단계 | 내용 |
|------|------|
| Stage 1 (deterministic) | SoT 카탈로그 기반 기계 검증. 외부 스크립트가 판정. LLM 추정 금지 |
| Stage 2 (LLM judge) | 의미적 정합성 평가. Stage 1 통과 시만 진입 |

검증 범주:

| 범주 | 상태 |
|------|------|
| (1) 템플릿 적합성 (필수 섹션·메타데이터) | 적용 |
| (2) 링크 무결성 ([text](path) 파일 존재) | 적용 |
| (3) Cross-reference 정합성 (api↔scenarios/entities/rules, cross-domain 태그, fragment↔spec-archive, release CHANGELOG↔spec-archive) | 적용 |
| (4) 용어 일관성 (forbidden_synonyms — 사용자 프로젝트가 카탈로그에 채움) | 적용 (기본 비어 있음) |
| (5) 스키마 유효성 (메타데이터 값 형식) | 적용 |
| (6) 타입·포맷 정합성 (api 필드 타입 ↔ entities 속성 타입) | 적용 |
| (7) 커버리지 (도메인별 필수 파일 누락) | 적용 |
| (8) 유일성 (ID 중복 방지) | 적용 |

호출 방법:
- **자동**: `dev:spec`의 검증 단계가 spec-verifier를 자동 위임. 명세 생성 시 검증 자동 포함
- **외부 명시 호출**: 일반 대화로 "명세서 검증해줘" 또는 spec-verifier 에이전트 위임 (동일 에이전트의 두 진입점)

```
plugins/dev/
├── sot-catalog.json           # SoT 카탈로그 (검증 기준 데이터)
├── sot-catalog.README.md      # 사람용 해설
└── scripts/
    ├── _lib.py                # 공통 라이브러리
    ├── check_template.py      # (1) 템플릿 적합성
    ├── check_links.py         # (2) 링크 무결성
    ├── check_cross_refs.py    # (3) cross-reference 정합성
    ├── check_glossary.py      # (4) 용어 일관성
    ├── check_schemas.py       # (5) 스키마 유효성
    ├── check_types.py         # (6) 타입·포맷 정합성
    ├── check_coverage.py      # (7) 커버리지
    ├── check_uniqueness.py    # (8) 유일성
    └── run_all.py             # 8개 체크 일괄 실행
```

#### 생성되는 명세서 구조

```
changelog.d/                # 스프린트 fragment (동시 워크플로우 — 스프린트별 분리 파일이라 충돌 0).
└── <스프린트 버전>.md         # 스프린트 버전 = <forked-from>-<스프린트 키>(워크트리명, 메인=main).
                            # spec 변경(①dev:spec)과 코드 변경(②dev:implement)을 함께 담는다.
                            # 버전·tag 없음 — ④dev:release가 fold + 최종 버전/tag.

CHANGELOG.md                # 루트 단일 (릴리스 전용, ④dev:release가 작성).
                            # release가 여러 fragment를 묶어 한 엔트리(`## vX.Y.Z — YYYY-MM-DD`)로 fold.

spec/                       # 항상 HEAD (현재 본문)
├── system.md
├── domain/
│   ├── cross-domain/
│   │   ├── {비즈니스흐름}.md
│   │   ├── screens.md           # 화면 행위
│   │   └── ui.md                # 화면 시각 명세 (프론트 흐름)
│   └── {도메인}/
│       ├── rules.md
│       ├── entities.md
│       ├── scenarios.md
│       ├── api.md
│       ├── screens.md           # 화면 행위 (구성·표시 조건·인터랙션·폼 검증)
│       └── ui.md                # 화면 시각 명세 (레이아웃·컴포넌트·상태·위계·토큰 — 프론트 도메인만)
└── service/
    └── {서비스명}.md

spec-archive/               # 본문 스냅샷 (read-only).
├── <스프린트 버전>/           # ①dev:spec이 스프린트 시점에 갱신된 파일 본문을 그대로 복사.
│   └── {원래 spec 이하 경로}  # 예: 1.4.0-add-discount/domain/order/rules.md
└── v{X.Y.Z}/                 # ④dev:release가 fold 시 최종 선형 버전으로 정리.
    └── {원래 spec 이하 경로}
```

#### 테스트 체계

| 단계 | 담당 | 유형 | 환경 |
| ---- | ---- | ---- | ---- |
| 구현 (②dev:implement) | unit-tester | 코드 레벨 (mock) | 환경 불필요 (DB·풀스택 불요) |
| 검증 (③dev:verify) | verifier | 시나리오/E2E (실제 기동) | local-service-deployer 환경 |

## 전체 흐름 (dev:run — ⓪설계 → ①명세 → ②구현 → ③검증 → ④릴리스)

```
요구사항 (외부 인입도 요구사항으로 취급 · 강제사항 포함 가능)
   │
dev:run  (한 세션 · vX.Y.Z 보유)
   ⓪ dev:design   요구사항 → design/design.md + 범위 묶음 + version bump   (항상 수행 · 사람 검토 게이트)
   ① dev:spec     design/design.md → spec/ + fragment(검증 항목 기록) + spec-archive
   ② dev:implement 명세 → 코드 + mock 단위테스트 (fragment 코드·마이그레이션)
   ③ dev:verify   deploy + 시나리오/E2E 검증 (fragment 검증 항목 실행)
   ④ dev:release  CHANGELOG fold(+ 가정한 값) + git tag vX.Y.Z + 정리
```

1. `dev:design`이 요구사항을 분석 → `design/design.md`(전략 설계) + version bump 산정. 외부 인입도 요구사항으로 취급(skip 없음), 강제사항은 `[입력 강제]`로 수용. 구조적 L3는 여기서 개발자에게 받음(유일한 사람 검토 게이트)
2. `dev:spec`이 `design/design.md`를 분석하여 `spec/` + 스프린트 fragment 생성 — 이번 변경의 change-scoped 검증 항목을 fragment에 기록 (잔여 L3만 escalate, L1/L2 값 가정은 릴리스 노트로 사후 보고)
3. `dev:implement`로 구현 + mock 단위테스트 → fragment에 코드·마이그레이션 기록
4. `dev:verify`가 구현 직후 같은 세션에서 deploy + 시나리오/E2E 검증 실행 (PASS여야 릴리스) — 판정은 **PASS/FAIL뿐**이며 "조건부 PASS" 같은 절충 상태를 만들지 않는다. UI 채널은 **실 런타임(실제 앱)을 선언된 드라이버로 끝까지 구동**해 확인하며 mock 단위 테스트로 대체할 수 없다(실 통합 seam은 mock 대체 불가). 미도달·보류·부분·mock 대체 등 **PASS 아닌 모든 상태는 release 차단**. UI 드라이버가 **호스트 키보드/마우스를 점유**하는 경우(네이티브 macOS XCUITest: 시뮬레이터 없이 호스트 직접 실행)에는 오케스트레이터가 그 UI 채널 **진입 전 개발자 허가**를 받고 진행(거부 시 보류, 생략 아님). 브라우저·iOS/Android는 무점유라 게이트 없음
5. `dev:release`가 보유한 `vX.Y.Z`로 CHANGELOG fold + tag
6. (가끔 병렬) 각 기능을 별도 `dev:run` 세션으로 → ad-hoc `git merge`(충돌 시 `merge-conflict-resolver`) → main에서 `dev:verify`·`dev:release`

## 플러그인 관리

```bash
# 업데이트
/plugin update dev@eqbr-plugins

# 비활성화
/plugin disable dev@eqbr-plugins

# 활성화
/plugin enable dev@eqbr-plugins

# 제거
/plugin uninstall dev@eqbr-plugins
```

## 주의사항

- **스코프 중복 설치 금지**: 같은 플러그인을 여러 스코프에 설치하면 두 번 로드됩니다. 하나만 선택하세요.
- **프로젝트 설치 시 커밋 필요**: project 스코프로 설치하면 `.claude/settings.json`이 생성됩니다. 이 파일을 커밋해야 팀원도 동일하게 적용됩니다.
- **세션 중단·재개**: 오케 작업 상태가 run-state(`.dev/<스프린트 버전>/`)에 외부화되어, 컨텍스트 컴팩션·세션 종료(같은 머신이면 컴퓨터 종료 포함)가 나도 **멈춘 지점부터 자동 재개**됩니다. 구현 단위가 많아도 한 세션에서 이어갈 수 있습니다. (`plugins/dev/run-state.md`)
- **오케스트레이터 상태 추적**: dev:run·dev:spec·dev:implement 등 오케스트레이터는 에이전트 반환 시 결과 기록 → 다음 행동 판단 → 실행 순서를 따르고, 그 진행을 run-state에 start/done 마커로 남깁니다. 진행 상태가 개발자에게 표시되므로 잘못된 판단에 즉시 개입할 수 있습니다.
- **에이전트 재위임**: 에이전트가 질문·FAIL을 반환해 다시 일을 시킬 때는 **새 호출(재spawn)**로 진행합니다 — 세션 기반 resume(SendMessage)에 의존하지 않습니다. 잃으면 안 되는 맥락(답변·FAIL 항목·결정)은 run-state·명세 경로를 템플릿에 담아 전달하고, 에이전트가 spec/·코드 파일에서 맥락을 회복합니다.

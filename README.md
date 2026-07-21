# EQBR Claude Plugins

EQBR의 Claude Code 플러그인 마켓플레이스입니다.

## 워크플로우

워크플로우는 하나의 `dev` 플러그인에서 **한 세션에 순차로** 동작합니다. 메타 오케스트레이터 `dev:run`이 ⓪설계→①상세설계→②구현→③검증→④릴리스를 차례로 진행합니다.

| 단계 | 내용 | 담당 (dev 스킬) |
|------|------|------|
| ⓪ 설계 (필수) | 요구사항 → **요구사항 추적 산출물 `design/requirements.md`**(요구사항별 `R-n` ID·상태 active/승계/released) + `design/design.md`(전략 설계 8섹션 — **완료 기준(`AC-n`·참조 `R-n`·요구사항별 3면 done 정의)** 포함) + 범위 묶음 + version bump. **외부 인입도 요구사항으로 취급(skip 없음)**, 강제사항 수용. **유일한 사람 검토 게이트**(완료 기준·`R-n` 확정을 검토) | `design` (+`domain-architect`) |
| ① 상세설계 작성 | `design/design.md` → 구현 가능한 상세설계 (`tactical/`) + **검증 원장 `tactical/verification-ledger.md`**(완료 기준 → 면별 다중 단정·채널 사다리·코더/verifier 2칸·해소 증거) + fragment(`changelog.d/`). writer 위임은 **프론티어 배치** 병렬 | `상세설계` |
| ② 구현 (+ 회귀 테스트) | 상세설계 → 코드 + **coder가 함께 소유하는 회귀 단위 테스트** + **원장 단정(채널 1~3) 구현시점 통과·코더 칸 기록**(회귀 보조 + 단정 증명일 뿐 done 증거 아님). 구현 단위는 **프론티어 배치** 병렬 | `implement` |
| ③ 검증 | 구현 직후 **같은 세션**에서 deploy + 검증 원장의 **면별 다중 단정을 채널별로 집행**(채널1~2 재실행·3~5 독립) + 원장 **verifier 칸** 갱신 | `verify` |
| ④ 릴리스 | `CHANGELOG.md` fold · `git tag` (버전은 ⓪/오케가 보유) | `release` |

기본은 **단일 세션 순차**입니다. 가끔 병렬이 필요하면 각 기능을 별도 `dev:run` 세션으로 돌리고 ad-hoc `git merge`로 합친 뒤 main에서 ③검증·④릴리스를 수행합니다. **완료 기준은 ⓪설계가 박고(사람 게이트) → ①상세설계가 검증 원장에서 실행 가능한 면별 다중 단정으로 분해 → ②구현이 채널 1~3 단정을 구현시점에 통과 증명(코더 칸) → ③검증이 실채널로 집행(verifier 칸)**하며, **버전은 ⓪설계가 정해 오케가 보유**합니다(상세설계서엔 버전 없음). 원장 두 칸은 **"미달성(코더 못함) vs 구현됨·미검증(코더 PASS·verifier 미확인) vs done(verifier PASS)"**을 자동으로 가릅니다. **미달성·미검증은 명시적 해소 증거 없이 확정(done)으로 승격되지 않으며(done=verifier PASS), ④릴리스의 결정론 백스톱(`check_ledger.py`)이 태그를 차단**합니다. ⓪의 "설계"는 아키텍처 설계입니다 — **별도의 UI/UX 디자인 스테이지는 두지 않되, 시각 디자인은 ①상세설계(프론트 디자인 컨벤션 → service.md 디자인 정책 + 화면별 `ui.md`)와 ③검증(UI 시각 품질 게이트)에 임베드**되어 있습니다.

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

상세설계 작성(상세설계)·구현(implement)·검증(verify)·릴리스(release)를 하나로 통합한 개발 워크플로우 플러그인입니다. **한 세션에서** ⓪설계→①상세설계→②구현→③검증→④릴리스를 진행합니다.

#### 사용법

```bash
/dev:run [요구사항 경로 + 개발 의도]   # 전체 파이프라인 (메타 오케)
```

단계별 개별 호출도 가능합니다:

```bash
/dev:design [요구사항]        # ⓪ 설계 (요구사항 → design/design.md + 완료 기준 + version bump)
/dev:tactical   [design.md 경로]   # ① 상세설계 (+ 검증 원장: 완료 기준 → 면별 다중 단정·채널 사다리)
/dev:implement [상세설계 경로]     # ② 구현 + 회귀 단위테스트(coder 소유) + 원장 단정(채널1~3) 코더 칸
/dev:verify                   # ③ 검증 (deploy + 원장의 면별 다중 단정 집행 · verifier 칸)
/dev:release [vX.Y.Z]          # ④ 릴리스 (CHANGELOG fold + tag)
```

#### 워크플로우

```
dev:run (메타 오케 · 한 세션 · vX.Y.Z 보유)
├─ ⓪ dev:design  [필수]  요구사항 → design/design.md(+ 완료 기준 3면) + 범위 묶음 + version bump   (외부 인입도 요구사항·강제사항으로 처리, skip 없음 · 사람 검토 게이트)
├─ ① dev:tactical            design/design.md → tactical/ + 검증 원장(verification-ledger.md, 완료 기준→면별 다중 단정) + fragment + tactical-archive   (writer 위임 = 프론티어 배치 병렬)
├─ ② dev:implement       상세설계 → 코드 + 회귀 단위테스트(coder 소유) + 원장 단정(채널1~3) 코더 칸 (fragment 코드·마이그레이션. 구현 단위 = 프론티어 배치 병렬)
├─ ③ dev:verify          deploy(local-service-deployer) + 검증(verifier) — 원장의 면별 다중 단정 채널별 집행 + 원장 verifier 칸 갱신
└─ ④ dev:release         CHANGELOG fold + 경계 대조 게이트(--boundary release = 커버리지 COV + 원장 L1~L7) + git tag vX.Y.Z + 정리
```

- **완료 기준·단정**: ⓪설계가 완료 기준(3면 done 정의)을 박음(사람 게이트) → ①상세설계의 verification-criteria-writer가 검증 원장에서 실행 가능한 **면별 다중 단정**(`T<n>` 절차→관측→기대, 채널 사다리 1~5)으로 분해 → ②구현 coder가 채널 1~3을 구현시점에 통과 증명(코더 칸) → ③검증이 실채널로 집행(verifier 칸)
- **검증 원장**: 커밋·누적·상태보유 산출물(`tactical/verification-ledger.md`) — 상태 **두 칸(코더·verifier)**으로 미달성/미검증/done을 가름. 릴리스에서 산문으로 녹지 않고 `tactical-archive/`로 스냅샷, 미종결 단정(verifier 보류/미결/- 또는 코더 FAIL)은 다음 스프린트로 **승계**. 미달성·미검증→확정 승격은 ④릴리스 결정론 백스톱이 차단(done=verifier PASS). 라이브 원장은 **현재 목록만** 유지합니다 — 완료 기준이 릴리스로 확정돼 design.md 현재 `## 완료 기준`에서 빠졌고 두 칸이 모두 종결-PASS인 AC블록은 라이브 원장에서 **졸업**(제거)하고, 그 완결 기록은 `tactical-archive/<그 버전>/`가 권위입니다. 즉 **라이브 원장 = (현재 완료 기준 AC) + (아직 안 끝난 승계 단정)** — 전 이력 보관소가 아닙니다(백스톱 L4는 미종결 단정 drop만 위반, 종결-PASS drop=졸업은 허용)
- **버전**: ⓪설계가 bump 결정 → 오케 보유 → ④릴리스 tag (상세설계서엔 없음)
- **경계별 결정론 대조 게이트**: 각 단계 경계에서 **커버리지**(상류 전항목 → 하류 대응)와 **종결**(목록 전항목이 완료 + 증거)을 결정론으로 강제해, 미구현·미검증·무토큰 보류가 릴리스로 새는 걸 막는다. 오케가 단계 전환 직전 커밋 산출물에 `run_all.py --boundary <경계>`를 실행하고 **위반 0일 때만 전진**한다 — tactical→커버리지(COV)+원장 L1~L3, implement→+L5(코더 종결), verify→+L6(verifier 종결)·L7(보류=항목별 승인 토큰), release→L1~L7 전량. 실행자는 자기 칸을 기록하되 **스스로 경계를 닫지 못하며**(닫힘 = 스크립트 판정), `dev:run`은 결과를 pipeline.md `## 경계 대조`에 남긴다. 커버리지는 `design/requirements.md`(R-n) → design.md `## 완료 기준`(AC-n) → 검증 원장 `## AC-n` 블록을 ID로 조인해 상류 전항목이 하류 목록이 됐는지를 본다. **보류는 차단 부채**다 — 포괄 override는 폐지되고, 항목별 승인 토큰(`승인: <개발자>·<날짜>·<사유>`)으로만 통과한다. 하위호환: `requirements.md`가 없으면 커버리지·종결 게이트는 no-op(레거시 소급 없음, 다음 스프린트 채택 시 강제)
- **병렬**: 기본은 단일 세션. 가끔 병렬은 별도 `dev:run` 세션 → ad-hoc `git merge` → main에서 ③·④
- **①상세설계 위임 스케줄**: 작업 단위 = 문서역할 × 도메인. 도메인 내부 의존은 `entities → rules → scenarios → {screens, api}`로 **4단 + 2갈래 분기**입니다(screens와 api는 서로 의존하지 않아 scenarios 완료 시 동시 출발 — api의 권위는 scenarios·entities·rules·system/service이고 screens를 참조하지 않습니다). `screens(d) → ui(d)`는 **도메인 로컬 엣지**라 한 도메인 screens가 끝나면 그 즉시 그 도메인 ui가 시작되고, cross-domain ui만 cross-domain screens에 의존합니다. cross-domain 흐름 f의 선행도 f가 관통하는 **참여 도메인**뿐입니다. 따라서 **전역 배리어는 검증 원장(cross-cutting)과 전역 검증 둘뿐**이며, 그 외에는 도메인 경계를 넘는 프론티어 배치 pipeline으로 흐릅니다
- **재사이클 상한(종료 보장)**: 같은 노드(문서역할 × 도메인)에 대한 재위임은 **최대 2회**입니다. 3회차 진입 시 재위임하지 않고 잔여 위반을 `미해결[]`로 확정 + escalation 로그를 남긴 뒤 나머지 노드는 계속 진행합니다(한 노드의 상한 도달이 전체를 멈추지 않음). 서로 다른 위반으로 재지적되어도 횟수는 합산되며, 상한 도달 노드는 최종 보고에 반드시 별도 항목으로 보고됩니다
- **읽기 범위**: writer 8종은 `# 읽기 범위(권위는 전량, 읽기는 필요한 만큼)` 규율을 따릅니다 — 자기 작업 범위와 무관한 구간을 통째로 읽지 않되, 범위 축소가 누락의 핑계가 되지 않도록 명시합니다. 오케는 위임 템플릿에 `설계서 참조 범위`(섹션 앵커)를 실어 보냅니다. 앵커는 **좌표이지 내용의 사본이 아니며**, 요약·발췌를 프롬프트에 실으면 그 요약이 권위 문서를 대체하기 시작해 SoT가 무너지므로 금지합니다
- **라이브 문서 = 현재 상태만**: writer 8종(도메인 상세·system/service·`design.md`)은 라이브 산출물에 **현재 상태만** 담습니다 — 변경 이력을 본문에 쌓지 않습니다. 갱신은 in-place 덮어쓰기라 바뀐 항목은 옛 내용을 덮어써 **최종 상태만** 남고, `0.X 델타`·`이전 델타`·`영향 점검`·`舊 X → 신규 Y`·`무변경/전량 보존` 같은 델타 서술을 본문에 누적하지 않습니다. **상단 메타에도 `> 수정 이력:`·`> 변경 이력:` 같은 이력 필드를 만들지 않습니다** — 메타는 `> 버전`·`> 최종 수정`(필수)과 `> 입력`(현행 근거)·`> 서비스`까지이고, `> 입력`은 현행 `design.md`·권위 입력만 가리킵니다. **옛 서술을 취소선(`~~…~~`)으로 남기지 않고** 덮어써 최종 상태만 둡니다. 단 "지금도 존재하는 deprecated 필드"·"재사용 금지 결번 ID"는 과거 이력이 아니라 **현재 제약**이라 반드시 남기되, 취소선이 아니라 **명시적 상태 표기**로 적습니다 — 필드명은 그대로 두고 상태 칸에 `deprecated`(+잔존 사실), 결번 ID 행에 `결번`/`재사용 금지`(+제거 사유). 취소선은 "지워졌다"는 뜻이라 "지금도 존재함"과 모순되고 상태 칸이 이미 현재 정보를 담으므로 중복 장식입니다. domain-architect도 개요는 현재 목적+범위로 in-place 덮어쓰고 버전 표는 현재 HEAD 한 건만 두며, 같은 취지로 메타 이력 필드·취소선을 두지 않습니다. **무엇이 언제 왜 바뀌었는지는 `CHANGELOG.md`·git tag·`tactical-archive/<버전>/`가 이미 보유**합니다 — 이력을 라이브 본문에 중복시키면 changelog-in-body로 문서가 스프린트마다 부풀어 SoT 가독성이 무너집니다. 이 규율은 결정론 체크 `check_history_residue.py`가 100% 집행합니다
- **단계 간 컨텍스트 인계**: `dev:run`은 단계 경계에서 **산출물 경로 + 게이트 판정 + 다음 단계가 실제로 쓰는 값**만 보유합니다. 위임별 반환 상세는 다음 단계로 넘기지 않고 run-state 파일에서 다시 읽습니다. 도메인 8개 이상 / bubble-up 재사이클 발생 / 사용량 한도 중단 이력 중 하나라도 해당하면 한 세션 완주 대신 단계별 세션 분할을 권장합니다
- **시각 디자인**: 별도 UI/UX 스테이지는 없음. 시각 디자인은 ①상세설계(프론트 디자인 컨벤션 → 디자인 정책 + 화면별 `ui.md`)와 ③검증(UI 시각 품질 게이트)에 임베드. ⓪의 "설계"는 아키텍처 설계. **외부 고정 디자인이 입력 강제로 들어오면** `ui-design-writer`가 *전달된 범위만 전사(`[입력 강제]`)*하고 나머지는 자율 저술(부분 커버리지) — 산출물 스키마는 그대로, 바뀌는 건 내용의 출처뿐

#### 구성

| 종류 | 이름 | 단계 | 역할 |
|------|------|------|------|
| Skill | run | 전체 | 파이프라인 메타 오케스트레이터 |
| Skill | design | ⓪ | 요구사항 → design/design.md + version bump (필수, 사람 게이트) |
| Agent | domain-architect | ⓪ | 전략 설계 작성 (도메인 카탈로그·컨텍스트맵·핵심흐름) + **요구사항 추적 산출물 `design/requirements.md`(R-n) 소유** + 완료 기준에 `AC-n` 부여(원장은 재사용, mint 금지) |
| Skill | 상세설계 | ① | 상세설계 생성 오케 (+ 검증 원장 생산, 프론트 도메인은 화면별 ui.md 포함) |
| Skill | implement | ② | 구현·회귀테스트 오케 (coder가 구현+회귀 단위테스트 함께 소유) |
| Skill | verify | ③ | 검증 단계 오케 (deploy + verifier — 원장의 면별 다중 단정 채널별 집행·verifier 칸 갱신) |
| Skill | release | ④ | 릴리스 오케 (fold + 경계 대조 게이트 `--boundary release`(커버리지 COV + 원장 L1~L7) + tag) |
| Skill | verify-run | ③ (helper) | 검증 실행 절차 + 템플릿 (verifier가 사용; 서비스 단위 성능 지표 수집·보고 포함) |
| Agent | system-service-writer · entities-writer · rules-writer · scenarios-writer · screens-writer · domain-api-writer · ui-design-writer · verification-criteria-writer · tactical-verifier | ① | 상세설계 작성·검증 (도메인 내부 의존 = `entities → rules → scenarios → {screens, api}`, `screens(d) → ui(d)`는 도메인 로컬 엣지; ui-design-writer = 화면별 시각 상세설계 ui.md; **verification-criteria-writer = 검증 원장(완료 기준 → 면별 다중 단정·채널 사다리) — cross-cutting 최후미**) |
| Agent | coder | ② | 구현 + **회귀 단위테스트를 함께 소유**(unit-tester 폐지·coder 흡수 — 회귀 보조 + 단정 증명일 뿐 done 증거 아님. 원장 담당 단정(채널1~3)을 T-n 회귀테스트로 실장·통과·**코더 칸** 기록). 디자인 정책·ui.md 기반 시각 구현 + 모션 계측 프로브·결정론적 재생 모드 동반 구현 포함. **개발 진단 로그 상시 의무**(검증 빌드에 `diag:…` 구조화 로그를 실패 이음매마다 심음 — 없는 구현은 미완성, FAIL 후엔 이 로그 우선 조회) |
| Agent | local-service-deployer · verifier | ③ | 기동·시나리오 검증 (verifier는 원장의 각 AC 면별 다중 단정을 **채널별 실채널로 집행**(채널1~2 재실행·3~5 독립 판정, 채널4 정적 스크린샷은 유효 PASS 근거)하고 원장 **verifier 칸** 갱신 — 단정은 스스로 도출 안 함. UI 시각 품질 게이트 — 상태·a11y·시각 정합 + 모션 불변식 프로브 실측 — 포함. FAIL 시 **개발 진단 로그(`diag:…`) 발췌를 진단에 포함**) |
| Agent | version-deriver | ④ | 버전 재산정 (병렬 fallback) |
| Agent | merge-conflict-resolver | ad-hoc | 병렬 머지 충돌 해결 |

컨벤션 카탈로그(`plugins/dev/conventions/`)·SoT 검증 스크립트(`plugins/dev/scripts/` + `sot-catalog.json`)·작성 에이전트 공통 계약 정본(`plugins/dev/scripts/writer-core.md`)은 dev에 포함됩니다.

#### run-state (세션 중단·재개) + 환경 SoT

- **run-state**: 오케 작업 상태(plan·진행·결정 로그·보유 버전)를 `.dev/<스프린트 버전>/`에 외부화 → 컨텍스트 컴팩션·세션 종료(같은 머신이면 컴퓨터 종료 포함)를 넘어 **멈춘 지점부터 자동 재개**. 소유=오케 레벨(재귀 폴더), start/done 마커. (`plugins/dev/run-state.md`)
- **환경 SoT**: 배포 환경 상태는 `.dev/env-state.md`(인스턴스 레벨)에 두어 deployer가 매 검증마다 재발견하지 않고 **인프라·서비스 재사용 / fresh는 검증 DB 데이터에 한정**. 검증 환경 사실(포트맵·연결·health·도구·로그)은 `tactical/system.md` 검증 환경 컨벤션에 선언(카탈로그 `plugins/dev/conventions/system/local-verification.md`). deployer는 이 인스턴스의 **개발 진단 로그 조회 명령**(로그 조회 규약을 인스턴스 값으로 채운 것)도 `.dev/env-state.md`에 기록해, coder·verifier·사용자가 재발견 없이 같은 명령으로 `diag:…`를 읽는다.
- `.dev/`는 gitignore (working 상태, 릴리스 시 정리).

#### 결정 등급 (L1/L2/L3)

상세설계 단계(①)에서 writer가 값을 결정할 때 사용하는 등급입니다.

| 등급 | 정의 | 처리 |
|------|------|------|
| L1 자율 | 설계서/컨벤션에서 결정값이 명확 | 그대로 작성 |
| L2 가정 | 합리적 디폴트 있음, 비즈니스/보안 영향 작음 | 작성 + 가정 마킹 → 통합 검토 |
| L3 | 사용자만 알 수 있는 정보, 비즈니스/보안/아키텍처 의사결정 | 가정 불가 시 미해결[]; 상위 모순이면 ⓪전략설계로 bubble-up (mid-cycle 사람 개입 아님) |

**L3 화이트리스트** (가정 금지): 시드 데이터, 비즈니스 보존/만료 정책, 권한/역할 정책, 자금·결제 비즈니스 룰, 컴플라이언스, 보안 정책, 인증/인가 정책, 외부 시스템 인증, 비기능 요구사항, 컨벤션 적용 조건이 모호한 항목. 가정하지 않고 미해결[]로 남기거나 상위 모순이면 ⓪전략설계로 bubble-up합니다.

#### 컨벤션 카탈로그

`plugins/dev/conventions/` 디렉토리에 상세설계서 작성 시 검토할 표준 컨벤션을 함께 제공합니다. system-service-writer가 상세설계서 작성 시 카탈로그를 자동 검토하여 적용 가능한 컨벤션의 결정 항목을 식별하고, 사용자만 결정할 수 있는 항목은 가정하지 않고 미해결[]로 남기거나 상위 모순이면 ⓪전략설계로 bubble-up하며(상세설계 단계에서 mid-cycle로 개발자에게 직접 묻지 않음), ⓪전략설계 게이트에서 받은 결정값을 상세설계서에 인라인으로 박습니다.

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

> 프론트 디자인 정책(색 토큰·컴포넌트 파운데이션·상태 커버리지·시각 위계·모션·a11y)도 컨벤션으로 결정값이 service.md에 박히고, `ui-design-writer`가 그 위에서 화면별 `ui.md`를 작성합니다 — 시각 품질이 상세설계의 일부가 됩니다. 외부 고정 디자인이 입력 강제로 들어온 화면/축은 `ui-design-writer`가 그 디자인 시스템 대신 *주어진 값을 전사*(`[입력 강제]`)하고, 디자인이 덮지 않는 부분만 디자인 정책 위에서 자율 저술합니다(부분 커버리지).

> **모션은 검증 가능한 문장으로만 상세설계됩니다** (`service/frontend/motion.md`의 모션 불변식): "자연스럽게" 같은 형용사는 번역 카탈로그를 대조해 **횟수·기하·시간 불변식**으로 전개되고(감성 품질은 "사람 확인 항목"으로 분리), coder가 **모션 계측 프로브**(`probe:<이벤트> key=value` 로그, 검증 빌드 한정)와 **결정론적 UI 재생 모드**를 동반 구현하며(`system/local-verification.md` 결정 항목), verifier가 프로브 로그 실측으로만 판정합니다 — 소스 대조·프레임 눈 판독 PASS 금지. 모션이 시간축 속성이라 정적 확인으로 판정될 수 없기 때문입니다.

> **개발 진단 로그로 검증 빌드가 실패를 소리 없이 삼키지 않게 합니다** (`system/local-verification.md` 결정 항목 — 모션 계측 프로브의 일반화): 검증 대상 서비스/앱은 실패 취약 이음매(caught 예외·에러 확정·외부/seam 호출 실패·핵심 상태 전이)의 **관찰 사실**을 구조화 한 줄(`diag:<이음매> level=<info|warn|error> …`)로 출력하는 진단 로그를 갖춥니다 — **검증 빌드 한정·사실만·판정 없음**(판정은 verify의 몫), 출력·조회는 로그 조회 규약과 **같은 채널**. 검증 실패 시 coder·verifier가, 개발자가 직접 실행할 때 사용자가 **같은 로그 하나**로 원인을 즉시 국소화합니다(에러 추적). 결정론 검사 (13) `check_dev_log.py`가 이 결정 항목이 `system.md` 검증 환경 컨벤션에 선언됐는지 전역 스코프에서 게이팅합니다. 제품 기능으로서의 에러 관측(사용자/어드민 대상·DB 영속·프라이버시 불변식)과는 목적·거처가 분리되며, 후자는 제품 도메인(tactical/domain)에 삽니다.

> 소스 코드 레이아웃은 `system/source-layout.md` 가 SoT입니다. 서비스 = 배포 단위 = 폴더 1개이며, system.md "서비스 구성"의 서비스 식별자가 곧 코드 폴더 경로(`services/{layer}/{서비스}`)가 되어 상세설계↔코드가 1:1로 고정됩니다(coder가 이 경로를 그대로 따름).

상세는 `plugins/dev/conventions/README.md` 참조.

#### 상세설계서 검증 (tactical-verifier)

상세설계서 작성과 별도로, SoT 카탈로그 기준 검증을 위한 tactical-verifier 에이전트를 제공합니다. 작성과 검증을 무상관으로 분리하여 writer 산출물의 무결성을 게이팅합니다. 두 단계로 동작합니다.

| 단계 | 내용 |
|------|------|
| Stage 1 (deterministic) | SoT 카탈로그 기반 기계 검증. 외부 스크립트가 판정. LLM 추정 금지 |
| Stage 2 (LLM judge) | 의미적 정합성 평가. Stage 1 통과 시만 진입 |

검증 범주:

| 범주 | 상태 |
|------|------|
| (1) 템플릿 적합성 (필수 섹션·메타데이터) | 적용 |
| (2) 링크 무결성 ([text](path) 파일 존재) | 적용 |
| (3) Cross-reference 정합성 (api↔scenarios/entities/rules, cross-domain 태그, fragment↔tactical-archive, release CHANGELOG↔tactical-archive) | 적용 |
| (4) 용어 일관성 (forbidden_synonyms — 사용자 프로젝트가 카탈로그에 채움) | 적용 (기본 비어 있음) |
| (5) 스키마 유효성 (메타데이터 값 형식) | 적용 |
| (6) 타입·포맷 정합성 (api 필드 타입 ↔ entities 속성 타입) | 적용 |
| (7) 커버리지 (도메인별 필수 파일 누락) | 적용 |
| (8) 유일성 (ID 중복 방지) | 적용 |
| (9) 검증 원장 무결성 (전역 스코프) — 3면 완비(각 면 ≥1 단정)·코더/verifier PASS 해소증거·계약 미결 0·미종결 단정 누적 승계 (+ 경계 종결 게이트 L5 코더 종결·L6 verifier 종결·L7 보류=항목별 승인 토큰 — `--boundary`에서만 발화) (+ Stage 2: 완료 기준 커버리지·단정 적절성·채널 하향 정당성) | 적용 |
| (10) 문서 크기 예산 (`doc_size_budget_exceeded` — 상한 초과 = 전량 읽기 불가 = 권위 문서 전제 붕괴) | 적용 (카탈로그에 `size_budget` 없으면 비활성) |
| (12) 경계 커버리지 (전역 스코프) — 요구사항(R-n)→완료기준(AC-n)→원장 AC 블록 ID 조인, 상류 전항목 하류 대응 (COV-1/1b/2/2b, 각 dangling 역검사) | 적용 (`requirements.md` 없으면 no-op) |
| (13) 개발 진단 로그 선언 (전역 스코프) — `system.md` `## 검증 환경 컨벤션`이 있으면 그 안에 "개발 진단 로그"(검증 빌드 한정 `diag:…` 구조화 로그) 결정 항목 선언 필수 (섹션 부재·system.md 부재면 no-op) | 적용 (섹션 없으면 no-op) |

호출 방법:
- **자동**: `dev:tactical`의 검증 단계가 tactical-verifier를 자동 위임. 상세설계 생성 시 검증 자동 포함
- **외부 명시 호출**: 일반 대화로 "상세설계서 검증해줘" 또는 tactical-verifier 에이전트 위임 (동일 에이전트의 두 진입점)

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
    ├── check_ledger.py        # (9) 검증 원장 백스톱 L1~L4 + 경계 종결 게이트 L5~L7 (전역 스코프 · 릴리스 tag 게이트 · L5~L7은 --boundary에서만 발화)
    ├── check_size_budget.py   # (10) 문서 크기 예산 (전량 읽기 가능성)
    ├── check_history_residue.py # (11) 이력 잔재 (라이브=현재상태만 · 이력 메타 필드·취소선·델타 블록)
    ├── check_traceability.py  # (12) 경계 커버리지 (요구사항 R-n → 완료기준 AC-n → 원장 AC, 전역 스코프)
    ├── check_dev_log.py       # (13) 개발 진단 로그 선언 (system.md 검증 환경 컨벤션에 "개발 진단 로그" 결정 항목 선언 필수, 전역 스코프 · 섹션/파일 부재면 no-op)
    ├── run_all.py             # 체크 13종 일괄 실행 (--domain 로컬 스코프에선 원장·커버리지·진단 로그 체크 skip · --boundary {design|tactical|implement|verify|release}로 경계 종결 게이트 발화)
    └── check_agent_core.py    # 작성 에이전트 공통 계약 드리프트 린트 (플러그인 내부 전용 · run_all 미등록)
```

**문서 크기 예산 (10)**: 상한 초과는 "에이전트가 그 문서를 전량 읽을 수 없다"는 뜻이고, 이는 권위 문서 전제 자체가 무너졌다는 신호입니다(비용 문제가 아니라 정합성 문제). 위반 rule명은 `doc_size_budget_exceeded`이며, 정상 처리는 **임의 파일 분할이 아니라 도메인 분리 검토 bubble-up(⓪`dev:design`)**입니다 — 파일을 기계적으로 쪼개면 SoT 카탈로그의 file_kind 경로·필수 섹션 계약이 함께 깨지기 때문입니다. 예산은 `sot-catalog.json` 최상위 `size_budget` 키(`default_max_bytes` 200000 · `advisory_bytes` 60000 · `per_kind`로 kind별 덮어쓰기 — design 250000)에서 관리하며, 이 키가 없으면 체크는 비활성입니다(하위호환).

**이력 잔재 (11)**: 크기 예산과 같은 논리의 결정론 집행입니다 — "라이브 문서 = 현재 상태만"이라는 작성 규율(이행 목표 90%)을 100% 집행합니다. 잡는 잔재는 세 가지입니다: 이력 메타 필드(`> 수정 이력:`·`> 변경 이력:` — rule `history_metadata_field`), 취소선(`~~…~~` — rule `strikethrough_residue`), 델타 블록/서사(rule `delta_block_residue`) — 리터럴 서명(`### 이전 델타`·`적용 범위 전환`·`스탠스 종료`·`시스템 영향 점검`·`델타 승계`)뿐 아니라 **버전-인접 "델타·점검"**(`\d+\.\d+\S*\s*(델타|점검)` — `**0.18.0 델타**` 블록과 `> 출처:`/`> 입력:`/`> 도메인:` 메타 줄의 "스프린트 0.X 델타" 서사를 함께 잡음. `.dev/0.12.0/kickoff.md` 같은 경로 참조는 버전 뒤가 `/kickoff`라 미매치). "영향 점검"을 "시스템 영향 점검"으로 좁혀 "…클라이언트 영향 점검" 같은 참조 설명 오탐을 배제. 배경은 sot-catalog `required_metadata`가 버전·최종수정 둘뿐인데 writer가 스키마 밖 이력 필드를 발명해도 `check_template`이 여분 필드를 검열하지 않아 통과시켰다는 것입니다. 코드펜스(```` ``` ````) 내부와 fragment·CHANGELOG(이력 권위)는 검사 대상에서 제외합니다. 정상 처리는 삭제가 아니라 **최종 상태 덮어쓰기**(이력 권위는 CHANGELOG·tactical-archive). 이 체크는 GLOBAL_ONLY가 아니라 `--domain` 스코프에서도 돌아 writer self-verify 시점에도 잡힙니다. 설정은 `sot-catalog.json` 최상위 `history_residue` 키(`metadata_history_fields`·`delta_block_signatures`·`flag_strikethrough`)에서 관리하며, 키가 없으면 내장 기본값을 씁니다(비활성 아님).

**드리프트 린트 (`check_agent_core.py`)**: 작성 에이전트 8종이 공유하는 계약 블록 3종(`read_scope`·`self_verify`·`l3_partial_write`)의 정본은 `plugins/dev/scripts/writer-core.md`이고, 각 에이전트는 그 텍스트를 **인라인으로 그대로 보유**합니다. 린트는 바이트 비교로 드리프트를 잡습니다. `run_all.py`에는 등록하지 않습니다 — `run_all`은 *사용자 프로젝트의 산출물*을, 이 린트는 *플러그인 자신의 소스*를 검사하므로 성격이 다릅니다. 참조(Read 지시)로 내리지 않은 이유는 에이전트 정의에 include 메커니즘이 없고, harness-design §6.1이 Read 지시의 이행 목표를 90%로 잡는데 완결 반환 계약·self-verify는 안전 장치라 10% 누락을 허용할 수 없기 때문입니다.

#### 생성되는 상세설계서 구조

```
changelog.d/                # 스프린트 fragment (동시 워크플로우 — 스프린트별 분리 파일이라 충돌 0).
└── <스프린트 버전>.md         # 스프린트 버전 = <forked-from>-<스프린트 키>(워크트리명, 메인=main).
                            # 상세설계 변경(①dev:tactical)과 코드 변경(②dev:implement)을 함께 담는다.
                            # 버전·tag 없음 — ④dev:release가 fold + 최종 버전/tag.

CHANGELOG.md                # 루트 단일 (릴리스 전용, ④dev:release가 작성).
                            # release가 여러 fragment를 묶어 한 엔트리(`## vX.Y.Z — YYYY-MM-DD`)로 fold.

tactical/                       # 항상 HEAD (현재 본문)
├── system.md
├── verification-ledger.md      # 검증 원장 (완료 기준 × 면별 다중 단정·코더/verifier 2칸·해소 증거)
│                               # verification-criteria-writer 소유(두 칸 초기 -), coder가 코더 칸(채널1~3)·verifier가 verifier 칸 갱신. 커밋·누적·릴리스에서 산문 fold 안 함
├── domain/
│   ├── cross-domain/
│   │   ├── {비즈니스흐름}.md
│   │   ├── screens.md           # 화면 행위
│   │   └── ui.md                # 화면 시각 상세설계 (프론트 흐름)
│   └── {도메인}/
│       ├── rules.md
│       ├── entities.md
│       ├── scenarios.md
│       ├── api.md
│       ├── screens.md           # 화면 행위 (구성·표시 조건·인터랙션·폼 검증)
│       └── ui.md                # 화면 시각 상세설계 (레이아웃·컴포넌트·상태·위계·토큰 — 프론트 도메인만)
└── service/
    └── {서비스명}.md

tactical-archive/               # 본문 스냅샷 (read-only).
├── <스프린트 버전>/           # ①dev:tactical이 스프린트 시점에 갱신된 파일 본문을 그대로 복사.
│   └── {원래 상세설계 이하 경로}  # 예: 1.4.0-add-discount/domain/order/rules.md
└── v{X.Y.Z}/                 # ④dev:release가 fold 시 최종 선형 버전으로 정리.
    └── {원래 상세설계 이하 경로}
```

#### 테스트 체계

| 단계 | 담당 | 유형 | 환경 |
| ---- | ---- | ---- | ---- |
| 구현 (②dev:implement) | coder (회귀 단위테스트 함께 소유) | 코드 레벨 (순수 격리 로직 + 계약-정합; 실 통합 seam mock 금지) — **회귀 보조, done 증거 아님** | 환경 불필요 (DB·풀스택 불요) |
| 검증 (③dev:verify) | verifier | 시나리오/E2E 3면(UI/UX·로직·데이터) 실채널 (실제 기동) — **done 판정** | local-service-deployer 환경 |

## 전체 흐름 (dev:run — ⓪설계 → ①상세설계 → ②구현 → ③검증 → ④릴리스)

```
요구사항 (외부 인입도 요구사항으로 취급 · 강제사항 포함 가능)
   │
dev:run  (한 세션 · vX.Y.Z 보유)
   ⓪ dev:design   요구사항 → design/design.md(+ 완료 기준 3면) + 범위 묶음 + version bump   (항상 수행 · 사람 검토 게이트)
   ① dev:tactical     design/design.md → tactical/ + 검증 원장(완료 기준→면별 다중 단정·채널 사다리) + fragment + tactical-archive   (writer = 프론티어 배치 병렬)
   ② dev:implement 상세설계 → 코드 + 회귀 단위테스트(coder 소유) + 원장 단정(채널1~3) 코더 칸 (fragment 코드·마이그레이션. 구현 단위 = 프론티어 배치 병렬)
   ③ dev:verify   deploy + 원장의 면별 다중 단정 채널별 집행 + 원장 verifier 칸 갱신
   ④ dev:release  CHANGELOG fold(+ 가정한 값) + 경계 대조 게이트(--boundary release = 커버리지 COV + 원장 L1~L7) + git tag vX.Y.Z + 정리
```

1. `dev:design`이 요구사항을 분석 → `design/design.md`(전략 설계) + version bump 산정. 외부 인입도 요구사항으로 취급(skip 없음), 강제사항은 `[입력 강제]`로 수용. 구조적 L3는 여기서 개발자에게 받음(유일한 사람 검토 게이트)
2. `dev:tactical`이 `design/design.md`를 분석하여 `tactical/` + 스프린트 fragment 생성 — verification-criteria-writer가 완료 기준을 **검증 원장(`tactical/verification-ledger.md`)**의 **면별 다중 단정**(`T<n>` 절차→관측→기대, 채널 사다리 1~5)으로 분해(cross-cutting 최후미), tactical-verifier가 원장을 감사(면별 다중 단정 완비·완료 기준 커버리지·통합 seam·계약 미결·누적 승계·채널 하향 정당성). writer 위임은 프론티어 배치로 병렬. 잔여 결정은 가정하거나 상위 모순이면 ⓪전략설계로 bubble-up
3. `dev:implement`로 구현 + **회귀 단위테스트(coder가 함께 소유)** — coder가 원장 담당 단정(채널 1~3)을 T-n 회귀테스트로 통과 증명·**코더 칸** 기록(구현 단위는 프론티어 배치 병렬) → fragment에 코드·마이그레이션 기록 (코더 칸 PASS·회귀테스트 PASS는 "구현됨·미검증"이지 done이 아님 — 실 통합 seam은 mock으로 지우지 않음)
4. `dev:verify`가 구현 직후 같은 세션에서 deploy + 시나리오/E2E 검증 실행 (PASS여야 릴리스) — 판정은 **PASS/FAIL뿐**이며 "조건부 PASS" 같은 절충 상태를 만들지 않는다. UI 채널은 **실 런타임(실제 앱)을 선언된 드라이버로 끝까지 구동**해 확인하며 mock 단위 테스트로 대체할 수 없다(실 통합 seam은 mock 대체 불가). 미도달·보류·부분·mock 대체 등 **PASS 아닌 모든 상태는 release 차단**. UI 드라이버가 **호스트 키보드/마우스를 점유**하는 경우(네이티브 macOS XCUITest: 시뮬레이터 없이 호스트 직접 실행)에는 오케스트레이터가 그 UI 채널 **진입 전 개발자 허가**를 받고 진행(거부 시 보류, 생략 아님). 브라우저·iOS/Android는 무점유라 게이트 없음
5. `dev:release`가 보유한 `vX.Y.Z`로 CHANGELOG fold + tag. 단 fold·tag 전에 **경계 대조 게이트(`run_all.py --boundary release` = 커버리지 COV + `check_ledger.py` L1~L7)**가 검증 원장을 검사한다 — L1~L4(3면 완비·코더/verifier PASS 해소증거·계약 미결 0·미종결 단정 누적 승계)에 더해 **종결 게이트 L5(코더 종결·채널1~3)·L6(verifier 종결)·L7(보류=채널5+항목별 승인 토큰)**과 커버리지(요구사항→완료기준→원장 AC)까지 전량. 위반이거나 원장에 done 아닌 단정(코더 -/FAIL=미달성, verifier -/보류/미결=미검증)이 남으면 **자동 릴리스 차단**(done=verifier PASS·코더 PASS만으론 불가) — override는 **항목별 승인 토큰(`승인: <개발자>·<날짜>·<사유>`)으로만** 가능하며(포괄 override 폐지), 그때도 원장은 승계 유지하고 CHANGELOG에 **"미달성"과 "미검증"으로 구분** 명시(done 승격 금지). 검증 원장은 산문으로 녹이지 않고 `tactical-archive/vX.Y.Z/`로 스냅샷
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
- **오케스트레이터 상태 추적**: dev:run·dev:tactical·dev:implement 등 오케스트레이터는 에이전트 반환 시 결과 기록 → 다음 행동 판단 → 실행 순서를 따르고, 그 진행을 run-state에 start/done 마커로 남깁니다. 진행 상태가 개발자에게 표시되므로 잘못된 판단에 즉시 개입할 수 있습니다.
- **에이전트 재위임(완결 사이클)**: 각 에이전트 호출은 **완결 사이클**입니다 — 멈춰서 되묻지 않고 못 정한 것을 데이터(가정[]/미해결[])로 반환합니다. 다시 일을 시키는 트리거는 **결정론 신호**(테스트 FAIL·검증 위반)나 **bubble-up blocker**(물려받은 모순을 한 칸 위로)이며 **새 호출(재spawn)**로 진행합니다 — 세션 기반 resume(SendMessage)에 의존하지 않습니다. 잃으면 안 되는 맥락(FAIL 항목·blocker)은 run-state·상세설계 경로를 템플릿에 담아 전달하고, 에이전트가 tactical/·코드 파일에서 맥락을 회복합니다.

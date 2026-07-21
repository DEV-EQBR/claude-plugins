# 로컬 검증 환경

> 버전: v1.4.0
> 최종 수정: 2026-07-21
> 적용 조건: 다음 중 하나라도 해당하면 적용
> - `system.md` 의 "서비스 구성" 에 프로세스로 기동되는 서비스가 1개 이상 정의된 경우
> - 프론트엔드 서비스가 **네이티브 클라이언트-앱**(빌드 아티팩트를 런타임/시뮬레이터에 설치·실행)인 경우
> - 시나리오/E2E 검증을 로컬(또는 단일 검증 환경)에서 수행하는 경우

---

## 메타-규칙

검증 환경은 **결정론적·재현 가능·자가회복적**이어야 한다. 검증은 영속 개발 DB를 재사용하지 않고 **fresh(깨끗한) 검증 상태에 배포 시나리오(스키마·시드)를 적용**해 수행한다. 코드 변경이 수동 재기동 사이클 없이 반영되고, 재기동이 스키마·데이터를 파괴하지 않으며, 무응답 의존성에 무한 대기하지 않는다.

배포 시나리오(`schema.sql`·`seed.sql`·migration)는 검증 대상이다 — "이미 적용됐겠지"로 신뢰하지 않고, 매 검증마다 fresh 상태에 적용하여 의도한 상태가 나오는지 확인한다. 이로써 "정의는 있으나 DB 미적용" 같은 스키마 드리프트가 구조적으로 발생하지 않는다.

또한 검증 환경의 **고정 사실(포트맵·연결정보·health 경로·도구 경로·로그 조회법)을 선언**하여, deployer가 매 실행마다 환경을 재발견(`docker ps`·`psql -l`·`find /`·스트리밍 로그)하지 않고 선언값을 적용하게 한다. 미선언 시 재발견 비용과 포트 충돌이 반복된다. **fresh는 검증 DB 데이터에 한정**하고, 인프라 컨테이너·기동된 서비스는 재사용한다(전체 스택을 매번 새로 짓지 않는다).

검증 빌드는 **실패를 소리 없이 삼키지 않는다** — 에러·예외·실패 확정·경계 이탈은 구조화 **개발 진단 로그**로 관측 가능해야 한다. 이 로그는 **사실만** 담고 판정 로직을 담지 않으며(판정은 verify의 몫 — 모션 프로브와 같은 자기검증 방지 원칙), 검증 실패 시 코더·검증자가, 개발자가 직접 실행할 때 사용자가, **같은 로그를 조회 규약 하나로** 읽어 원인을 즉시 국소화한다. 개발 진단 로그는 **검증 빌드 한정·비영속**이라 제품 기능으로서의 에러 관측(사용자/어드민 대상·DB 영속·프라이버시 불변식)과는 목적·거처가 분리된다 — 후자는 제품 도메인(tactical/domain)에 살고, 전자는 이 검증 인프라 컨벤션이 소유한다.

---

## 결정 항목

이 컨벤션을 따르려면 다음 항목들을 결정하여 상세설계서에 명시해야 한다.

| 결정 항목 | 명시 위치 | 형태 / 제약 |
|----------|---------|-----------|
| 검증용 기동 방식 | `system.md` / 검증 환경 컨벤션 섹션 | 코드 변경이 재기동 사이클 없이 반영되는 방식인가(핫리로드/watch 등). 핫리로드 불가 서비스는 "변경 시 rebuild 후 재기동" 단일 경로를 명시 |
| 프로세스 매니저 | `system.md` / 검증 환경 컨벤션 섹션 | 검증 환경에서 서비스를 관리하는 도구를 **하나로 단일화**(혼재 금지). 무엇을 쓸지 명시 |
| 스키마 전략 | `system.md` / 검증 환경 컨벤션 섹션 | ORM auto-sync(synchronize 등) **금지**. 스키마는 `schema.sql`/migration으로만 표현·적용(재기동 비파괴) |
| 배포 시나리오 SQL 위치 | `system.md` / 검증 환경 컨벤션 섹션 | `schema.sql`·`seed.sql`(+ migration)의 경로 |
| 검증 상태 모델 | `system.md` / 검증 환경 컨벤션 섹션 | **fresh 검증 DB** 사용(영속 개발 DB 재사용 금지). 검증 DB 식별 방법과 검증 후 정리(teardown) 방식 |
| 의존성 대기 timeout | `system.md` / 검증 환경 컨벤션 섹션 | 외부 호출·헬스 대기에 timeout 명시(무응답 시 무한 대기 금지) |
| 배포 타깃 종류 | `system.md` / 검증 환경 컨벤션 섹션 | 각 배포 단위가 둘 중 무엇인가: `서비스-프로세스`(장기 실행 서버 — 기동 후 health 폴링) / `클라이언트-앱`(빌드 아티팩트를 런타임/시뮬레이터·에뮬레이터에 설치·실행 — 예: iOS·Android 네이티브 앱). deployer가 기동/빌드 방식과 readiness 검증 방식을 이 값으로 분기 |
| 검증 실행 도구 (채널별) | `system.md` / 검증 환경 컨벤션 섹션 | API/시스템 트리거 채널의 검증 실행 도구. 디폴트 권장: API=Hurl, 트리거=스크립트(timeout 포함). `verify-run` skill이 이 선언을 따른다(미선언 시 디폴트) |
| UI 검증 드라이버 (프론트 런타임별) | `system.md` / 검증 환경 컨벤션 섹션 | 프론트 서비스의 런타임 종류에 따른 UI 검증 드라이버. **브라우저 런타임**(웹·Electron/Tauri 등 웹뷰 래핑 포함) → 브라우저 자동화(디폴트 Playwright MCP / 연결된 브라우저 MCP). **네이티브(iOS)** → 네이티브 UI 자동화(검증 권장: `xcodebuild test` + XCUITest(`.tap()`), 시뮬레이터 lifecycle = `xcrun simctl`; 선언적 대안 = Maestro). **네이티브(Android)** → 네이티브 UI 자동화(검증 권장: `./gradlew connectedAndroidTest` + Espresso/UI Automator, 에뮬레이터 lifecycle = `avdmanager`·`emulator`·`adb`; 선언적 대안 = Maestro). **네이티브(macOS 데스크톱)** → 네이티브 UI 자동화(검증 권장: `xcodebuild test -destination 'platform=macOS'` + XCUITest(`.click()`), **시뮬레이터 없이 호스트 맥에서 직접 실행** — simctl 불필요). **호스트 입력 점유 분류**: 네이티브 macOS만 **점유형**(검증 중 호스트의 실제 키보드/마우스를 점유 → `dev:verify` 오케스트레이터의 진입 전 개발자 허가 게이트 대상). 브라우저(내부 합성)·네이티브 iOS/Android(시뮬레이터·에뮬레이터 내부)는 **무점유**. 미선언 시 브라우저 디폴트. `verify-run` skill이 이 선언으로 드라이버를 선택 |
| 클라이언트-앱 빌드/기동 (배포 타깃 = 클라이언트-앱인 경우) | `system.md` / 검증 환경 컨벤션 섹션 | 빌드 명령·대상 런타임·설치/기동 방법. iOS 예: 빌드+테스트 `xcodebuild test -scheme <S> -destination 'platform=iOS Simulator,name=<device>'`(시뮬레이터 빌드는 코드사이닝 불필요), 시뮬레이터 = `xcrun simctl`. Android 예: 빌드+설치+테스트 `./gradlew connectedDebugAndroidTest`(부팅된 에뮬레이터/실기기에 debug APK 자동 설치·실행, debug 빌드는 자동 생성 debug keystore로 서명 → 수동 서명 불필요), 에뮬레이터 = `avdmanager`·`emulator`·`adb`. macOS 예: 빌드+테스트 `xcodebuild test -scheme <S> -destination 'platform=macOS'`(시뮬레이터 없이 호스트 맥에서 직접 실행, 로컬은 ad-hoc 서명 `CODE_SIGN_IDENTITY=-`). readiness = 빌드 성공 + 앱 설치/기동 확인(서버 health 아님) |
| 모션 계측 프로브 (모션 불변식이 상세설계된 프론트 서비스) | `system.md` / 검증 환경 컨벤션 섹션 | `ui.md`에 모션 불변식(횟수·기하·시간 — `motion.md` 컨벤션)이 상세설계된 프론트 서비스는, 검증 빌드에서 모션의 **관찰 사실**(요소 등장/전이의 시작·끝 + 대상 identity, 정착 시점의 기하값)을 구조화 로그 한 줄로 출력하는 프로브를 갖춘다. **형식 고정**: `probe:<이벤트> key=value ...` — verify가 프로젝트 불문 같은 방식으로 파싱한다. 프로브는 사실만 출력하고 **판정 로직을 담지 않는다**(판정은 verify의 몫 — 구현 주체가 판정까지 쥐는 자기검증 방지). 상세설계할 것: 프로브 이벤트 목록, 출력 채널(어느 로그 스트림), 조회 방법 |
| 결정론적 UI 재생 모드 (모션 검증 대상 화면) | `system.md` / 검증 환경 컨벤션 섹션 | 모션 검증 대상 화면은 외부 의존(LLM·네트워크 등 비결정 입력) 없이 **고정 자극 시퀀스를 고정 간격으로 자동 재생**하는 수단(기동 인자 등)을 선언한다. 재생이 결정적이어야 불변식 판정이 재현 가능하고 회귀 검증이 된다. 앱이 스스로 진행하므로 UI 자동화 드라이버 없이 프로브 로그 검증이 가능 — 호스트 입력 점유형 드라이버의 점유 회피 수단이기도 하다. 상세설계할 것: 진입 방법, 재생 시나리오 내용(자극 목록·간격), 종료 조건 |
| 성능 측정 정책 | `system.md` / 검증 환경 컨벤션 섹션 | 검증 중 성능 지표(CPU/메모리) 수집 정책. **on/off**, **샘플 간격**(기본 1s), **대상 매핑**, **저장 경로**. 측정원은 native 도구 디폴트(추가 설치 0, 채택 전 정확도 확인). **백엔드/서비스**: 컨테이너=`docker stats`, pm2=`pm2 jlist`. **프론트(UI 검증 드라이버 런타임별, Docker 제한 비대상 — 절대값 기준)**: 네이티브 iOS·macOS=`ps`(앱 PID), Android=`adb top`(패키지), 웹=**CDP**(브라우저 JS heap+main-thread CPU). 웹은 브라우저를 `--remote-debugging-port=<P> --remote-allow-origins=* --enable-precise-memory-info`로 띄워야 함. `verify-run`의 `perf-sampler.py`가 이 선언을 따른다(미선언 시: on, 1s, docker 전체+pm2 전체). 시나리오별 귀속은 시작/종료 마커로 수행 |
| 서비스 포트맵 | `system.md` / 검증 환경 컨벤션 섹션 | 서비스→포트 **고정 할당 맵**. deployer가 동적 추론하지 않고 이 맵을 적용. 단일 세션=선언값 그대로, ad-hoc 병렬=인스턴스 키로 오프셋. 미선언 시 포트 충돌 |
| 연결정보 형식 | `system.md` / 검증 환경 컨벤션 섹션 | DB/Redis/MQ/S3 등 연결문자열 템플릿(호스트·포트·DB명 자리). deployer가 인스턴스별 값을 채워 `.env.local`에 기록 |
| 환경변수 로딩 | `system.md` / 검증 환경 컨벤션 섹션 | 앱이 deployer가 쓴 `.env.local`을 **우선 로드**함을 보장(예: NestJS `envFilePath: ['.env.local','.env']`, Next `.env.local`). deployer 값이 앱에 도달하지 못하면 포트/연결이 무시됨 |
| 서비스 health 경로 | `system.md` / 검증 환경 컨벤션 섹션 | 서비스별 헬스 엔드포인트(메서드 포함, 예 `GET /health/ready`). 완료 게이트·재사용 판단이 이걸로 확인 |
| 검증 도구 경로 | `system.md` / 검증 환경 컨벤션 섹션 | psql·docker 등 도구 경로(또는 "PATH에 있음"). `find /` 전체 스캔 금지 |
| 로그 조회 규약 | `system.md` / 검증 환경 컨벤션 섹션 | **스트리밍 금지** — 비차단 조회(예 `pm2 logs <svc> --nostream --lines N`). 스트리밍은 호출당 무한/장시간 블로킹 |
| 개발 진단 로그 (검증 대상 전 서비스/앱) | `system.md` / 검증 환경 컨벤션 섹션 | 검증 빌드에서 실패 취약 이음매(caught 예외·에러 확정 지점·외부/seam 호출 실패·시나리오 관련 핵심 상태 전이)의 **관찰 사실**을 구조화 한 줄로 출력하는 진단 로그를 갖춘다. **형식 고정**: `diag:<이음매> level=<info|warn|error> ...`(가능하면 `ac=<AC-n>`·`t=<T-n>` 상관 태그) — verify가 프로젝트 불문 같은 방식으로 파싱·발췌한다. **사실만 출력·판정 로직 없음**(판정은 verify — 모션 프로브와 동일 원칙). **검증 빌드 한정**(dev/verify 빌드에서만 컴파일/활성, release 미포함 — 빌드 플래그/환경으로 게이팅). 출력 채널·조회는 위 `로그 조회 규약`과 **동일 채널**(한 곳만 보면 됨). 상세설계할 것: 진단 이음매 목록, 빌드 게이팅 방법, 출력 채널, 비차단 조회 명령 |

---

## 상세설계 작성 예

결정의 결과가 상세설계서에 어떻게 박히는지 샘플.

```markdown
## 검증 환경 컨벤션

| 항목 | 정책 |
|------|------|
| 검증용 기동 방식 | 백엔드: `start:dev`(watch) 핫리로드. 핫리로드 불가 서비스 없음 |
| 프로세스 매니저 | pm2 단일 (검증 환경에서 직접 nest/node 기동 혼용 금지) |
| 스키마 전략 | TypeORM `synchronize: false`. 스키마는 `db/schema.sql` + `db/migrations/*` 로만 적용 |
| 배포 시나리오 SQL | `db/schema.sql`, `db/seed.sql`, 마이그레이션 `db/migrations/` |
| 검증 상태 모델 | fresh 검증 DB `<project>_verify` 를 매 검증마다 생성 → schema/seed 적용 → 검증 후 drop. 영속 `<project>_dev` 는 검증에 사용하지 않음 |
| 의존성 대기 timeout | 헬스 대기 30s, 외부 호출 10s (초과 시 즉시 실패 처리) |
| 배포 타깃 종류 | 백엔드 서비스 = 서비스-프로세스. admin-web = 서비스-프로세스(Next dev 서버) |
| 검증 실행 도구 | API=Hurl, 시스템 트리거=스크립트(`curl --max-time`) |
| UI 검증 드라이버 | admin-web(브라우저 런타임) = Playwright MCP / 연결된 브라우저 MCP |
| 성능 측정 정책 | on, 간격 1s. 대상: docker 컨테이너 전체(infra) + pm2 프로세스 전체(서비스). 저장 `.dev/<버전>/perf/`. 도구 = `perf-sampler.py`(docker stats + pm2 jlist). 시나리오별 마커로 귀속 |
| 서비스 포트맵 | gateway 3100, core 3010, blockchain-layer 3011, external-integration 3002, audit 3200, admin-web 3001 |
| 연결정보 형식 | DB `postgresql://dev:dev@127.0.0.1:<port>/<project>_verify`, Redis `redis://127.0.0.1:<port>/0` |
| 환경변수 로딩 | NestJS `envFilePath: ['.env.local', '.env']`, admin-web(Next) `.env.local` 우선 |
| 서비스 health 경로 | 각 서비스 `GET /health/ready` (gateway는 `OPTIONS`) |
| 검증 도구 경로 | psql·docker는 PATH. 스펙 검증 스크립트 = `plugins/dev/scripts/run_all.py` |
| 로그 조회 규약 | `pm2 logs <svc> --nostream --lines 100` (스트리밍 금지) |
| 개발 진단 로그 | 검증 빌드(`NODE_ENV!=production`)에서 실패 이음매를 `diag:<이음매> level=<lvl> ac=<AC-n> ...`로 stdout에 출력(pm2가 수집). 이음매 = 전역 예외 필터·실패 확정 catch·외부 호출 실패·핵심 상태 전이. 조회 = 로그 조회 규약과 동일(`pm2 logs <svc> --nostream --lines 100`). release 빌드 미포함 |
```

모션 불변식이 상세설계된 프론트 서비스가 있는 경우의 추가 행 (예: 대화 화면의 턴 추가 모션 — 플랫폼 무관, 출력 채널·기동 인자만 프로젝트별로 달라짐).

```markdown
## 검증 환경 컨벤션 (모션 계측 추가분)

| 항목 | 정책 |
|------|------|
| 모션 계측 프로브 | kiosk-client 검증 빌드에서 출력: `probe:appear id=<턴ID> bottom=<y>` (턴 뷰 등장 시) · `probe:settle visible_bottom=<y>` (스크롤 정착 시). 출력 채널 = 앱 표준 로그 스트림, 조회 = 로그 조회 규약과 동일(비차단) |
| 결정론적 UI 재생 모드 | 기동 인자 `--demo-replay conversation` — 고정 대화 턴 5개(사용자/아바타 교대)를 1s 간격 주입, LLM·네트워크 미사용. 마지막 턴 주입 후 2s 뒤 자동 종료 |
```

프론트엔드가 **네이티브 클라이언트-앱(iOS)**인 경우의 추가/대체 행 (실측 검증된 도구):

```markdown
## 검증 환경 컨벤션 (iOS 네이티브 프론트 추가분)

| 항목 | 정책 |
|------|------|
| 배포 타깃 종류 | 모바일 앱 = 클라이언트-앱 (시뮬레이터에 빌드·설치·실행) |
| UI 검증 드라이버 | 네이티브 UI 자동화 = `xcodebuild test` + XCUITest (접근성 식별자 셀렉터). 시뮬레이터 lifecycle = `xcrun simctl` |
| 클라이언트-앱 빌드/기동 | `xcodebuild test -scheme <App> -destination 'platform=iOS Simulator,name=iPhone 17'` — 시뮬레이터 자동 부팅·빌드·UITest 실행. 시뮬레이터 빌드는 코드사이닝/프로비저닝 프로파일 불필요 |
| 클라이언트-앱 readiness | 빌드 성공 + 앱이 시뮬레이터에 설치·기동됨 (서버 health 엔드포인트 아님) |
| 검증 도구 경로 | `xcodebuild`·`xcrun simctl`은 Xcode CLT(PATH). 프로젝트 생성이 필요하면 `xcodegen` 등 |
```

프론트엔드가 **네이티브 클라이언트-앱(Android)**인 경우의 추가/대체 행 (실측 검증된 도구):

```markdown
## 검증 환경 컨벤션 (Android 네이티브 프론트 추가분)

| 항목 | 정책 |
|------|------|
| 배포 타깃 종류 | 모바일 앱 = 클라이언트-앱 (에뮬레이터에 빌드·설치·실행) |
| UI 검증 드라이버 | 네이티브 UI 자동화 = `./gradlew connectedAndroidTest` + Espresso/UI Automator (resource-id/content-description 셀렉터). 에뮬레이터 lifecycle = `avdmanager`(AVD 생성)·`emulator`(부팅)·`adb`(제어·`sys.boot_completed` 폴링) |
| 클라이언트-앱 빌드/기동 | `./gradlew connectedDebugAndroidTest` — 부팅된 에뮬레이터에 debug APK + test APK 자동 설치 후 instrumented test 실행. debug 빌드는 자동 생성 debug keystore로 서명되어 수동 코드 서명 불필요 (헤드리스 부팅 예: `emulator @<AVD> -no-snapshot -no-boot-anim`; Espresso 안정화를 위해 애니메이션 0 권장 — 아래 주의 참조) |
| 클라이언트-앱 readiness | 빌드 성공 + 앱이 에뮬레이터에 설치·기동됨 (서버 health 엔드포인트 아님) |
| 검증 도구 경로 | `adb`·`emulator`는 Android SDK(`$ANDROID_HOME/platform-tools`·`/emulator`), `avdmanager`·`sdkmanager`는 cmdline-tools. 빌드는 프로젝트 `./gradlew` |
```

> **Android UI 검증 실전 주의 (실측으로 확인된 함정 — 둘 다 안 하면 탭이 빗나가 PASS가 안 나온다)**:
> 1. **시스템바/edge-to-edge 인셋**: API 35+(Android 15)는 edge-to-edge가 기본이라, `screen-layout.md`의 "시스템 예약 영역(safe area)"을 처리하지 않으면 화면 요소가 상태바·내비게이션바·액션바 뒤에 가려진다. 가려진 요소는 접근성 트리엔 보여 assert는 통과하지만 **주입 탭이 가림 요소(액션바 등)에 먹혀 onClick이 안 난다** → 시나리오가 "탭은 됐는데 상태 전이 없음"으로 실패. 앱은 `WindowInsets`로 콘텐츠를 safe area 안에 배치해야 한다.
> 2. **애니메이션 비활성화**: Espresso 표준 요건. 검증 전 `adb shell settings put global window_animation_scale 0`(+`transition_animation_scale`·`animator_duration_scale`)로 끈다.

프론트엔드가 **네이티브 클라이언트-앱(macOS 데스크톱)**인 경우의 추가/대체 행 (실측 검증된 도구):

```markdown
## 검증 환경 컨벤션 (macOS 네이티브 프론트 추가분)

| 항목 | 정책 |
|------|------|
| 배포 타깃 종류 | 데스크톱 앱 = 클라이언트-앱 (호스트 맥에서 직접 빌드·실행 — 시뮬레이터/에뮬레이터 없음) |
| UI 검증 드라이버 | 네이티브 UI 자동화 = `xcodebuild test -destination 'platform=macOS'` + XCUITest. macOS는 `.click()` 사용(`.tap()`은 iOS 전용). 셀렉터 = `accessibilityIdentifier` |
| 클라이언트-앱 빌드/기동 | `xcodebuild test -scheme <App> -destination 'platform=macOS'` — 호스트 맥에서 앱을 띄워 UITest 실행. 로컬은 ad-hoc 서명(`CODE_SIGN_IDENTITY=-`, hardened runtime off) |
| 클라이언트-앱 readiness | 빌드 성공 + 앱이 호스트에서 기동됨 (서버 health 엔드포인트 아님) |
| 호스트 입력 점유 | **점유형** — XCUITest가 호스트 세션의 실제 키보드/마우스를 점유(개발자가 검증 중 다른 작업 동시 불가). `dev:verify` 오케스트레이터가 이 UI 채널 진입 **전에 개발자 허가**를 받는다(허가 없이 진입 금지, 거부 시 보류). |
| 검증 도구 경로 | `xcodebuild`은 Xcode CLT(PATH). 프로젝트 생성이 필요하면 `xcodegen` 등. UITest는 호스트의 Accessibility 권한이 필요할 수 있음(GUI 세션 전제) |
```

> **런타임 분류 주의 — "맥/데스크톱에서 도는 앱"을 OS로 단정하지 말 것**: UI 드라이버는 OS가 아니라 *런타임*으로 갈린다.
> - **네이티브 macOS**(AppKit/SwiftUI for macOS, Mac Catalyst) → 위 macOS 드라이버(XCUITest, `platform=macOS`). iOS와 도구 패밀리는 같지만 destination·`.click()`·시뮬레이터 부재가 다르므로 **iOS로 분류하지 않는다**.
> - **Electron/Tauri 등 웹뷰 래핑 데스크톱 앱** → 런타임이 브라우저(Chromium)이므로 **브라우저 자동화 드라이버**(Playwright 등)로 분류. macOS 네이티브 아님.
> - **iPhone/iPad 앱을 Apple Silicon 맥에서 그대로 실행** → iOS 런타임. iOS 드라이버 사용.

> **호스트 입력 점유 게이트 (네이티브 macOS 한정)**: 네이티브 macOS UI 검증은 시뮬레이터가 없어 호스트 맥에서 직접 XCUITest를 돌리므로 검증 중 **호스트의 실제 키보드/마우스를 점유**한다(개발자가 동시에 다른 작업 불가). 따라서 `dev:verify` 오케스트레이터는 이 UI 채널 진입 **전에** 개발자에게 허가를 묻고, 허가가 있을 때만 진입한다(거부 시 해당 채널은 보류 — 생략 아님). 브라우저(브라우저 내부 합성)·iOS/Android(시뮬레이터·에뮬레이터 내부)는 호스트 입력을 점유하지 않으므로 게이트 대상이 아니다. 일반 규칙은 `skills/verify/SKILL.md`의 "호스트 입력 점유 채널 게이트"에 있다.

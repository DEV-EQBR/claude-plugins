---
name: verify-run
description: |
  검증 실행 절차. 검증 항목(시나리오·기대결과·채널)을 채널별 시나리오로 구동하여 실행·판정·보고한다.
  verifier가 시나리오/E2E 검증을 수행할 때 사용한다. 즉흥 셸 구현 대신 결정론적 절차와 재사용 템플릿을 제공한다.
  This skill should be used when running scenario/E2E verification — driving 검증 항목 through
  API/UI/trigger channels deterministically with timeouts and explicit assertions.
---

# 역할

검증 실행 절차. 검증 항목을 채널별 시나리오로 구동하여 실행·판정·보고한다. verifier가 "어떻게 실행하는가"를 매번 즉흥(셸 curl 등)으로 만들지 않도록, 결정론적 절차와 재사용 템플릿을 제공한다.

# 입력

- **검증 항목**: 검증 원장(`tactical/verification-ledger.md`)의 AC별 **3면(UI/UX·로직·데이터) 행**(검증항목·채널·상태·해소증거). verify-run은 항목을 도출하지 않고 원장에서 받은 각 면을 그 면의 채널로 구동한다(원장에 없거나 검증 불가면 verifier가 bubble-up 대상으로 반환). 시나리오 상세는 `scenarios.md` / `cross-domain/`을 참조한다.
- **검증 실행 도구**: `system.md` "검증 환경 컨벤션"의 채널별 검증 실행 도구 + **UI 검증 드라이버(프론트 런타임별)** 선언. 미선언 시 디폴트(UI: 브라우저 자동화 = Playwright MCP, API: Hurl, 트리거: 스크립트).
- **fresh 검증 상태**: deployer가 제공한 빈 검증 DB + schema 적용 + 서비스 기동.
- **성능 측정 정책**: `system.md` "검증 환경 컨벤션"의 성능 측정 정책(샘플 간격·대상 서비스 매핑·클라이언트-앱 PID/패키지·저장 경로) 선언. 미선언 시 디폴트(간격 1s, docker 컨테이너 전체 + pm2 전체, 클라이언트-앱은 채널에서 도출).

# 실행 절차

1. 검증 원장에서 각 AC의 3면(UI/UX·로직·데이터) 항목·채널을 읽는다 (verify-run은 항목을 도출하지 않는다 — 원장이 SoT).
2. fresh 검증 상태를 확인하고 `seed.sql`을 실행한다 — 배포 시나리오 검증(스키마·시드 적용 결과가 의도한 상태인지 확인). 불일치면 진행 불가로 보고한다.
3. **성능 샘플러를 백그라운드로 시작한다** (`templates/perf-sampler.py sample --out trace.jsonl --interval 1 ...`). 측정 대상은 `system.md` 포트맵·프로세스 매니저·성능 측정 정책 선언을 따른다. 측정값은 native 도구에서 수집(추가 설치 0, 실측 정확도 확인됨):
   - 백엔드/서비스: 컨테이너=`--container`(미지정 시 docker 전체, `docker stats`), pm2 프로세스=`--pm2`(`pm2 jlist`).
   - 프론트(UI 검증 드라이버 런타임별, Docker 제한 비대상 — 절대값 기준): 네이티브 iOS 시뮬레이터·macOS 호스트 앱=`--pid name=PID`(`ps`), 네이티브 Android=`--adb-pkg name=pkg`(`adb top`), **웹=`--cdp name=port`**(브라우저 클라이언트 JS heap + main-thread CPU, stdlib CDP). 네이티브 앱 PID는 시나리오 launch 후 해석(iOS=시뮬레이터 호스트 프로세스, Android=`adb shell pidof <pkg>`).
   - **웹(`--cdp`) 전제**: UI 드라이버가 브라우저를 `--remote-debugging-port=<port> --remote-allow-origins=* --enable-precise-memory-info`로 띄워야 한다(이 플래그 없으면 CDP 연결 불가/heap 부정확).
   성능 측정이 정책상 off면 생략한다.
4. 각 AC의 **3면(UI/UX·로직·데이터)**을 각자 채널로 나란히 구동·assert한다 (모든 외부 호출에 timeout 강제). 한 면 통과로 다른 면을 추론하지 않는다 — 프론트가 있어도 로직 면·데이터 면을 UI 채널과 **별도로** 실측한다. **각 시나리오 시작 직전 `perf-sampler.py mark --scenario <ID> --event start`, 종료 직후 `--event end`로 시간 경계를 기록**해 시나리오별 리소스 귀속이 가능하게 한다:
   - **로직 면 (실 API·통합 seam)** → 선언적 HTTP 시나리오 (`templates/api-scenario.hurl` 패턴). 실 API·실 seam을 요청 → 응답 assert(mock 대체 금지). 백엔드 비즈니스 로직·상태 전이·판정이 실제로 맞게 도는지 확인한다.
   - **데이터 면 (DB·전송 페이로드 실측)** → 영속 데이터는 DB 실조회로, 경계 전송 데이터는 실 페이로드로 값·형태·계약·정합을 assert한다. **통합 seam(백엔드↔클라이언트 계약)을 실 페이로드로 실측** — 백엔드 산출값이 경계를 넘어 정확히 전달·해석되는지(과거 붕괴 지점). 화면 추론·"저장됐겠지"로 대체 금지.
   - **UI/UX 면** → `system.md` 선언 **UI 검증 드라이버**로 구동한다. 사용자 진입점부터 종료점까지 진행하고 `screens.md`의 기대 상태와 일치하는지 **접근성 식별자(역할/라벨/accessibilityIdentifier) 기반**으로 assert. 중간 API 응답·눈대중 PASS 금지.
     - 브라우저 런타임(web) → 브라우저 자동화 (Playwright MCP 접근성 스냅샷 또는 `templates/ui-scenario-web.spec.ts`)
     - 네이티브(iOS) → `xcodebuild test` + XCUITest (`templates/ui-scenario-ios.swift`). 시뮬레이터는 `xcrun simctl`로 lifecycle 관리(또는 `xcodebuild test`가 destination으로 자동 부팅). 시뮬레이터 빌드는 코드사이닝 불필요
     - 네이티브(Android) → `./gradlew connectedAndroidTest` + Espresso/UI Automator (`templates/ui-scenario-android.kt`). 에뮬레이터는 `emulator @<AVD>`로 부팅 후 `adb wait-for-device` + `sys.boot_completed` 폴링. debug 빌드는 자동 debug keystore로 서명되어 수동 코드 서명 불필요. **검증 전 애니메이션 비활성화**(`adb shell settings put global window_animation_scale 0` 등)와 **앱의 시스템바 인셋 처리**(API 35+ edge-to-edge — 안 하면 요소가 가려져 탭이 빗나간다)가 전제. 탭이 빗나가면 화면 캡처(`adb exec-out screencap`)로 요소 가림을 먼저 확인
     - 네이티브(macOS 데스크톱) → `xcodebuild test -destination 'platform=macOS'` + XCUITest (`templates/ui-scenario-macos.swift`). 시뮬레이터 없이 호스트 맥에서 직접 실행. macOS는 `.click()` 사용(`.tap()` 아님). 로컬은 ad-hoc 서명(`CODE_SIGN_IDENTITY=-`). ※ **호스트 입력 점유형**: 이 드라이버는 호스트의 실제 키보드/마우스를 점유한다 — `dev:verify` 오케스트레이터의 진입 전 개발자 허가 게이트(`skills/verify/SKILL.md`)를 통과한 뒤에만 실행한다. ※ Electron/Tauri 등 웹뷰 래핑 맥 앱은 macOS 네이티브가 아니라 **브라우저 런타임**으로 분류
   - **시스템 트리거** → 트리거 발생 후 기대 결과(상태 전이·이벤트)를 확인.
5. **UI 시각 품질 게이트** (프론트 레이어가 있는 도메인 의무 — 행위 검증 통과 후 수행). 각 주요 화면에 대해 ui.md/디자인 정책 기준으로:
   - **상태 커버리지 실측**: 화면의 핵심 상태(기본·빈·로딩·에러)를 실제로 구동하여 각 상태가 ui.md/정책대로 표현되는지 assert. 빈 상태가 흰 화면인지, 로딩이 레이아웃 점프인지, 에러가 멈춤인지 잡는다(눈대중 금지).
   - **접근성 자동 감사**: a11y 베이스라인(대비 WCAG AA·역할·라벨·터치 타깃)을 자동 감사 도구로 측정한다 — 웹=axe-core 주입(`templates/ui-visual-web.spec.ts`), 네이티브=플랫폼 접근성 감사(iOS/macOS Accessibility Audit, Android Accessibility Scanner/`UiAutomator` 검사). 위반은 시각 결함으로 집계.
   - **스크린샷 캡처**: 각 상태 화면을 캡처하여 아티팩트로 저장하고, ui.md의 레이아웃·컴포넌트 매핑·시각 위계·토큰 사용과 대조한다(토큰 이탈·1차 액션 다중 등 정책 위반 식별).
   - **모션 불변식 실측** (ui.md에 모션 불변식이 상세설계된 화면): `templates/motion-probe-assert.md`의 절차를 따른다 —
     ① *계측기 정합 확인*: 프로브(`probe:<이벤트> key=value ...`)가 상세설계된 이벤트(요소 등장·정착 기하)에 올바르게 붙어 있는지 소스로 확인한다(잘못 심긴 프로브의 깨끗한 로그는 무의미).
     ② *결정론적 재생*: system.md 선언 **결정론적 UI 재생 모드**(기동 인자 등)로 구동한다 — 외부 의존 없이 앱이 스스로 진행하므로 UI 드라이버 불필요(호스트 입력 점유 없음).
     ③ *프로브 로그 수집*: 선언된 출력 채널에서 비차단 조회한다 (예: iOS 시뮬레이터=`xcrun simctl spawn <UDID> log show/stream --timeout`, macOS 호스트 앱=`log show --predicate` 또는 stdout 리다이렉트, Android=`adb logcat -d`, 웹=UI 드라이버의 콘솔 메시지 캡처). **이 비차단 수집은 개발 진단 로그(`diag:` 라인)도 같은 채널에서 함께 걷는다**(모션 프로브 `probe:`와 동일 조회 — system.md 로그 조회 규약). 어떤 단정이든 FAIL 진단 시 이 채널에서 `diag:` 라인을 `ac`/`t` 태그로 발췌해 실패 국소화에 쓴다(`verifier.md` 실패 진단).
     ④ *불변식 assert*: `probe:` 라인을 파싱해 상세설계의 각 불변식을 판정한다 — **횟수**(이벤트 카운트: 신규 identity당 등장 1회·기존 identity 재등장 0회), **기하**(좌표 비교: 요소 경계 vs 가시 영역), **시간**(타임스탬프 차 vs 상한). 위반은 수치로 집계한다("등장 2회", "잘림 12pt", "정착 480ms > 상한 300ms").
     모션 판정을 스크린샷·프레임 추출의 눈 판독으로 하지 않는다(시간·공간 해상도 부족 — 보조 증거로만). 프로브·재생 모드가 구현에 없으면 우회하지 않고 **구현 누락 결함**으로 보고한다(도구 제한 아님 — coder 재구현 대상). 상세설계의 "사람 확인 항목"은 판정하지 않고 그대로 전달한다.
   - axe류 감사 도구/스크린샷 수단이 환경에 부재·미연결이면 자체 우회하지 않고 "도구 제한"으로 반환한다.
6. 각 AC 면의 기대 결과를 **명시적 assert**로 판정하여 면별(UI/UX·로직·데이터) 통과/실패를 집계한다 (응답·화면·저장값을 눈대중으로 PASS 처리 금지). 시각 결함도 행위 실패와 동일하게 집계한다. AC는 3면 전부 PASS여야 done — 한 면이라도 실측 없이 남으면 그 면을 미도달/보류로 집계한다.
7. 시나리오 간 상태를 격리한다 (`templates/state-reset.md` — 고유 식별자 또는 재시드).
8. **성능 샘플러를 정지하고 보고서를 생성한다**: 샘플러에 SIGTERM → `perf-sampler.py report --trace trace.jsonl --markers markers.jsonl --out perf-report.md`. 서비스별·시나리오별 CPU/메모리(avg/peak)와 전구간 시계열 요약이 나온다.
9. 결과를 보고한다 — AC별 **면별(3면: UI/UX·로직·데이터) 판정 + 해소증거**(실채널 실행 참조) + 실패는 **재현법**(시나리오 파일·요청·응답·화면 상태·DB/페이로드 실측값) + **시각 결함**(화면·상태·스크린샷 위치·a11y 위반) + **성능 보고**(서비스 단위 CPU/메모리, 시나리오별 리소스, 전구간 추이)를 포함한다. 성능 수치 caveat 명시: 샘플링 기반(avg/peak·추이 신뢰), docker MEM은 절대 사용량(MB) 기준이며 MEM%의 분모는 Docker VM(호스트 전체 아님).

# 도구 선택

- `system.md` "검증 환경 컨벤션"의 검증 실행 도구 + UI 검증 드라이버(프론트 런타임별) 선언을 따른다.
- 미선언 시 디폴트: UI = 브라우저 자동화(Playwright MCP), API = Hurl, 트리거 = 스크립트(timeout 포함).
- UI 드라이버는 프론트 런타임으로 갈린다: 브라우저 런타임(웹·Electron 등 웹뷰 래핑) → 브라우저 자동화, 네이티브(iOS) → `xcodebuild test` + XCUITest(+ `xcrun simctl`), 네이티브(Android) → `./gradlew connectedAndroidTest` + Espresso/UI Automator(+ `emulator`·`adb`), 네이티브(macOS) → `xcodebuild test -destination 'platform=macOS'` + XCUITest(`.click()`, 호스트 직접 실행). "맥/데스크톱에서 돈다"는 이유로 iOS로 분류하지 않는다(런타임 기준).
- 환경에 도구가 없으면(미설치·미연결: 브라우저 MCP 미연결 / Xcode·시뮬레이터 부재 / Android SDK·에뮬레이터 부재 등) 자체 우회(브라우저 강제 종료·프로필 재설정 등)하지 않고 "도구 제한"으로 반환한다.

# 번들 템플릿

| 파일 | 용도 |
|------|------|
| `templates/api-scenario.hurl` | API 채널 — 선언적 요청+assert+timeout 예시 |
| `templates/ui-scenario-web.spec.ts` | UI 채널 (브라우저 런타임) — Playwright 시나리오 골격(접근성 기반 셀렉터) |
| `templates/ui-visual-web.spec.ts` | UI 시각 품질 게이트 (브라우저 런타임) — 상태 커버리지 실측 + axe-core 접근성 감사 + 스크린샷 캡처 골격 |
| `templates/ui-scenario-ios.swift` | UI 채널 (iOS 네이티브) — XCUITest 시나리오 골격(`accessibilityIdentifier` 셀렉터). `xcodebuild test`로 실행 |
| `templates/ui-scenario-android.kt` | UI 채널 (Android 네이티브) — Espresso 시나리오 골격(resource-id/content-description 셀렉터). `./gradlew connectedAndroidTest`로 실행 |
| `templates/ui-scenario-macos.swift` | UI 채널 (macOS 네이티브) — XCUITest 시나리오 골격(`accessibilityIdentifier` 셀렉터, `.click()`). `xcodebuild test -destination 'platform=macOS'`로 실행 |
| `templates/motion-probe-assert.md` | UI 시각 품질 게이트 — 모션 불변식 실측 패턴 (프로브 로그 형식·수집·파싱·횟수/기하/시간 assert, 플랫폼 무관) |
| `templates/state-reset.md` | 시나리오 간 상태 격리 패턴(고유 식별자·재시드) |
| `templates/perf-sampler.py` | 성능 측정 — 서비스/앱 단위 CPU/메모리 시계열 수집(sample) + 시나리오 마커(mark) + 서비스별·시나리오별·시계열 보고서(report, CSV 동시 출력). 수집원: `docker stats`(컨테이너)·`pm2 jlist`(프로세스)·`ps`(네이티브앱 macOS·iOS 시뮬레이터)·`adb top`(Android 앱)·**CDP**(웹 브라우저 JS heap+main-thread CPU, stdlib WebSocket). 표준 라이브러리만(pip 불필요) |

템플릿은 예시/패턴이다. 프로젝트가 system.md에 다른 도구를 선언했으면 그 도구로 같은 절차를 따른다 (도구 비고정).

# 원칙

- 즉흥 셸로 시나리오를 돌리지 않는다. 정의된 채널 도구 + 템플릿으로 재현 가능하게 실행한다.
- 각 AC는 3면(UI/UX·로직·데이터)을 각자 채널로 실측한다. 한 면 통과로 다른 면을 추론하지 않는다 — 로직 면=실 API·seam, 데이터 면=DB·페이로드 실측을 UI 채널과 나란히 구동한다. 검증 항목은 원장에서 받으며 verify-run이 도출하지 않는다.
- 모든 외부 호출에 timeout을 둔다. 무응답 시 무한 대기하지 않는다.
- 비즈니스 엔티티는 실제 API로 생성한다. 배포 시나리오 SQL(schema/seed)은 fresh 검증 상태에서만 실행하며 개발자의 영속 데이터를 파괴하지 않는다.
- 판정은 명시적 assert로 한다.
- 성능 지표는 검증과 같은 실런타임 환경에서 수집한다(별도 합성 부하 아님). 측정원은 native 도구로 고정하지 않되, 채택 전 실제 출력으로 정확도를 확인한다(되는 것만). 수집 자체가 검증 부하를 왜곡하지 않도록 폴링 간격을 과도하게 줄이지 않는다(기본 1s).

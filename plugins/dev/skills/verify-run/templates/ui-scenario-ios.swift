// UI 채널 시나리오 템플릿 (iOS 네이티브 — XCUITest)
// 검증 항목 → 사용자 진입점부터 종료점까지 구동, screens.md 기대 상태 assert.
// 접근성 식별자(accessibilityIdentifier) 셀렉터 사용 — 픽셀 좌표·취약 텍스트 매칭 지양.
//
// 실행 (시뮬레이터 자동 부팅·빌드·테스트, 코드사이닝 불필요):
//   xcodebuild test \
//     -scheme <App> \
//     -destination 'platform=iOS Simulator,name=iPhone 17' \
//     -resultBundlePath /tmp/verify.xcresult
//
// 시뮬레이터 lifecycle을 직접 다뤄야 하면 xcrun simctl 사용:
//   xcrun simctl boot 'iPhone 17';  xcrun simctl shutdown all
//
// 전제: 앱 코드가 검증 대상 요소에 .accessibilityIdentifier("...")를 부여한다
//   (SwiftUI 예: Button("실행") { … }.accessibilityIdentifier("executeButton"))

import XCTest

final class TransferUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    // SC-005 송금 실행 — 실행 후 진행중 상태가 화면에 표시
    func testExecuteShowsInProgress() throws {
        let app = XCUIApplication()
        // 전제 상태(시드 사용자/송금)는 실제 API로 구성하거나 launch 인자로 주입
        // app.launchEnvironment["VERIFY_BASE_URL"] = "http://127.0.0.1:3100"
        app.launch()

        // 사용자 진입점 → 종료점까지 진행
        app.buttons["executeButton"].tap()

        // screens.md 기대 상태 assert (눈대중 금지, timeout 강제)
        XCTAssertTrue(
            app.staticTexts["statusLabel"].waitForExistence(timeout: 10),
            "실행 후 '진행중' 상태가 화면에 표시되어야 한다 (screens.md 기대 상태)"
        )
    }
}

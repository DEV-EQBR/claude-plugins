// UI 채널 시나리오 템플릿 (Android 네이티브 — Espresso)
// 검증 항목 → 사용자 진입점부터 종료점까지 구동, screens.md 기대 상태 assert.
// resource-id / content-description 셀렉터 사용 — 픽셀 좌표·취약 텍스트 매칭 지양.
//
// 실행 (부팅된 에뮬레이터/실기기에 debug APK + test APK 자동 설치·실행, 수동 코드 서명 불필요):
//   ./gradlew :app:connectedDebugAndroidTest
//
// 에뮬레이터 lifecycle을 직접 다뤄야 하면 emulator/adb 사용 (헤드리스 부팅 + 준비 대기):
//   emulator @<AVD> -no-snapshot -no-boot-anim &
//   adb wait-for-device
//   until [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 ]; do sleep 2; done
//
// ⚠️ 실측으로 확인된 전제 — 둘 중 하나라도 빠지면 "탭은 수행됐는데 onClick 미발화 → 상태 전이 없음"으로 실패한다:
//   1) 애니메이션 비활성화 (Espresso 표준 요건):
//        adb shell settings put global window_animation_scale 0
//        adb shell settings put global transition_animation_scale 0
//        adb shell settings put global animator_duration_scale 0
//   2) 시스템바/edge-to-edge 인셋 처리 (API 35+ 기본 edge-to-edge):
//      앱이 WindowInsets로 콘텐츠를 safe area 안에 배치하지 않으면, 요소가 상태바·내비바·액션바
//      뒤에 가려져 접근성 트리엔 보이지만(assert는 통과) 주입 탭이 가림 요소에 먹혀 클릭이 빗나간다.
//      → 탭이 안 먹으면 `adb exec-out screencap -p > s.png` 로 요소 가림부터 의심.
//
// 전제: 앱 코드가 검증 대상 요소에 안정적 셀렉터를 부여한다
//   (XML 예: android:id="@+id/executeButton"  /  Compose 예: Modifier.testTag("executeButton"))

package com.example.app

import androidx.test.core.app.ActivityScenario
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class TransferUiTest {

    // SC-005 송금 실행 — 실행 후 진행중 상태가 화면에 표시
    @Test
    fun executeShowsInProgress() {
        // 전제 상태(시드 사용자/송금)는 실제 API로 구성하거나 launch 인자로 주입
        ActivityScenario.launch(MainActivity::class.java).use {
            // 사용자 진입점 → 종료점까지 진행 (resource-id 셀렉터, 실제 탭)
            onView(withId(R.id.executeButton)).perform(click())

            // screens.md 기대 상태 assert (눈대중 금지)
            onView(withId(R.id.statusLabel)).check(matches(withText("진행중")))
        }
    }
}

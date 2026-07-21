// UI 시각 품질 게이트 템플릿 (브라우저 런타임 — Playwright + axe-core)
// 행위 검증(ui-scenario-web.spec.ts)을 통과한 화면에 대해, 시각 품질을 실측한다.
// 본 게이트가 보는 것: (1) 상태 커버리지 실측 (2) 접근성 자동 감사 (3) 스크린샷 캡처(시각 상세설계 정합 대조용).
// 시각 결함은 행위 결함과 동일하게 PASS 차단 사유다.
//
// 의존: @playwright/test, @axe-core/playwright (환경에 없으면 "도구 제한"으로 반환).
// 실행 예: playwright test ui-visual-web.spec.ts --timeout=30000
// (Playwright MCP를 쓰는 경우: 같은 화면을 접근성 스냅샷으로 구동하고, axe 주입 + 스크린샷 캡처를 동일하게 수행)

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const BASE = process.env.VERIFY_BASE_URL ?? 'http://127.0.0.1:5173'
const SHOTS = process.env.VERIFY_SHOT_DIR ?? 'verify-artifacts/visual'

// 화면별로 ui.md/디자인 정책의 상태 커버리지에 맞춰 핵심 상태를 구동한다.
// 각 상태는 "그 상태로 진입하는 방법"을 시나리오로 명시한다(빈 데이터 계정/네트워크 차단 등).
const SCREEN = '주문 목록'
const STATES: { name: string; enter: (page: import('@playwright/test').Page) => Promise<void>; expect: (page: import('@playwright/test').Page) => Promise<void> }[] = [
  {
    name: 'default',
    enter: async (page) => { await page.goto(`${BASE}/orders`) },
    // 정상 데이터: 목록 항목이 보인다
    expect: async (page) => { await expect(page.getByRole('list')).toBeVisible({ timeout: 10_000 }) },
  },
  {
    name: 'empty',
    enter: async (page) => { await page.goto(`${BASE}/orders?seed=empty`) },
    // 빈 상태: 흰 화면이 아니라 안내 + 다음 행동 (component-states 정책)
    expect: async (page) => {
      await expect(page.getByText(/아직.*없|주문이 없/)).toBeVisible({ timeout: 10_000 })
      await expect(page.getByRole('button', { name: /주문|시작/ })).toBeVisible()
    },
  },
  {
    name: 'loading',
    enter: async (page) => {
      // 응답을 지연시켜 로딩 상태를 강제 — 스켈레톤이 레이아웃을 보존하는지 본다
      await page.route('**/api/**', async (route) => { await new Promise((r) => setTimeout(r, 1500)); await route.continue() })
      await page.goto(`${BASE}/orders`)
    },
    expect: async (page) => { await expect(page.getByTestId('skeleton').or(page.getByRole('status'))).toBeVisible({ timeout: 5_000 }) },
  },
  {
    name: 'error',
    enter: async (page) => {
      // 네트워크 실패 주입 — 멈춤/흰 화면이 아니라 에러 + 재시도 (component-states 정책)
      await page.route('**/api/**', (route) => route.abort())
      await page.goto(`${BASE}/orders`)
    },
    expect: async (page) => {
      await expect(page.getByText(/실패|오류|문제/)).toBeVisible({ timeout: 10_000 })
      await expect(page.getByRole('button', { name: /다시|재시도/ })).toBeVisible()
    },
  },
]

for (const state of STATES) {
  test(`[시각] ${SCREEN} — ${state.name} 상태`, async ({ page }, testInfo) => {
    await state.enter(page)

    // (1) 상태 커버리지 실측: 이 상태가 ui.md/정책대로 표현되는가 (누락 = 결함)
    await state.expect(page)

    // (2) 접근성 자동 감사: a11y-baseline 정책(대비 WCAG AA·역할·라벨) — 결정론적 신호
    const a11y = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze()
    if (a11y.violations.length) {
      console.log(`[a11y] ${SCREEN}/${state.name} 위반 ${a11y.violations.length}건:`,
        a11y.violations.map((v) => `${v.id}(${v.impact}) x${v.nodes.length}`).join(', '))
    }

    // (3) 스크린샷 캡처: ui.md의 레이아웃·컴포넌트 매핑·시각 위계·토큰 사용 대조용 아티팩트
    const shot = await page.screenshot({ fullPage: true })
    await testInfo.attach(`${SCREEN}-${state.name}.png`, { body: shot, contentType: 'image/png' })

    // 접근성 위반은 시각 결함 → PASS 차단. (심각도 임계는 a11y-baseline 정책 기준으로 조정)
    expect(a11y.violations, `${SCREEN}/${state.name} 접근성 위반`).toEqual([])
  })
}

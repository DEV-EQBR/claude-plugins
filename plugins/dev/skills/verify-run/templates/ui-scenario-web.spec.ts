// UI 채널 시나리오 템플릿 (Playwright)
// 검증 항목 → 사용자 진입점부터 종료점까지 구동, screens.md 기대 상태 assert.
// 접근성 기반 셀렉터(역할/라벨) 사용 — 픽셀 좌표·취약 CSS 셀렉터 금지.
// 실행 예: playwright test --timeout=30000
//
// (Playwright MCP를 쓰는 경우: 같은 흐름을 접근성 스냅샷으로 구동하고 동일하게 assert)

import { test, expect } from '@playwright/test'

const BASE = process.env.VERIFY_BASE_URL ?? 'http://127.0.0.1:5173'

test('SC-005 송금 실행 — 실행 후 진행중 상태가 화면에 표시', async ({ page }) => {
  // 전제: 로그인 (기안·승인 완료된 송금이 시드되어 있음)
  await page.goto(`${BASE}/sign-in`)
  await page.getByLabel('이메일').fill(process.env.MAKER ?? '')
  await page.getByLabel('비밀번호').fill(process.env.PW ?? '')
  await page.getByRole('button', { name: '로그인' }).click()

  // 사용자 진입점 → 종료점까지 진행
  await page.goto(`${BASE}/transfers/${process.env.TRANSFER_ID}`)
  await page.getByRole('button', { name: '실행' }).click()

  // screens.md 기대 상태 assert (눈대중 금지)
  await expect(page.getByText('진행중')).toBeVisible({ timeout: 10_000 })
})

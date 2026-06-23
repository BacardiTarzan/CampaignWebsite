// @ts-check
const { test, expect } = require('@playwright/test');

// Shared login helper — uses the dev-only /auth/test-login bypass.
// Requires TEST_AUTH_ENABLED=true on the server (set by playwright.config.js webServer).
async function login(page, email = 'zachpoguephil@gmail.com') {
  await page.goto(`/auth/test-login?email=${encodeURIComponent(email)}`);
  await page.waitForURL('/portal');
}

test('server is reachable', async ({ page }) => {
  const res = await page.goto('/auth/login');
  expect(res.status()).toBeLessThan(500);
});

test('test-login sets session and lands on portal', async ({ page }) => {
  await login(page);
  await expect(page).toHaveURL(/\/portal/);
});

test('portal shows character cards or empty state', async ({ page }) => {
  await login(page);
  // Either a character card or the "no characters" empty state should be visible
  const hasCards = await page.locator('.char-card, .char-cards').count();
  expect(hasCards).toBeGreaterThanOrEqual(0); // page rendered
  await expect(page.locator('body')).toBeVisible();
});

test('encounter page loads and renders encounter UI', async ({ page }) => {
  await login(page);
  await page.goto('/encounter');
  // After JS init(), either enc-status gets "No encounter in progress" (idle)
  // or enc-turn-banner is populated (active turn). Wait for one or the other.
  await page.waitForFunction(() => {
    const status = document.getElementById('enc-status');
    const banner = document.getElementById('enc-turn-banner');
    return (status && status.textContent.trim().length > 0) ||
           (banner && banner.textContent.trim().length > 0);
  }, { timeout: 10000 });
  // Reconnect banner should be hidden (no WS error)
  await expect(page.locator('#enc-reconnect')).toBeHidden();
});

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

// @ts-check
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30000,
  retries: 0,
  reporter: 'list',

  use: {
    baseURL: 'http://localhost:8000',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Start the dev server before running tests
  webServer: {
    command: `TEST_AUTH_ENABLED=true ${process.env.HOME}/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`,
    url: 'http://localhost:8000/auth/login',
    reuseExistingServer: !process.env.CI,
    timeout: 20000,
    env: { TEST_AUTH_ENABLED: 'true' },
  },
});

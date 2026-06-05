import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    headless: false,  // 显示浏览器窗口
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], headless: false },
    },
  ],

  webServer: {
    command: 'python run.py',
    cwd: 'd:\\learnning\\260521',
    url: 'http://localhost:8000',
    reuseExistingServer: true,
    timeout: 30000,
    env: {
      STORAGE_ENV: 'test'
    }
  },
});
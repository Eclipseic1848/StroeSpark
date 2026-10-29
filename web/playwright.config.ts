import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173', channel: 'chromium', headless: true, trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  webServer: { command: 'npm run dev -- --port 5173 --strictPort', url: 'http://127.0.0.1:5173', reuseExistingServer: !process.env.CI, timeout: 30000 },
})

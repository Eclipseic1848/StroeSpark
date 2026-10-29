import { chromium, expect } from '@playwright/test'
import { mkdir, readFile, writeFile } from 'node:fs/promises'

// 仅用于已启动 tests/runtime_server.py 的手动联调，不拦截任何 API 请求。
const browser = await chromium.launch({ channel: 'chromium', headless: true })
const context = await browser.newContext({ viewport: { width: 1504, height: 1048 } })
const page = await context.newPage()
const runtimeErrors = []
const consoleErrors = []
page.on('pageerror', error => runtimeErrors.push(error.message))
page.on('console', message => { if (message.type() === 'error') consoleErrors.push({ text: message.text(), url: message.location().url }) })

try {
  await mkdir('test-results', { recursive: true })
  await page.goto('http://127.0.0.1:5173')
  await page.getByLabel('任务名称', { exact: true }).fill('浏览器联调测试')
  await page.getByLabel('宣传需求', { exact: true }).fill('浏览器联调测试：使用合成资料检查任务、素材、内容和导出，不代表真实商家需求。')
  await page.getByRole('button', { name: '创建任务', exact: true }).click()
  await expect(page.getByRole('heading', { name: '本次宣传需求' })).toBeVisible()
  await page.getByLabel('上传素材', { exact: true }).setInputFiles({ name: '浏览器联调资料.txt', mimeType: 'text/plain', buffer: Buffer.from('仅供浏览器联调使用。门店名称、菜品和价格均待商家确认。', 'utf8') })
  await expect(page.getByText('浏览器联调资料.txt', { exact: true })).toBeVisible()
  await page.getByRole('radio', { name: '提出方向', exact: true }).check()
  await page.getByRole('button', { name: '提出方向', exact: true }).click()
  await expect(page.getByText('本次处理已完成，结果已保存。', { exact: true })).toBeVisible()
  await page.getByRole('radio', { name: '生成文案', exact: true }).check()
  await page.getByRole('button', { name: '生成文案', exact: true }).click()
  const editor = page.getByLabel('内容正文', { exact: true })
  await expect(editor).not.toHaveValue('')
  await page.getByLabel('内容标题', { exact: true }).fill(' 浏览器联调保存回归 ')
  await editor.fill(' 浏览器联调人工修改：内容待商家确认。\n\n')
  await page.getByRole('button', { name: '保存内容修改', exact: true }).click()
  await expect(page.getByText('内容修改已保存。', { exact: true })).toBeVisible()
  await expect(page.getByLabel('内容标题', { exact: true })).toHaveValue('浏览器联调保存回归')
  await expect(editor).toHaveValue('浏览器联调人工修改：内容待商家确认。')
  await expect(page.getByRole('button', { name: '导出任务', exact: true })).toBeEnabled()
  const pendingDownload = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出任务', exact: true }).click()
  const download = await pendingDownload
  await download.saveAs('test-results/integration-export.md')
  expect(await readFile('test-results/integration-export.md', 'utf8')).toContain('浏览器联调人工修改：内容待商家确认。')
  await page.screenshot({ path: 'design/render-integration-desktop.png', fullPage: true })

  await page.getByLabel('补充信息或修改要求', { exact: true }).fill('测试 fixture：模型服务失败')
  await page.getByRole('radio', { name: '梳理需求', exact: true }).check()
  await page.getByRole('button', { name: '梳理需求', exact: true }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page.getByLabel('补充信息或修改要求', { exact: true })).toHaveValue('测试 fixture：模型服务失败')
  await expect(page.getByText('本次处理已完成，结果已保存。', { exact: true })).not.toBeVisible()
  await expect(editor).toHaveValue('浏览器联调人工修改：内容待商家确认。')
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: 'design/render-integration-mobile.png', fullPage: true })
  expect(runtimeErrors).toEqual([])
  expect(consoleErrors.filter(message => !message.text.includes('502'))).toEqual([])
  await writeFile('design/integration-result.json', JSON.stringify({ status: 'passed', apiInterception: false, runtimeErrors, consoleErrors, intentionalFailure: '模型 fixture 返回 502；未调用真实模型', viewport: ['1504x1048', '390x844'], checked: ['create', 'upload', 'direction', 'generate', 'trim-save', 'export', 'failure-preserves-input', 'mobile-overflow'] }, null, 2) + '\n', 'utf8')
  console.log('PASS: actual FastAPI + SQLite browser integration; only model transport is a test fixture')
} finally {
  await context.close()
  await browser.close()
}

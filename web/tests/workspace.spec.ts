import { test, expect } from '@playwright/test'
import type { Page } from '@playwright/test'
import type { TaskDetail } from '../src/types'

async function mockApi(page: Page, options: { authentication?: boolean; configured?: boolean } = {}) {
  const tasks: TaskDetail[] = []
  const state = { configured: options.configured ?? true, savedKey: '', attempts: 0, rejectNext: false, tokenRequired: options.authentication ?? false }
  await page.route('**/api/**', async route => {
    const request = route.request()
    const path = new URL(request.url()).pathname
    const send = (value: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(value) })
    if (state.tokenRequired && request.headers().authorization !== 'Bearer test-workspace-token') return send({ detail: '访问令牌无效' }, 401)
    if (path === '/api/v1/provider') {
      if (request.method() === 'PUT') { const value = request.postDataJSON(); state.savedKey = value.api_key ?? ''; state.configured = !!state.savedKey }
      return send({ provider: 'deepseek', base_url: 'https://api.deepseek.com', model: 'deepseek-flash', api_key_set: state.configured, source: state.configured ? 'saved' : 'default' })
    }
    if (path === '/api/v1/tasks') {
      if (request.method() === 'POST') {
        const value = request.postDataJSON()
        const task: TaskDetail = { ...value, id: String(tasks.length + 1), status: 'draft', created_at: '2026-10-28T00:00:00Z', updated_at: '2026-10-28T00:00:00Z', messages: [], materials: [], artifacts: [] }
        tasks.unshift(task)
        return send(task, 201)
      }
      return send(tasks)
    }
    const task = tasks.find(item => item.id === path.split('/')[4])
    if (!task) return send({ detail: '任务不存在' }, 404)
    if (path.endsWith('/materials')) {
      state.attempts += 1
      if (state.rejectNext) { state.rejectNext = false; return send({ detail: '文件上传未完成，请重试。' }, 413) }
      const material = { id: String(task.materials.length + 1), name: '门店资料.txt', media_type: 'text/plain', size: 24, created_at: '2026-10-28T00:00:00Z' }
      task.materials.push(material)
      return send(material, 201)
    }
    if (path.endsWith('/messages')) {
      const value = request.postDataJSON()
      task.messages.push({ id: String(task.messages.length + 1), role: 'user', content: value.content || '请继续当前任务', created_at: '2026-10-28T00:00:00Z' })
      if (value.content === '触发失败') return send({ detail: '模型服务暂时不可用，请稍后重试。' }, 502)
      task.messages.push({ id: String(task.messages.length + 1), role: 'assistant', content: '这是自动化测试使用的合成回复。', created_at: '2026-10-28T00:00:00Z' })
      if (value.action === 'generate') { task.status = 'content'; task.artifacts.push({ id: String(task.artifacts.length + 1), kind: 'copy', title: '测试文案', content: '仅用于自动化测试的合成内容，门店事实待确认。', created_at: '2026-10-28T00:00:00Z' }) }
      return send(task)
    }
    if (path.includes('/artifacts/')) {
      const artifact = task.artifacts.find(item => item.id === path.split('/').at(-1))!
      const value = request.postDataJSON()
      Object.assign(artifact, { title: value.title.trim(), content: value.content.trim() })
      return send(artifact)
    }
    if (path.endsWith('/export')) return route.fulfill({ contentType: 'text/markdown; charset=utf-8', body: `# ${task.title}\n\n${task.artifacts.at(-1)?.content ?? task.brief}` })
    return send(task)
  })
  return { tasks, state }
}

async function create(page: Page) {
  await page.getByLabel('宣传需求', { exact: true }).fill('我想宣传门店，但还没有确定方向。')
  await page.getByRole('button', { name: '创建任务', exact: true }).click()
  await expect(page.getByRole('heading', { name: '本次宣传需求' })).toBeVisible()
}

test('任务、素材、文案编辑、未保存保护和导出形成完整流程', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  const { tasks } = await mockApi(page)
  await page.setViewportSize({ width: 1504, height: 1048 })
  await page.goto('/')
  await expect(page.getByText('暂无任务', { exact: true })).toBeVisible()
  await page.screenshot({ path: 'design/render-empty-desktop.png', fullPage: true })
  await page.getByRole('button', { name: '创建任务', exact: true }).click()
  await expect(page.getByText('请写一句宣传需求，或选择一份已有素材。')).toBeVisible()
  await expect(page.getByLabel('宣传需求', { exact: true })).toBeFocused()
  await create(page)
  expect(tasks).toHaveLength(1)
  await page.getByLabel('上传素材', { exact: true }).setInputFiles({ name: '门店资料.txt', mimeType: 'text/plain', buffer: Buffer.from('店名等待商家确认。', 'utf8') })
  await expect(page.getByText('门店资料.txt', { exact: true })).toBeVisible()
  await page.getByRole('radio', { name: '生成文案', exact: true }).check()
  await page.getByRole('button', { name: '生成文案', exact: true }).click()
  const editor = page.getByLabel('内容正文', { exact: true })
  await expect(editor).toHaveValue(/合成内容/)
  await page.getByLabel('内容标题', { exact: true }).fill(' 新标题 ')
  await editor.fill('人工修改并等待商家核实的内容。\n\n')
  await page.getByRole('button', { name: '新建任务', exact: true }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByRole('button', { name: '继续编辑', exact: true })).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).not.toBeVisible()
  await expect(editor).toHaveValue('人工修改并等待商家核实的内容。\n\n')
  await expect(page.getByRole('button', { name: '导出任务', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: '保存内容修改', exact: true }).click()
  await expect(page.getByText('内容修改已保存。', { exact: true })).toBeVisible()
  await expect(page.getByLabel('内容标题', { exact: true })).toHaveValue('新标题')
  await expect(editor).toHaveValue('人工修改并等待商家核实的内容。')
  await expect(page.getByRole('button', { name: '导出任务', exact: true })).toBeEnabled()
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: '导出任务', exact: true }).click()
  expect((await download).suggestedFilename()).toMatch(/\.md$/)
  await page.screenshot({ path: 'design/render-task-desktop.png', fullPage: true })
  expect(errors).toEqual([])
})

test('模型失败保留输入，且不生成虚假成功或文案', async ({ page }) => {
  const { tasks } = await mockApi(page)
  await page.goto('/')
  await create(page)
  await page.getByLabel('补充信息或修改要求').fill('触发失败')
  await page.getByRole('button', { name: '梳理需求', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('模型服务暂时不可用')
  await expect(page.getByLabel('补充信息或修改要求')).toHaveValue('触发失败')
  expect(tasks[0].artifacts).toHaveLength(0)
  expect(tasks[0].messages).toHaveLength(1)
  await expect(page.getByText('本次处理已完成，结果已保存。')).not.toBeVisible()
})

test('访问令牌恢复连接，模型密钥默认隐藏且不进入浏览器存储', async ({ page }) => {
  const { state } = await mockApi(page, { authentication: true, configured: false })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '模型设置', exact: true })).toBeVisible()
  await page.getByLabel('工作台访问令牌', { exact: true }).fill('test-workspace-token')
  await page.getByRole('button', { name: '连接工作台', exact: true }).click()
  await expect(page.getByText('工作台已连接。', { exact: true })).toBeVisible()
  const key = page.getByLabel('API 密钥', { exact: true })
  await expect(key).toHaveAttribute('type', 'password')
  await key.fill('synthetic-key-for-tests-only')
  await page.getByRole('button', { name: '显示API 密钥', exact: true }).click()
  await expect(key).toHaveAttribute('type', 'text')
  await page.getByRole('button', { name: '保存模型设置', exact: true }).click()
  await expect(page.getByText('模型设置已保存，尚未发起模型调用。')).toBeVisible()
  await expect(key).toHaveValue('')
  expect(state.savedKey).toBe('synthetic-key-for-tests-only')
  const storage = await page.evaluate(() => ({ local: JSON.stringify(localStorage), session: JSON.stringify(sessionStorage) }))
  expect(storage.local + storage.session).not.toContain('synthetic-key-for-tests-only')
  expect(storage.session).toContain('test-workspace-token')
})

test('素材上传部分失败可重试，不会重复创建任务', async ({ page }) => {
  const { tasks, state } = await mockApi(page)
  state.rejectNext = true
  await page.goto('/')
  await page.getByLabel('已有素材（可选）', { exact: true }).setInputFiles({ name: '门店资料.txt', mimeType: 'text/plain', buffer: Buffer.from('待核实资料', 'utf8') })
  await page.getByRole('button', { name: '创建任务', exact: true }).click()
  await expect(page.getByText(/这些素材还未上传/)).toBeVisible()
  await page.getByRole('button', { name: '重试上传', exact: true }).click()
  await expect(page.getByText('门店资料.txt', { exact: true })).toBeVisible()
  await expect(page.getByText(/这些素材还未上传/)).not.toBeVisible()
  expect(tasks).toHaveLength(1)
  expect(state.attempts).toBe(2)
})

test('窄屏和减少动态效果保留核心表单与任务操作', async ({ page }) => {
  await mockApi(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await expect(page.getByText('暂无任务', { exact: true })).toBeVisible()
  await page.screenshot({ path: 'design/render-empty-mobile.png', fullPage: true })
  await create(page)
  await expect(page.getByRole('button', { name: '梳理需求', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '导出任务', exact: true })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: 'design/render-task-mobile.png', fullPage: true })
})

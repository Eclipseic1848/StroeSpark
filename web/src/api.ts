import type { Artifact, Provider, ProviderInput, Task, TaskDetail, Material, Health, Action } from './types'

const TOKEN_KEY = 'storespark-access-token'
let accessToken = ''
try { accessToken = sessionStorage.getItem(TOKEN_KEY) ?? '' } catch { /* 浏览器禁止存储时使用内存令牌。 */ }

export function currentToken() { return accessToken }

export function connect(token: string) {
  accessToken = token.trim()
  try {
    if (accessToken) sessionStorage.setItem(TOKEN_KEY, accessToken)
    else sessionStorage.removeItem(TOKEN_KEY)
  } catch { /* 令牌仍可用于当前页面，不依赖持久存储。 */ }
}

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message) }
}

async function request(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers)
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (typeof options.body === 'string') headers.set('Content-Type', 'application/json')
  const timeout = AbortSignal.timeout(180000)
  const signal = options.signal ? AbortSignal.any([options.signal, timeout]) : timeout
  const response = await fetch(path, { ...options, headers, signal })
  if (!response.ok) {
    let message = response.status === 401 ? '访问令牌无效或未填写，请在模型设置中重新连接。' : `请求未完成（${response.status}），请重试。`
    try {
      const payload = await response.json()
      if (typeof payload.detail === 'string' && response.status !== 401) message = payload.detail
      if (response.status === 422) message = '输入内容不符合要求，请检查长度、格式及必填信息。'
    } catch { /* 非 JSON 错误也保留可读的恢复提示。 */ }
    throw new ApiError(message, response.status)
  }
  return response
}

async function json<T>(path: string, options?: RequestInit): Promise<T> {
  return (await request(path, options)).json()
}

export const api = {
  health: (signal?: AbortSignal) => json<Health>('/api/health', { signal }),
  provider: (signal?: AbortSignal) => json<Provider>('/api/v1/provider', { signal }),
  saveProvider: (value: ProviderInput) => json<Provider>('/api/v1/provider', { method: 'PUT', body: JSON.stringify(value) }),
  tasks: (signal?: AbortSignal) => json<Task[]>('/api/v1/tasks', { signal }),
  task: (id: string, signal?: AbortSignal) => json<TaskDetail>(`/api/v1/tasks/${encodeURIComponent(id)}`, { signal }),
  create: (value: Pick<Task, 'title' | 'brief' | 'channel' | 'format'>) => json<Task>('/api/v1/tasks', { method: 'POST', body: JSON.stringify(value) }),
  message: (id: string, content: string, action: Action) => json<TaskDetail>(`/api/v1/tasks/${encodeURIComponent(id)}/messages`, { method: 'POST', body: JSON.stringify({ content, action }) }),
  upload: (id: string, file: File) => {
    const body = new FormData()
    body.append('file', file)
    return json<Material>(`/api/v1/tasks/${encodeURIComponent(id)}/materials`, { method: 'POST', body })
  },
  saveArtifact: (taskId: string, value: Artifact) => json<Artifact>(`/api/v1/tasks/${encodeURIComponent(taskId)}/artifacts/${encodeURIComponent(value.id)}`, { method: 'PATCH', body: JSON.stringify({ title: value.title, content: value.content }) }),
  export: async (id: string) => (await request(`/api/v1/tasks/${encodeURIComponent(id)}/export`)).blob(),
}

export function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error && error.name === 'AbortError') return ''
  if (error instanceof Error && error.name === 'TimeoutError') return '请求已超时，输入仍然保留。请先重新打开任务核对结果，再决定是否重新处理。'
  return '连接未完成，请检查网络与服务是否启动后重试。你的输入仍保留在页面中。'
}

export function fileError(file: File) {
  if (!/\.(txt|md|csv|jpe?g|png|webp)$/i.test(file.name)) return '仅支持 TXT、MD、CSV、JPEG、PNG 和 WebP 文件。'
  if (file.size === 0) return '文件为空，请选择包含内容的文件。'
  if (file.size > 5 * 1024 * 1024) return '单个文件不能超过 5 MB，请缩小文件后重试。'
  return ''
}

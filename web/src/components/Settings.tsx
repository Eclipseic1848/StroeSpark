import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Provider, ProviderInput } from '../types'
import { currentToken } from '../api'
import { Field, Notice, SecretField } from './Shared'

export default function Settings({ provider, busy, onSave, onConnect, onBack, onDirty }: { provider: Provider | null; busy: boolean; onSave: (input: ProviderInput) => Promise<boolean>; onConnect: (token: string) => Promise<void>; onBack: () => void; onDirty: (dirty: boolean) => void }) {
  const [baseUrl, setBaseUrl] = useState(provider?.base_url ?? 'https://api.deepseek.com')
  const [model, setModel] = useState(provider?.model ?? 'deepseek-flash')
  const [key, setKey] = useState('')
  const [token, setToken] = useState(currentToken)
  const [error, setError] = useState('')
  async function save(event: FormEvent) {
    event.preventDefault()
    if (busy) return
    let valid = false
    try { valid = new URL(baseUrl).protocol === 'https:' } catch { valid = false }
    if (!valid || !model.trim()) {
      setError(!valid ? '请填写使用 HTTPS 的模型 API 基础地址。' : '请填写准确的模型 ID。')
      document.getElementById(!valid ? 'base-url' : 'model-id')?.focus()
      return
    }
    setError('')
    if (await onSave({ provider: 'deepseek', base_url: baseUrl.trim(), model: model.trim(), ...(key.trim() ? { api_key: key.trim() } : {}) })) { setKey(''); onDirty(false) }
  }
  return <section className="settings-panel" aria-labelledby="settings-heading"><div className="section-heading"><div><h1 id="settings-heading">模型设置</h1><p className="lead">设置服务端调用的模型。密钥不会保存在浏览器中。</p></div><button className="button button-outline" onClick={onBack}>返回工作台</button></div>
    <form className="settings-form" noValidate onSubmit={save}><h2>DeepSeek 官方接口</h2><Field label="API 基础地址" id="base-url" value={baseUrl} onChange={event => { setBaseUrl(event.target.value); onDirty(true) }} type="url" maxLength={300} disabled={busy} help="通常为 https://api.deepseek.com" error={error && !baseUrl.startsWith('https:') ? error : undefined}/><Field label="模型 ID" id="model-id" value={model} onChange={event => { setModel(event.target.value); onDirty(true) }} maxLength={100} disabled={busy}/><SecretField label="API 密钥" id="provider-key" value={key} onChange={value => { setKey(value); onDirty(true) }} disabled={busy} help={provider?.api_key_set ? '已配置密钥。留空会保留现有密钥；填写新值会替换。' : '填写你在 DeepSeek 官方平台申请的密钥。'}/>{error ? <Notice tone="error">{error}</Notice> : null}<p className="field-help">当前配置来源：{provider?.source === 'environment' ? '服务端环境变量' : provider?.source === 'saved' ? '已保存配置' : '默认配置'}。保存配置不会发起模型调用。</p><button className="button button-primary" disabled={busy} aria-busy={busy}>{busy ? '正在保存…' : '保存模型设置'}</button></form>
    <form className="connection-form" noValidate onSubmit={async event => { event.preventDefault(); if (!busy) await onConnect(token) }}><h2>工作台连接</h2><p>服务器启用了访问令牌时，在这里填写。仅保留到当前浏览器会话结束。</p><SecretField label="工作台访问令牌" id="access-token" value={token} onChange={setToken} disabled={busy} help="本地未启用访问令牌时可以留空；它与模型 API 密钥不同。"/><button className="button button-outline" disabled={busy} aria-busy={busy}>连接工作台</button></form>
  </section>
}

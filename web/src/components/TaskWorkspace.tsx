import { useEffect, useState } from 'react'
import type { Action, Artifact, TaskDetail } from '../types'
import { fileError } from '../api'
import ContentEditor from './ContentEditor'
import { Notice, TextField } from './Shared'

const actions: { value: Action; label: string; help: string }[] = [
  { value: 'clarify', label: '梳理需求', help: '根据现有信息明确任务，补问必要的问题。' },
  { value: 'direction', label: '提出方向', help: '提出宣传重点，说明已有依据和待核实信息。' },
  { value: 'generate', label: '生成文案', help: '按本次任务生成可编辑文案，缺少的真实信息会标出。' },
  { value: 'revise', label: '修改文案', help: '根据你的具体反馈修改已有文案。' },
]

export default function TaskWorkspace({ task, busy, configured, pendingFiles, onClearPending, onAction, onUpload, onSave, onExport, onDirty, onSettings }: {
  task: TaskDetail; busy: boolean; configured: boolean; pendingFiles: File[]; onClearPending: () => void;
  onAction: (content: string, action: Action) => Promise<boolean>; onUpload: (files: File[]) => Promise<void>;
  onSave: (artifact: Artifact) => Promise<Artifact | null>; onExport: () => void; onDirty: (dirty: boolean) => void; onSettings: () => void
}) {
  const [content, setContent] = useState('')
  const [action, setAction] = useState<Action>('clarify')
  const [error, setError] = useState('')
  const [artifactDirty, setArtifactDirty] = useState(false)
  const artifact = task.artifacts.at(-1)
  useEffect(() => { onDirty(!!content.trim() || artifactDirty || pendingFiles.length > 0) }, [content, artifactDirty, pendingFiles.length, onDirty])
  const selected = actions.find(item => item.value === action)!
  return <section className="workspace" aria-labelledby="task-heading"><div className="section-heading"><div><h1 id="task-heading">{task.title}</h1><p className="lead">{[task.channel, task.format].filter(Boolean).join(' · ') || '使用渠道与内容形式待明确'}</p></div><button className="button button-outline" disabled={busy || artifactDirty} onClick={onExport} title={artifactDirty ? '请先保存内容修改，再导出' : undefined}>导出任务</button></div>
    <div className="task-brief"><h2>本次宣传需求</h2><p>{task.brief || '尚未补充，可以从已有素材开始。'}</p></div>
    <div className="workspace-columns"><div className="conversation-column"><section className="materials-section" aria-labelledby="materials-heading"><div className="section-heading"><h2 id="materials-heading">已有素材</h2><label className={`button button-outline file-button ${busy ? 'is-disabled' : ''}`}>上传素材<input aria-label="上传素材" type="file" multiple disabled={busy} accept=".txt,.md,.csv,.jpg,.jpeg,.png,.webp" onChange={event => {
      const files = Array.from(event.target.files ?? [])
      const invalid = files.map(fileError).find(Boolean)
      event.target.value = ''
      if (invalid) { setError(invalid); return }
      setError(''); void onUpload(files)
    }}/></label></div>{task.materials.length ? <ul className="material-list">{task.materials.map(material => <li key={material.id}><span>{material.name}</span><small>{new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 1 }).format(material.size / 1024)} KB</small></li>)}</ul> : <p className="empty-copy">还没有素材。你可以直接描述需求，也可以提交已有资料。</p>}<p className="field-help">TXT、MD、CSV、JPEG、PNG、WebP；单个文件不超过 5 MB。</p>{pendingFiles.length ? <Notice tone="error"><p>这些素材还未上传：{pendingFiles.map(file => file.name).join('、')}</p><div className="inline-actions"><button className="button button-outline" disabled={busy} onClick={() => void onUpload(pendingFiles)}>重试上传</button><button className="button button-ghost" disabled={busy} onClick={onClearPending}>移除待上传文件</button></div></Notice> : null}</section>
    <section className="conversation" aria-labelledby="conversation-heading"><h2 id="conversation-heading">任务沟通</h2>{task.messages.length ? <div className="message-list">{task.messages.map(message => <article key={message.id} className={`message message-${message.role}`}><h3>{message.role === 'user' ? '你的补充' : 'StoreSpark'}</h3><p>{message.content}</p></article>)}</div> : <p className="empty-copy">任务已保存。可以先梳理需求，或在信息足够时直接提出方向。</p>}</section>
    {!configured ? <Notice><p>还未配置模型密钥。任务与素材可以先保存，模型处理需要完成设置。</p><button className="button button-outline" disabled={busy} onClick={onSettings}>配置模型</button></Notice> : null}
    <form className="message-form" noValidate onSubmit={async event => {
      event.preventDefault()
      if (busy || !configured) return
      if (action === 'revise' && !content.trim()) { setError('请说明希望修改的具体内容。'); document.getElementById('task-message')?.focus(); return }
      if (artifactDirty) { setError('请先保存内容修改，再发起新的处理。'); return }
      setError('')
      if (await onAction(content.trim(), action)) setContent('')
    }}><TextField id="task-message" label="补充信息或修改要求" value={content} onChange={event => setContent(event.target.value)} rows={4} disabled={busy} maxLength={16000} placeholder="可以回答前面的问题，或说明希望调整的地方。" error={error}/><fieldset className="action-options" disabled={busy}><legend>这次希望完成什么</legend>{actions.map(item => <label key={item.value}><input type="radio" name="task-action" value={item.value} checked={action === item.value} onChange={() => setAction(item.value)}/><span>{item.label}</span></label>)}</fieldset><p className="field-help action-help">{selected.help}</p><button className="button button-primary" disabled={busy || !configured || artifactDirty} aria-busy={busy}>{busy ? '正在处理，请稍候…' : selected.label}</button><p className="field-help">每次处理会调用已配置的模型；失败时保留输入，不会显示为生成成功。</p></form></div>
    <aside className="content-column" aria-labelledby="content-heading"><h2 id="content-heading">宣传内容</h2>{artifact ? <ContentEditor key={artifact.id} artifact={artifact} busy={busy} onSave={onSave} onDirty={setArtifactDirty}/> : <div className="content-empty"><h3>内容将在这里保留</h3><p>先明确宣传方向，再生成文案。你可以编辑结果、保存修改并导出。</p></div>}<p className="content-boundary">使用前请核实菜品、价格、地址及活动信息。当前交付为文本，不包含海报图片或视频成片。</p></aside></div>
  </section>
}

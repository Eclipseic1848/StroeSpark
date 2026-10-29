import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { Task } from '../types'
import { fileError } from '../api'
import { Field, Notice, TextField } from './Shared'

export default function CreateTask({ busy, onCreate, onDirty }: { busy: boolean; onCreate: (value: Pick<Task, 'title' | 'brief' | 'channel' | 'format'>, files: File[]) => Promise<void>; onDirty: (dirty: boolean) => void }) {
  const [title, setTitle] = useState('')
  const [brief, setBrief] = useState('')
  const [channel, setChannel] = useState('')
  const [format, setFormat] = useState('')
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState('')
  useEffect(() => { onDirty(!!(title || brief || channel || format || files.length)) }, [title, brief, channel, format, files.length, onDirty])
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (busy) return
    if (!brief.trim() && files.length === 0) {
      setError('请写一句宣传需求，或选择一份已有素材。')
      document.getElementById('brief')?.focus()
      return
    }
    setError('')
    await onCreate({ title: title.trim() || brief.trim().slice(0, 30) || '新的宣传任务', brief: brief.trim() || '请结合我提供的素材，帮助我明确本次宣传任务。', channel: channel.trim(), format: format.trim() || '宣传文案' }, files)
  }
  return <div className="creation-layout"><section className="creation-main" aria-labelledby="create-heading"><h1 id="create-heading">从一个宣传想法开始</h1><p className="lead">说说你想宣传什么，也可以先上传已有素材。</p><form noValidate onSubmit={submit} className="create-form">
    <Field id="task-title" label="任务名称" value={title} onChange={event => setTitle(event.target.value)} placeholder="给这次宣传起个名字（可选）" maxLength={100} disabled={busy}/>
    <TextField id="brief" label="宣传需求" value={brief} onChange={event => setBrief(event.target.value)} placeholder="例如：我的店刚开业，想让附近的人愿意来试试，但还不知道该怎么宣传。" maxLength={12000} error={error} rows={6} disabled={busy}/>
    <div className="form-columns"><Field id="channel" label="使用渠道（可选）" value={channel} onChange={event => setChannel(event.target.value)} placeholder="例如：朋友圈、门店、外卖页面" maxLength={100} disabled={busy}/><Field id="format" label="内容形式（可选）" value={format} onChange={event => setFormat(event.target.value)} placeholder="首版支持宣传文案" maxLength={100} disabled={busy}/></div>
    <div className="field"><label htmlFor="initial-materials">已有素材（可选）</label><input id="initial-materials" type="file" multiple accept=".txt,.md,.csv,.jpg,.jpeg,.png,.webp" disabled={busy} onChange={event => {
      const selected = Array.from(event.target.files ?? [])
      const invalid = selected.map(fileError).find(Boolean)
      if (invalid) { setError(invalid); setFiles([]); event.target.value = ''; return }
      setFiles(selected); setError('')
    }} aria-describedby="initial-materials-help"/><span id="initial-materials-help" className="field-help">支持 TXT、MD、CSV、JPEG、PNG、WebP，单个文件不超过 5 MB。素材将随任务保存。</span>{files.length > 0 ? <span className="field-help">已选择 {files.length} 份素材</span> : null}</div>
    <button className="button button-primary button-wide" type="submit" disabled={busy} aria-busy={busy}>{busy ? '正在创建任务…' : '创建任务'}</button>
    <Notice>需求还不清楚也没关系，可以从一句话开始。</Notice>
  </form></section><aside className="delivery-guide"><h2>一次任务的交付</h2><ol><li><strong>宣传方向</strong><p>梳理宣传目标与核心信息，明确想要传达的重点。</p></li><li><strong>对应内容</strong><p>先完成可编辑的宣传文案，再根据真实反馈调整。</p></li><li><strong>使用建议</strong><p>说明如何使用内容，以及怎样收集小范围反馈。</p></li></ol></aside></div>
}

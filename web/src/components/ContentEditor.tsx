import { useEffect, useState } from 'react'
import type { Artifact } from '../types'
import { Field, TextField } from './Shared'

export default function ContentEditor({ artifact, busy, onSave, onDirty }: { artifact: Artifact; busy: boolean; onSave: (artifact: Artifact) => Promise<Artifact | null>; onDirty: (dirty: boolean) => void }) {
  const [title, setTitle] = useState(artifact.title)
  const [content, setContent] = useState(artifact.content)
  const dirty = title !== artifact.title || content !== artifact.content
  useEffect(() => { onDirty(dirty) }, [dirty, onDirty])
  return <form className="artifact-editor" noValidate onSubmit={async event => {
    event.preventDefault()
    if (busy || !title.trim() || !content.trim()) return
    const saved = await onSave({ ...artifact, title: title.trim(), content })
    if (saved) { setTitle(saved.title); setContent(saved.content) }
  }}><div className="section-heading"><h3>内容草稿</h3><span className="field-help">{dirty ? '有未保存的修改' : '已保存'}</span></div><Field id={`artifact-title-${artifact.id}`} label="内容标题" value={title} onChange={event => setTitle(event.target.value)} maxLength={200} disabled={busy}/><TextField id={`artifact-content-${artifact.id}`} label="内容正文" value={content} onChange={event => setContent(event.target.value)} rows={14} maxLength={30000} disabled={busy}/><button className="button button-outline" disabled={busy || !dirty || !title.trim() || !content.trim()} aria-busy={busy}>保存内容修改</button></form>
}

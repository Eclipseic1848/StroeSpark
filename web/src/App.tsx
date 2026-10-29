import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError, connect, errorMessage } from './api'
import type { Action, Artifact, Provider, ProviderInput, Task, TaskDetail } from './types'
import CreateTask from './components/CreateTask'
import Settings from './components/Settings'
import TaskWorkspace from './components/TaskWorkspace'
import { Mark, Notice } from './components/Shared'

const statusNames: Record<Task['status'], string> = { draft: '待梳理', clarifying: '需求梳理', direction: '宣传方向', content: '内容草稿' }

export default function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [provider, setProvider] = useState<Provider | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [detail, setDetail] = useState<TaskDetail | null>(null)
  const [view, setView] = useState<'workspace' | 'settings'>('workspace')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<{ text: string; tone: 'info' | 'success' | 'error' } | null>(null)
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  const [dirty, setDirty] = useState(false)
  const [leave, setLeave] = useState<(() => void) | null>(null)
  const dialog = useRef<HTMLDialogElement>(null)
  const requestSequence = useRef(0)

  const fail = useCallback((error: unknown) => {
    const text = errorMessage(error)
    if (text) setNotice({ text, tone: 'error' })
  }, [])

  const load = useCallback(async (signal?: AbortSignal) => {
    const [items, config] = await Promise.all([api.tasks(signal), api.provider(signal)])
    setTasks(items)
    setProvider(config)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    load(controller.signal).catch(error => { fail(error); if (error instanceof ApiError && error.status === 401) setView('settings') }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [load, fail])

  useEffect(() => {
    if (!selected) { setDetail(null); return }
    const controller = new AbortController()
    const sequence = ++requestSequence.current
    setLoading(true)
    api.task(selected, controller.signal).then(task => { if (sequence === requestSequence.current) setDetail(task) }).catch(fail).finally(() => { if (!controller.signal.aborted && sequence === requestSequence.current) setLoading(false) })
    return () => controller.abort()
  }, [selected, fail])

  useEffect(() => {
    if (!dirty) return
    const guard = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    window.addEventListener('beforeunload', guard)
    return () => window.removeEventListener('beforeunload', guard)
  }, [dirty])

  useEffect(() => {
    if (!leave) return
    const element = dialog.current
    const previous = document.activeElement as HTMLElement | null
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    element?.showModal()
    return () => { element?.close(); document.body.style.overflow = overflow; previous?.focus() }
  }, [leave])

  function navigate(action: () => void) {
    if (busy) return
    if (dirty) setLeave(() => action)
    else action()
  }

  function remember(task: TaskDetail) {
    setDetail(task)
    setTasks(items => [task, ...items.filter(item => item.id !== task.id)])
  }

  async function uploadFiles(id: string, files: File[]) {
    const remaining: File[] = []
    for (const file of files) {
      try { await api.upload(id, file) }
      catch (error) { remaining.push(file); fail(error) }
    }
    setPendingFiles(remaining)
    return remaining.length === 0
  }

  async function createTask(value: Pick<Task, 'title' | 'brief' | 'channel' | 'format'>, files: File[]) {
    setBusy(true); setNotice(null)
    try {
      const task = await api.create(value)
      const uploaded = await uploadFiles(task.id, files)
      setDirty(false); setSelected(task.id); setView('workspace')
      remember(await api.task(task.id))
      if (uploaded) setNotice({ text: '任务已创建，可以继续梳理需求或提出宣传方向。', tone: 'success' })
    } catch (error) { fail(error) }
    finally { setBusy(false) }
  }

  async function runAction(content: string, action: Action) {
    if (!selected || busy) return false
    setBusy(true); setNotice(null)
    try {
      remember(await api.message(selected, content, action))
      setNotice({ text: '本次处理已完成，结果已保存。', tone: 'success' })
      return true
    } catch (error) {
      fail(error)
      try { remember(await api.task(selected)) } catch { /* 保留已有工作区与输入，稍后可以重试。 */ }
      return false
    } finally { setBusy(false) }
  }

  async function upload(files: File[]) {
    if (!selected || busy) return
    setBusy(true); setNotice(null)
    try {
      const uploaded = await uploadFiles(selected, files)
      remember(await api.task(selected))
      if (uploaded) setNotice({ text: '素材已保存，下次处理需求时会结合可读取的内容。', tone: 'success' })
    } catch (error) { fail(error) }
    finally { setBusy(false) }
  }

  async function saveArtifact(artifact: Artifact) {
    if (!selected || busy) return null
    setBusy(true); setNotice(null)
    try {
      const saved = await api.saveArtifact(selected, artifact)
      setDetail(current => current ? { ...current, artifacts: current.artifacts.map(item => item.id === saved.id ? saved : item) } : current)
      setNotice({ text: '内容修改已保存。', tone: 'success' })
      return saved
    } catch (error) { fail(error); return null }
    finally { setBusy(false) }
  }

  async function exportTask() {
    if (!selected || busy) return
    setBusy(true); setNotice(null)
    try {
      const blob = await api.export(selected)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${(detail?.title || '宣传任务').replace(/[<>:"/\\|?*]/g, '-').slice(0, 60)}.md`
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
      setNotice({ text: '已导出保存的任务内容。', tone: 'success' })
    } catch (error) { fail(error) }
    finally { setBusy(false) }
  }

  async function saveProvider(input: ProviderInput) {
    setBusy(true); setNotice(null)
    try { setProvider(await api.saveProvider(input)); setNotice({ text: '模型设置已保存，尚未发起模型调用。', tone: 'success' }); return true }
    catch (error) { fail(error); return false }
    finally { setBusy(false) }
  }

  async function reconnect(token: string) {
    setBusy(true); setNotice(null)
    connect(token)
    try { await load(); setNotice({ text: '工作台已连接。', tone: 'success' }) }
    catch (error) { fail(error) }
    finally { setBusy(false) }
  }

  return <div className="app-shell"><header className="app-header"><button className="brand" onClick={() => navigate(() => { setView('workspace'); setSelected(null) })} disabled={busy} aria-label="StoreSpark 工作台首页"><Mark/><span>StoreSpark</span></button><button className="button button-outline settings-button" disabled={busy || loading} onClick={() => navigate(() => { setView(view === 'settings' ? 'workspace' : 'settings'); setNotice(null) })}>{view === 'settings' ? '返回工作台' : '模型设置'}</button></header>
    <div className="app-body"><aside className="task-rail" aria-label="宣传任务"><h2>宣传任务</h2><button className="button button-primary button-wide" disabled={busy} onClick={() => navigate(() => { setSelected(null); setView('workspace'); setNotice(null); setPendingFiles([]) })}>新建任务</button>{tasks.length ? <ul className="task-list">{tasks.map(task => <li key={task.id}><button className={`task-item ${selected === task.id && view === 'workspace' ? 'is-selected' : ''}`} disabled={busy} aria-current={selected === task.id && view === 'workspace' ? 'page' : undefined} onClick={() => { if (selected !== task.id || view !== 'workspace') navigate(() => { setSelected(task.id); setView('workspace'); setNotice(null); setPendingFiles([]) }) }}><span>{task.title}</span><small>{statusNames[task.status]}</small></button></li>)}</ul> : <p className="rail-empty">{loading ? '正在读取任务…' : '暂无任务'}</p>}</aside>
    <main className="main-content">{notice ? <div className="page-feedback"><Notice tone={notice.tone}>{notice.text}</Notice></div> : null}{view === 'settings' ? <Settings key={provider?.model ?? 'settings'} provider={provider} busy={busy} onSave={saveProvider} onConnect={reconnect} onBack={() => navigate(() => setView('workspace'))} onDirty={setDirty}/> : selected ? loading || !detail || detail.id !== selected ? <div className="loading-state" role="status">正在读取任务…</div> : <TaskWorkspace key={detail.id} task={detail} busy={busy} configured={!!provider?.api_key_set} pendingFiles={pendingFiles} onClearPending={() => setPendingFiles([])} onAction={runAction} onUpload={upload} onSave={saveArtifact} onExport={exportTask} onDirty={setDirty} onSettings={() => navigate(() => setView('settings'))}/> : <CreateTask busy={busy || loading} onCreate={createTask} onDirty={setDirty}/>}</main></div>
    {leave ? <dialog ref={dialog} className="leave-dialog" aria-labelledby="leave-title" aria-describedby="leave-description" onCancel={event => { event.preventDefault(); setLeave(null) }}><h2 id="leave-title">保留当前修改？</h2><p id="leave-description">当前有尚未保存的输入或内容修改。离开会丢失这些修改，已保存的内容不会改变。</p><div className="dialog-actions"><button autoFocus className="button button-primary" onClick={() => setLeave(null)}>继续编辑</button><button className="button button-outline" onClick={() => { const action = leave; setDirty(false); setLeave(null); action() }}>放弃修改并离开</button></div></dialog> : null}
  </div>
}

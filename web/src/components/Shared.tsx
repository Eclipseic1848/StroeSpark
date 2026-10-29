import { useEffect, useRef, useState } from 'react'
import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from 'react'

export function Mark() {
  return <svg viewBox="0 0 28 28" aria-hidden="true"><path d="M14 2c0 7-5 12-12 12 7 0 12 5 12 12 0-7 5-12 12-12-7 0-12-5-12-12Z" fill="none" stroke="currentColor" strokeWidth="2.4"/><path d="M14 2c0 7-5 12-12 12" fill="none" stroke="var(--color-accent)" strokeWidth="2.7"/></svg>
}

export function Notice({ children, tone = 'info' }: { children: ReactNode; tone?: 'info' | 'error' | 'success' }) {
  return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{children}</div>
}

export function Field({ label, id, help, error, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; id: string; help?: string; error?: string }) {
  return <div className="field"><label htmlFor={id}>{label}</label><input id={id} {...props} aria-invalid={!!error} aria-describedby={help || error ? `${id}-help` : undefined}/>{help || error ? <span id={`${id}-help`} className={error ? 'field-error' : 'field-help'}>{error || help}</span> : null}</div>
}

export function TextField({ label, id, help, error, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string; id: string; help?: string; error?: string }) {
  const ref = useRef<HTMLTextAreaElement>(null)
  useEffect(() => {
    const input = ref.current
    if (input) { input.style.height = 'auto'; input.style.height = `${Math.min(640, Math.max(input.scrollHeight, 120))}px` }
  }, [props.value])
  return <div className="field"><label htmlFor={id}>{label}</label><textarea id={id} ref={ref} {...props} className={`resize-none ${props.className ?? ''}`} style={{ ...props.style, resize: 'none' }} aria-invalid={!!error} aria-describedby={help || error ? `${id}-help` : undefined}/>{help || error ? <span id={`${id}-help`} className={error ? 'field-error' : 'field-help'}>{error || help}</span> : null}</div>
}

export function SecretField({ label, id, value, onChange, help, disabled }: { label: string; id: string; value: string; onChange: (value: string) => void; help: string; disabled?: boolean }) {
  const [visible, setVisible] = useState(false)
  return <div className="field"><label htmlFor={id}>{label}</label><div className="secret-input"><input id={id} type={visible ? 'text' : 'password'} autoComplete="off" spellCheck={false} value={value} onChange={event => onChange(event.target.value)} aria-describedby={`${id}-help`} disabled={disabled}/><button type="button" className="button button-ghost" onClick={() => setVisible(current => !current)} aria-pressed={visible} aria-label={`${visible ? '隐藏' : '显示'}${label}`} disabled={disabled}>{visible ? '隐藏' : '显示'}</button></div><span id={`${id}-help`} className="field-help">{help}</span></div>
}

export interface Task {
  id: string
  title: string
  brief: string
  channel: string
  format: string
  status: 'draft' | 'clarifying' | 'direction' | 'content'
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Material {
  id: string
  name: string
  media_type: string
  size: number
  created_at: string
}

export interface Artifact {
  id: string
  kind: 'copy'
  title: string
  content: string
  created_at: string
}

export interface TaskDetail extends Task {
  messages: Message[]
  materials: Material[]
  artifacts: Artifact[]
}

export interface Provider {
  provider: string
  base_url: string
  model: string
  api_key_set: boolean
  source: string
}

export interface ProviderInput {
  provider: string
  base_url: string
  model: string
  api_key?: string
}

export interface Health {
  status: string
  version: string
  provider_configured: boolean
}

export type Action = 'clarify' | 'direction' | 'generate' | 'revise'

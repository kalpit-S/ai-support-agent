export interface Message {
  id: number
  customer_id: number
  direction: 'inbound' | 'outbound'
  channel: 'sms' | 'email' | 'voice'
  content: string
  metadata?: {
    tool_calls?: ToolCall[]
    [key: string]: unknown
  }
  created_at: string
}

export interface ToolCall {
  id: string
  name: string
  args: Record<string, unknown>
  result?: Record<string, unknown>
}

export interface ToolExecution {
  id: string
  name: string
  args: Record<string, unknown>
  result?: Record<string, unknown>
  status: 'pending' | 'success' | 'error'
  startTime: number
  duration?: number
}

export interface Customer {
  id: number
  phone_number: string | null
  email: string | null
  first_name: string | null
  last_name: string | null
  extracted_data: Record<string, unknown> | null
  messages: Message[]
  created_at: string
  updated_at: string
}

export interface WebhookResponse {
  status: string
  message_id: number
  customer_id: number
  batch_id: string
}

export type Channel = 'email' | 'sms' | 'voice'

export type VoiceStatus =
  | 'idle'
  | 'connecting'
  | 'listening'
  | 'processing'
  | 'speaking'
  | 'error'

export interface VoiceMessage {
  type: 'ready' | 'transcript' | 'thinking' | 'tool_call' | 'response' | 'audio_done' | 'error'
  text?: string
  name?: string
  args?: Record<string, unknown>
  result?: Record<string, unknown>
  message?: string
}

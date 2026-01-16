import type { Customer, WebhookResponse } from '@/types'

const DEMO_PHONE = '+15551234567'
const DEMO_EMAIL = 'kal@example.com'

export async function sendSmsMessage(body: string): Promise<WebhookResponse> {
  const response = await fetch('/webhook/sms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_number: DEMO_PHONE,
      body,
    }),
  })

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`)
  }

  return response.json()
}

export async function sendEmailMessage(
  body: string,
  subject = 'Support Request'
): Promise<WebhookResponse> {
  const response = await fetch('/webhook/email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from_email: DEMO_EMAIL,
      body,
      subject,
    }),
  })

  if (!response.ok) {
    throw new Error(`Failed to send email: ${response.statusText}`)
  }

  return response.json()
}

export async function getCustomer(customerId: number): Promise<Customer> {
  const response = await fetch(`/customers/${customerId}`)

  if (!response.ok) {
    throw new Error(`Failed to fetch customer: ${response.statusText}`)
  }

  return response.json()
}

export function createVoiceWebSocket(): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const ws = new WebSocket(`${protocol}//${host}/ws/voice`)
  ws.binaryType = 'arraybuffer'
  return ws
}

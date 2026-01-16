import { useCallback, useRef } from 'react'
import { useAppStore, type Channel } from '@/stores/appStore'
import { useToolStreamStore } from '@/stores/toolStreamStore'
import { sendSmsMessage, sendEmailMessage, getCustomer } from '@/api/client'
import type { Message, ToolCall } from '@/types'

export function useChat() {
  const { setCustomerId, setCustomerData, setMessages, isLoading, setLoading, setError } =
    useAppStore()
  const { addExecution } = useToolStreamStore()

  // Track which tool calls we've already added
  const seenToolCallsRef = useRef<Set<string>>(new Set())

  const sendMessage = useCallback(
    async (text: string, channel: Channel = 'sms') => {
      setLoading(true)
      setError(null)

      try {
        // Send message via specified channel
        const response = channel === 'email'
          ? await sendEmailMessage(text)
          : await sendSmsMessage(text)

        setCustomerId(response.customer_id)

        // Poll for response
        await pollForResponse(response.customer_id)
      } catch (error) {
        console.error('Failed to send message:', error)
        setError(error instanceof Error ? error.message : 'Failed to send message')
      } finally {
        setLoading(false)
      }
    },
    [setCustomerId, setLoading, setError]
  )

  const pollForResponse = async (custId: number) => {
    // Wait for worker to process
    await new Promise((resolve) => setTimeout(resolve, 1000))

    let attempts = 0
    const maxAttempts = 30

    while (attempts < maxAttempts) {
      const customer = await getCustomer(custId)
      setCustomerData(customer)
      setMessages(customer.messages)

      // Extract tool calls from messages
      extractToolCalls(customer.messages)

      // Check if we have an outbound response
      const lastMessage = customer.messages[customer.messages.length - 1]
      if (lastMessage?.direction === 'outbound') {
        return
      }

      await new Promise((resolve) => setTimeout(resolve, 2000))
      attempts++
    }
  }

  const extractToolCalls = (messages: Message[]) => {
    messages.forEach((msg) => {
      if (msg.metadata?.tool_calls) {
        (msg.metadata.tool_calls as ToolCall[]).forEach((tc) => {
          const execId = `${msg.id}-${tc.id}`

          // Only add if we haven't seen it before
          if (!seenToolCallsRef.current.has(execId)) {
            seenToolCallsRef.current.add(execId)
            addExecution({
              id: execId,
              name: tc.name,
              args: tc.args,
              result: tc.result,
              status: 'success',
              startTime: Date.now(),
              duration: 50,
            })
          }
        })
      }
    })
  }

  return {
    sendMessage,
    isLoading,
  }
}

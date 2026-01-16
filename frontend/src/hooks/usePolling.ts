import { useEffect, useRef, useCallback } from 'react'
import { useAppStore } from '@/stores/appStore'
import { getCustomer } from '@/api/client'

const POLL_INTERVAL = 2000

export function usePolling() {
  const { customerId, setCustomerData, setMessages } = useAppStore()
  const intervalRef = useRef<number | null>(null)

  const poll = useCallback(async () => {
    if (!customerId) return

    try {
      const customer = await getCustomer(customerId)
      setCustomerData(customer)
      setMessages(customer.messages)
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, [customerId, setCustomerData, setMessages])

  useEffect(() => {
    if (customerId) {
      poll() // Initial fetch
      intervalRef.current = window.setInterval(poll, POLL_INTERVAL)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [customerId, poll])

  return { refetch: poll }
}

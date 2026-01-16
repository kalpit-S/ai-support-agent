import { create } from 'zustand'
import type { Customer, Message } from '@/types'

export type Channel = 'email' | 'sms' | 'voice'

interface AppState {
  channel: Channel
  customerId: number | null
  customerData: Customer | null
  messages: Message[]
  isLoading: boolean
  error: string | null

  setChannel: (channel: Channel) => void
  setCustomerId: (id: number | null) => void
  setCustomerData: (data: Customer | null) => void
  addMessage: (msg: Message) => void
  setMessages: (msgs: Message[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
}

export const useAppStore = create<AppState>((set) => ({
  channel: 'email',
  customerId: null,
  customerData: null,
  messages: [],
  isLoading: false,
  error: null,

  setChannel: (channel) => set({ channel }),
  setCustomerId: (customerId) => set({ customerId }),
  setCustomerData: (customerData) => set({ customerData }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (messages) => set({ messages }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () =>
    set({
      customerId: null,
      customerData: null,
      messages: [],
      isLoading: false,
      error: null,
    }),
}))

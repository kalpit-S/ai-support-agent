import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useAppStore } from '@/stores/appStore'
import { useChat } from '@/hooks/useChat'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function SmsView() {
  const messages = useAppStore((state) => state.messages)
  const isLoading = useAppStore((state) => state.isLoading)
  const { sendMessage } = useChat()

  const [text, setText] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  // Filter to only SMS messages
  const smsMessages = messages.filter((m) => m.channel === 'sms')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [smsMessages, isLoading])

  const handleSend = async () => {
    if (!text.trim()) return
    await sendMessage(text, 'sms')
    setText('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-black">
      {/* iMessage-style header */}
      <div className="flex items-center justify-center px-4 py-3 border-b bg-zinc-100/80 dark:bg-zinc-900/80 backdrop-blur">
        <div className="text-center">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-semibold mx-auto mb-1">
            S
          </div>
          <p className="text-sm font-medium">Macrocenter Support</p>
          <p className="text-xs text-muted-foreground">+1 (555) 867-5309</p>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4">
        {smsMessages.length === 0 && !isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <p className="text-sm">No messages yet</p>
              <p className="text-xs mt-1">Send a message to start the conversation</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2 max-w-lg mx-auto">
            {smsMessages.map((msg, idx) => {
              const isUser = msg.direction === 'inbound'
              const showTimestamp =
                idx === 0 ||
                new Date(msg.created_at).getTime() -
                  new Date(smsMessages[idx - 1].created_at).getTime() >
                  300000 // 5 min gap

              return (
                <div key={msg.id}>
                  {showTimestamp && (
                    <div className="text-center text-xs text-muted-foreground py-2">
                      {new Date(msg.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  )}
                  <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
                    <div
                      className={cn(
                        'max-w-[75%] px-4 py-2 rounded-2xl text-sm',
                        isUser
                          ? 'bg-blue-500 text-white rounded-br-md'
                          : 'bg-zinc-200 dark:bg-zinc-800 text-foreground rounded-bl-md'
                      )}
                    >
                      {isUser ? (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}

            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-zinc-200 dark:bg-zinc-800 px-4 py-3 rounded-2xl rounded-bl-md">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* iMessage-style input */}
      <div className="p-3 border-t bg-zinc-100/80 dark:bg-zinc-900/80 backdrop-blur">
        <div className="flex items-end gap-2 max-w-lg mx-auto">
          <div className="flex-1 bg-white dark:bg-zinc-800 rounded-full border px-4 py-2">
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="iMessage"
              className="w-full bg-transparent text-sm focus:outline-none"
            />
          </div>
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!text.trim() || isLoading}
            className="rounded-full h-9 w-9 bg-blue-500 hover:bg-blue-600"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { Send, Inbox, RefreshCw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useAppStore } from '@/stores/appStore'
import { useChat } from '@/hooks/useChat'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'

export function EmailView() {
  const messages = useAppStore((state) => state.messages)
  const isLoading = useAppStore((state) => state.isLoading)
  const { sendMessage } = useChat()

  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [selectedEmail, setSelectedEmail] = useState<number | null>(null)

  // Filter to only email messages
  const emailMessages = messages.filter((m) => m.channel === 'email')

  const handleSend = async () => {
    if (!body.trim()) return
    const fullMessage = subject ? `Subject: ${subject}\n\n${body}` : body
    await sendMessage(fullMessage, 'email')
    setSubject('')
    setBody('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.metaKey) {
      handleSend()
    }
  }

  // Group messages into threads - each inbound email paired with following outbound responses
  const threads: Array<{ inbound: typeof emailMessages[0]; outbound?: typeof emailMessages[0] }> = []

  for (let i = 0; i < emailMessages.length; i++) {
    const msg = emailMessages[i]
    if (msg.direction === 'inbound') {
      // Find the next outbound email after this inbound
      const outbound = emailMessages.slice(i + 1).find(m => m.direction === 'outbound')
      threads.push({ inbound: msg, outbound })
    }
  }

  // Auto-select the latest thread when a new response arrives
  useEffect(() => {
    if (threads.length > 0 && selectedEmail === null) {
      setSelectedEmail(0)
    }
  }, [threads.length])

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-950">
      {/* Gmail-style header */}
      <div className="flex items-center gap-2 px-4 py-2 border-b bg-zinc-50 dark:bg-zinc-900">
        <Inbox className="h-5 w-5 text-red-500" />
        <span className="font-medium">Inbox</span>
        <span className="text-sm text-muted-foreground">
          {threads.length > 0 && `(${threads.length})`}
        </span>
        <div className="flex-1" />
        <Button variant="ghost" size="icon" className="h-8 w-8">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Email list */}
        <div className="w-80 border-r flex flex-col min-h-0">
          <ScrollArea className="flex-1">
            {threads.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <Inbox className="h-12 w-12 mx-auto mb-3 opacity-20" />
                <p className="text-sm">No emails yet</p>
                <p className="text-xs mt-1">Compose an email to get started</p>
              </div>
            ) : (
              <div className="divide-y">
                {threads.map((thread, idx) => (
                  <button
                    key={thread.inbound.id}
                    onClick={() => setSelectedEmail(idx)}
                    className={cn(
                      'w-full text-left p-3 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors',
                      selectedEmail === idx && 'bg-blue-50 dark:bg-blue-950/30',
                      !thread.outbound && 'opacity-60' // Dim if no response yet
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium",
                        thread.outbound ? "bg-blue-500" : "bg-zinc-400"
                      )}>
                        {thread.outbound ? 'S' : '...'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm truncate">
                            {thread.outbound ? 'Macrocenter Support' : 'Awaiting reply...'}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(thread.outbound?.created_at || thread.inbound.created_at).toLocaleTimeString([], {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">
                          {thread.outbound?.content.slice(0, 50) || thread.inbound.content.slice(0, 50)}...
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Email view / Compose */}
        <div className="flex-1 flex flex-col min-h-0">
          {selectedEmail !== null && threads[selectedEmail] ? (
            // View selected email thread
            <ScrollArea className="flex-1">
              <div className="p-6 space-y-6">
                {/* User's email */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white font-medium">
                      Y
                    </div>
                    <div>
                      <p className="font-medium">You</p>
                      <p className="text-xs text-muted-foreground">
                        to support@macrocenter.com
                      </p>
                    </div>
                    <div className="flex-1" />
                    <span className="text-xs text-muted-foreground">
                      {new Date(threads[selectedEmail].inbound.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="pl-13 text-sm whitespace-pre-wrap">
                    {threads[selectedEmail].inbound.content}
                  </div>
                </div>

                {/* Agent's reply */}
                {threads[selectedEmail].outbound && (
                  <div className="space-y-3 border-t pt-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium">
                        S
                      </div>
                      <div>
                        <p className="font-medium">Macrocenter Support</p>
                        <p className="text-xs text-muted-foreground">to you</p>
                      </div>
                      <div className="flex-1" />
                      <span className="text-xs text-muted-foreground">
                        {new Date(threads[selectedEmail].outbound.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="pl-13 text-sm prose prose-sm dark:prose-invert max-w-none">
                      <ReactMarkdown>{threads[selectedEmail].outbound.content}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          ) : (
            // Compose new email
            <div className="flex-1 flex flex-col p-4">
              <div className="text-sm font-medium mb-4 text-muted-foreground">New Message</div>

              <div className="space-y-3 flex-1 flex flex-col">
                <div className="flex items-center gap-2 pb-2 border-b">
                  <span className="text-sm text-muted-foreground w-16">To:</span>
                  <span className="text-sm">support@macrocenter.com</span>
                </div>

                <div className="flex items-center gap-2 pb-2 border-b">
                  <span className="text-sm text-muted-foreground w-16">Subject:</span>
                  <Input
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    placeholder="Enter subject..."
                    className="border-0 shadow-none focus-visible:ring-0 p-0 h-auto"
                  />
                </div>

                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Write your message here..."
                  className="flex-1 resize-none bg-transparent text-sm focus:outline-none"
                />

                <div className="flex items-center gap-2 pt-2">
                  <Button
                    onClick={handleSend}
                    disabled={!body.trim() || isLoading}
                    className="gap-2"
                  >
                    <Send className="h-4 w-4" />
                    {isLoading ? 'Sending...' : 'Send'}
                  </Button>
                  <span className="text-xs text-muted-foreground">Cmd+Enter to send</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

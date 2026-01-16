import { Mail, MessageSquare, Phone, User, Wrench, ChevronDown, ChevronRight, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { useAppStore } from '@/stores/appStore'
import { useToolStreamStore } from '@/stores/toolStreamStore'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Message, ToolExecution } from '@/types'

export function UnifiedContext() {
  const customerData = useAppStore((state) => state.customerData)
  const messages = useAppStore((state) => state.messages)
  const executions = useToolStreamStore((state) => state.executions)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold">Unified Context</h2>
        <p className="text-xs text-muted-foreground">Cross-channel conversation history</p>
      </div>

      {/* Customer Info */}
      <CustomerCard customer={customerData} />

      {/* Conversation Timeline */}
      <div className="flex-1 min-h-0">
        <ScrollArea className="h-full">
          <div className="p-4">
            {messages.length === 0 && executions.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <p className="text-sm">No activity yet</p>
                <p className="text-xs mt-1">
                  Send a message via Email, SMS, or Voice to see the unified timeline
                </p>
              </div>
            ) : (
              <ConversationTimeline messages={messages} executions={executions} />
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  )
}

function CustomerCard({ customer }: { customer: import('@/types').Customer | null }) {
  if (!customer) {
    return (
      <div className="p-4 border-b bg-muted/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
            <User className="h-5 w-5 text-muted-foreground" />
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">No customer yet</p>
            <p className="text-xs text-muted-foreground">Start a conversation to identify</p>
          </div>
        </div>
      </div>
    )
  }

  const name = [customer.first_name, customer.last_name].filter(Boolean).join(' ') || 'Unknown'
  const extractedData = customer.extracted_data as Record<string, unknown> | null

  return (
    <div className="p-4 border-b bg-muted/30">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
          {name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{name}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {customer.email && <span>{customer.email}</span>}
            {customer.phone_number && <span>{customer.phone_number}</span>}
          </div>
        </div>
      </div>

      {/* Extracted data */}
      {extractedData && Object.keys(extractedData).length > 0 && (
        <div className="space-y-1">
          {Object.entries(extractedData).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground capitalize">{key.replace(/_/g, ' ')}:</span>
              <span className="font-medium">{String(value)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ConversationTimeline({
  messages,
  executions,
}: {
  messages: Message[]
  executions: ToolExecution[]
}) {
  // Combine messages and tool executions into a unified timeline
  type TimelineItem =
    | { type: 'message'; data: Message; time: number }
    | { type: 'tool'; data: ToolExecution; time: number }

  const timeline: TimelineItem[] = [
    ...messages.map((m) => ({
      type: 'message' as const,
      data: m,
      time: new Date(m.created_at).getTime(),
    })),
    ...executions.map((e) => ({
      type: 'tool' as const,
      data: e,
      time: e.startTime,
    })),
  ].sort((a, b) => a.time - b.time)

  return (
    <div className="space-y-3">
      {timeline.map((item) => {
        if (item.type === 'message') {
          return <MessageEntry key={`msg-${item.data.id}`} message={item.data} />
        } else {
          return <ToolEntry key={`tool-${item.data.id}`} execution={item.data} />
        }
      })}
    </div>
  )
}

function MessageEntry({ message }: { message: Message }) {
  const isUser = message.direction === 'inbound'
  const ChannelIcon = {
    email: Mail,
    sms: MessageSquare,
    voice: Phone,
  }[message.channel]

  const channelColor = {
    email: 'text-red-500',
    sms: 'text-green-500',
    voice: 'text-purple-500',
  }[message.channel]

  return (
    <div className="flex gap-2">
      <div className={cn('mt-1', channelColor)}>
        <ChannelIcon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium">{isUser ? 'Customer' : 'Agent'}</span>
          <Badge variant="outline" className="text-[10px] px-1 py-0">
            {message.channel}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-2">{message.content}</p>
      </div>
    </div>
  )
}

function ToolEntry({ execution }: { execution: ToolExecution }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="flex gap-2">
      <div className="mt-1 text-amber-500">
        <Wrench className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 mb-1 w-full text-left"
        >
          {expanded ? (
            <ChevronDown className="h-3 w-3 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
          )}
          <span className="text-xs font-mono font-medium">{execution.name}</span>
          {execution.status === 'success' && (
            <CheckCircle className="h-3 w-3 text-green-500" />
          )}
          {execution.duration && (
            <span className="text-xs text-muted-foreground">{execution.duration}ms</span>
          )}
        </button>

        {expanded && (
          <div className="text-xs bg-muted/50 rounded p-2 space-y-2">
            <div>
              <p className="text-muted-foreground mb-1">Args:</p>
              <pre className="text-xs overflow-auto">{JSON.stringify(execution.args, null, 2)}</pre>
            </div>
            {execution.result && (
              <div>
                <p className="text-muted-foreground mb-1">Result:</p>
                <pre className="text-xs overflow-auto max-h-24">
                  {JSON.stringify(execution.result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

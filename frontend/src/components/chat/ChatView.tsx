import { AlertCircle, X } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { Button } from '@/components/ui/button'

export function ChatView() {
  const error = useAppStore((state) => state.error)
  const setError = useAppStore((state) => state.setError)

  return (
    <div className="flex flex-col h-full">
      {/* Error Banner */}
      {error && (
        <div className="bg-destructive/10 border-b border-destructive/20 px-4 py-2 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <span className="text-sm text-destructive flex-1">{error}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => setError(null)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-auto">
        <MessageList />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4">
        <ChatInput />
      </div>
    </div>
  )
}

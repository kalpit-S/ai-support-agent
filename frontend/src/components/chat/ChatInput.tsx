import { useState, type FormEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useChat } from '@/hooks/useChat'

export function ChatInput() {
  const [text, setText] = useState('')
  const { sendMessage, isLoading } = useChat()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!text.trim() || isLoading) return

    const message = text.trim()
    setText('')
    await sendMessage(message)
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={isLoading ? 'Waiting for response...' : 'Type your message...'}
        disabled={isLoading}
        className="flex-1"
      />
      <Button type="submit" disabled={!text.trim() || isLoading} size="icon">
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  )
}

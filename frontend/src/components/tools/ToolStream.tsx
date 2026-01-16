import { Trash2 } from 'lucide-react'
import { useToolStreamStore } from '@/stores/toolStreamStore'
import { ToolCard } from './ToolCard'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'

export function ToolStream() {
  const { executions, clearExecutions } = useToolStreamStore()

  if (executions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <p className="text-sm text-muted-foreground text-center">
          Tool executions will appear here as the agent processes requests.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {executions.map((exec) => (
            <ToolCard key={exec.id} execution={exec} />
          ))}
        </div>
      </ScrollArea>

      <div className="p-3 border-t border-border">
        <Button
          variant="ghost"
          size="sm"
          className="w-full gap-2"
          onClick={clearExecutions}
        >
          <Trash2 className="h-4 w-4" />
          Clear
        </Button>
      </div>
    </div>
  )
}

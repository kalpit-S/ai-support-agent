import { useState } from 'react'
import { ChevronDown, ChevronRight, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { ToolExecution } from '@/types'

interface ToolCardProps {
  execution: ToolExecution
}

export function ToolCard({ execution }: ToolCardProps) {
  const [expanded, setExpanded] = useState(false)

  const StatusIcon = {
    pending: Loader2,
    success: CheckCircle,
    error: XCircle,
  }[execution.status]

  const statusColor = {
    pending: 'text-yellow-500',
    success: 'text-green-500',
    error: 'text-red-500',
  }[execution.status]

  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full text-left"
      >
        <CardContent className="p-3">
          <div className="flex items-center gap-2">
            <StatusIcon
              className={cn(
                'h-4 w-4 flex-shrink-0',
                statusColor,
                execution.status === 'pending' && 'animate-spin'
              )}
            />
            <span className="font-mono text-sm font-medium flex-1 truncate">
              {execution.name}
            </span>
            {execution.duration && (
              <Badge variant="secondary" className="text-xs">
                {execution.duration}ms
              </Badge>
            )}
            {expanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </CardContent>
      </button>

      {expanded && (
        <div className="border-t border-border bg-muted/50 p-3 space-y-2">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Arguments</p>
            <pre className="text-xs bg-background p-2 rounded overflow-auto max-h-32">
              {JSON.stringify(execution.args, null, 2)}
            </pre>
          </div>
          {execution.result && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Result</p>
              <pre className="text-xs bg-background p-2 rounded overflow-auto max-h-32">
                {JSON.stringify(execution.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

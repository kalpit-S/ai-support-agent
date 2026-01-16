import { Badge } from '@/components/ui/badge'
import type { VoiceStatus as VoiceStatusType } from '@/types'

interface VoiceStatusProps {
  status: VoiceStatusType
  error?: string | null
}

const statusLabels: Record<VoiceStatusType, string> = {
  idle: 'Ready',
  connecting: 'Connecting...',
  listening: 'Listening',
  processing: 'Processing',
  speaking: 'Speaking',
  error: 'Error',
}

const statusVariants: Record<VoiceStatusType, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  idle: 'secondary',
  connecting: 'warning',
  listening: 'success',
  processing: 'warning',
  speaking: 'success',
  error: 'destructive',
}

export function VoiceStatus({ status, error }: VoiceStatusProps) {
  return (
    <div className="text-center">
      <Badge variant={statusVariants[status]}>
        {statusLabels[status]}
      </Badge>
      {error && (
        <p className="text-sm text-destructive mt-2">{error}</p>
      )}
    </div>
  )
}

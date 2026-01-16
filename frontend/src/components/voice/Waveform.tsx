import { cn } from '@/lib/utils'

interface WaveformProps {
  isActive: boolean
}

export function Waveform({ isActive }: WaveformProps) {
  return (
    <div className="flex items-center justify-center gap-1 h-24">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'w-2 bg-primary rounded-full transition-all duration-200',
            isActive
              ? 'animate-pulse'
              : 'h-8'
          )}
          style={{
            height: isActive ? `${Math.random() * 60 + 20}px` : '32px',
            animationDelay: `${i * 100}ms`,
          }}
        />
      ))}
    </div>
  )
}

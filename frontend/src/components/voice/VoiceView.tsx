import { useState, useEffect } from 'react'
import { Phone, PhoneOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useVoice } from '@/hooks/useVoice'
import { Waveform } from './Waveform'
import { cn } from '@/lib/utils'

export function VoiceView() {
  const { status, transcript, startSession, endSession, error } = useVoice()
  const isActive = status !== 'idle' && status !== 'error'
  const isConnecting = status === 'connecting'

  const statusText = {
    idle: 'Ready to call',
    connecting: 'Connecting...',
    listening: 'Listening',
    processing: 'Processing...',
    speaking: 'Agent speaking',
    error: error || 'Connection error',
  }[status]

  const statusColor = {
    idle: 'text-muted-foreground',
    connecting: 'text-yellow-500',
    listening: 'text-green-500',
    processing: 'text-blue-500',
    speaking: 'text-purple-500',
    error: 'text-red-500',
  }[status]

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-zinc-900 to-black">
      {/* Phone call UI */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        {/* Avatar */}
        <div className="relative mb-6">
          <div
            className={cn(
              'w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center',
              isActive && 'ring-4 ring-green-500/50 animate-pulse'
            )}
          >
            <span className="text-4xl font-bold text-white">S</span>
          </div>
          {isActive && (
            <div className="absolute -bottom-1 -right-1 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <Phone className="w-4 h-4 text-white" />
            </div>
          )}
        </div>

        {/* Name and number */}
        <h2 className="text-2xl font-semibold text-white mb-1">Macrocenter Support</h2>
        <p className="text-zinc-400 mb-4">+1 (555) 867-5309</p>

        {/* Status */}
        <p className={cn('text-sm font-medium mb-8', statusColor)}>{statusText}</p>

        {/* Waveform */}
        {isActive && (
          <div className="mb-8 w-full max-w-xs">
            <Waveform isActive={status === 'listening' || status === 'speaking'} />
          </div>
        )}

        {/* Live transcript */}
        {transcript && isActive && (
          <div className="max-w-md text-center mb-8 bg-white/10 rounded-lg px-6 py-4 backdrop-blur">
            <p className="text-xs text-zinc-400 uppercase tracking-wide mb-2">You said</p>
            <p className="text-white text-lg">&ldquo;{transcript}&rdquo;</p>
          </div>
        )}

        {/* Call timer (when active) */}
        {isActive && !isConnecting && <CallTimer />}
      </div>

      {/* Call controls */}
      <div className="p-8 flex justify-center">
        {isActive ? (
          <Button
            size="lg"
            variant="destructive"
            onClick={endSession}
            className="rounded-full h-16 w-16"
          >
            <PhoneOff className="h-6 w-6" />
          </Button>
        ) : (
          <Button
            size="lg"
            onClick={startSession}
            className="rounded-full h-16 w-16 bg-green-500 hover:bg-green-600"
          >
            <Phone className="h-6 w-6" />
          </Button>
        )}
      </div>

      {/* Instructions */}
      {!isActive && (
        <p className="text-center text-zinc-500 text-sm pb-8">
          Press the call button to start a voice conversation
        </p>
      )}
    </div>
  )
}

function CallTimer() {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds((s) => s + 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60

  return (
    <p className="text-zinc-400 font-mono text-lg">
      {mins.toString().padStart(2, '0')}:{secs.toString().padStart(2, '0')}
    </p>
  )
}

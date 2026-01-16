import { useState, useRef, useCallback } from 'react'
import { useToolStreamStore } from '@/stores/toolStreamStore'
import { createVoiceWebSocket } from '@/api/client'
import type { VoiceStatus, VoiceMessage } from '@/types'

export function useVoice() {
  const [status, setStatus] = useState<VoiceStatus>('idle')
  const [transcript, setTranscript] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)

  const { addExecution, updateExecution } = useToolStreamStore()

  const startSession = useCallback(async () => {
    try {
      setStatus('connecting')
      setError(null)
      setTranscript('')

      // Create WebSocket
      const ws = createVoiceWebSocket()
      wsRef.current = ws

      ws.onopen = () => {
        console.log('Voice WebSocket connected')
      }

      ws.onmessage = async (event) => {
        if (typeof event.data === 'string') {
          const msg: VoiceMessage = JSON.parse(event.data)
          handleVoiceMessage(msg)
        } else {
          // Binary TTS audio
          await playAudio(event.data as ArrayBuffer | Blob)
        }
      }

      ws.onerror = () => {
        setError('WebSocket connection error')
        setStatus('error')
      }

      ws.onclose = () => {
        setStatus('idle')
        stopRecording()
        // Clear any buffered audio on disconnect
        audioBufferRef.current = []
        isPlayingRef.current = false
      }

      // Start microphone
      await startRecording(ws)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start voice session')
      setStatus('error')
    }
  }, [])

  const handleVoiceMessage = (msg: VoiceMessage) => {
    switch (msg.type) {
      case 'ready':
        setStatus('listening')
        break
      case 'transcript':
        setTranscript(msg.text || '')
        break
      case 'thinking':
        setStatus('processing')
        break
      case 'tool_call':
        if (msg.name) {
          const execId = `voice-${Date.now()}-${msg.name}`
          addExecution({
            id: execId,
            name: msg.name,
            args: msg.args || {},
            status: 'pending',
            startTime: Date.now(),
          })
          // Store execId for later update
          setTimeout(() => {
            updateExecution(execId, {
              status: 'success',
              result: msg.result,
              duration: 50,
            })
          }, 100)
        }
        break
      case 'response':
        setStatus('speaking')
        break
      case 'audio_done':
        // Flush any remaining audio in the buffer and return to listening.
        // If we don't have buffered audio (or playback failed), still reset state.
        if (audioBufferRef.current.length === 0 && !isPlayingRef.current) {
          setStatus('listening')
        } else {
          flushAudioBuffer()
        }
        break
      case 'error':
        setError(msg.message || 'Unknown error')
        setStatus('error')
        break
    }
  }

  const startRecording = async (ws: WebSocket) => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })
    mediaStreamRef.current = stream

    const audioContext = new AudioContext({ sampleRate: 16000 })
    audioContextRef.current = audioContext

    const source = audioContext.createMediaStreamSource(stream)
    const processor = audioContext.createScriptProcessor(4096, 1, 1)
    processorRef.current = processor

    processor.onaudioprocess = (e) => {
      if (ws.readyState === WebSocket.OPEN) {
        const float32Data = e.inputBuffer.getChannelData(0)
        const int16Data = new Int16Array(float32Data.length)
        for (let i = 0; i < float32Data.length; i++) {
          int16Data[i] = Math.max(-32768, Math.min(32767, float32Data[i] * 32768))
        }
        ws.send(int16Data.buffer)
      }
    }

    source.connect(processor)
    // ScriptProcessorNode must be connected to an output to run, but we don't want sidetone.
    const silentGain = audioContext.createGain()
    silentGain.gain.value = 0
    processor.connect(silentGain)
    silentGain.connect(audioContext.destination)
  }

  const stopRecording = () => {
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
      audioContextRef.current = null
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }
  }

  // Audio buffer for accumulating chunks
  const audioBufferRef = useRef<Int16Array[]>([])
  const isPlayingRef = useRef(false)

  const playAudio = async (data: ArrayBuffer | Blob) => {
    try {
      if (data instanceof Blob) {
        await playAudio(await data.arrayBuffer())
        return
      }

      // Skip empty chunks
      if (data.byteLength === 0) {
        return
      }

      const int16Array = new Int16Array(data)
      if (int16Array.length === 0) {
        return
      }

      // Accumulate audio chunks
      audioBufferRef.current.push(int16Array)

      // Play accumulated audio if we have enough (at least 4800 samples = 200ms at 24kHz)
      const totalSamples = audioBufferRef.current.reduce((sum, arr) => sum + arr.length, 0)
      if (totalSamples >= 4800 && !isPlayingRef.current) {
        await flushAudioBuffer()
      }
    } catch (err) {
      console.error('Failed to queue audio:', err)
    }
  }

  const flushAudioBuffer = async () => {
    if (audioBufferRef.current.length === 0 || isPlayingRef.current) {
      return
    }

    isPlayingRef.current = true

    try {
      // Combine all chunks
      const totalLength = audioBufferRef.current.reduce((sum, arr) => sum + arr.length, 0)
      if (totalLength === 0) {
        isPlayingRef.current = false
        return
      }

      const combined = new Int16Array(totalLength)
      let offset = 0
      for (const chunk of audioBufferRef.current) {
        combined.set(chunk, offset)
        offset += chunk.length
      }
      audioBufferRef.current = []

      // Convert to float32
      const float32Array = new Float32Array(combined.length)
      for (let i = 0; i < combined.length; i++) {
        float32Array[i] = combined[i] / 32768
      }

      // Play
      const audioContext = new AudioContext({ sampleRate: 24000 })
      const audioBuffer = audioContext.createBuffer(1, float32Array.length, 24000)
      audioBuffer.copyToChannel(float32Array, 0)

      const source = audioContext.createBufferSource()
      source.buffer = audioBuffer
      source.connect(audioContext.destination)
      source.start()

      source.onended = () => {
        audioContext.close()
        isPlayingRef.current = false
        // Check if more audio accumulated while playing
        if (audioBufferRef.current.length > 0) {
          flushAudioBuffer()
        } else {
          setStatus('listening')
        }
      }
    } catch (err) {
      console.error('Failed to play audio:', err)
      isPlayingRef.current = false
    }
  }

  const endSession = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    stopRecording()
    // Clear audio buffer
    audioBufferRef.current = []
    isPlayingRef.current = false
    setStatus('idle')
    setTranscript('')
  }, [])

  return {
    status,
    transcript,
    error,
    startSession,
    endSession,
  }
}

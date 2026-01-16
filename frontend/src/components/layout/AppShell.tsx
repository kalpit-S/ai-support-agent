import { Mail, MessageSquare, Phone, RotateCcw } from 'lucide-react'
import { useAppStore, type Channel } from '@/stores/appStore'
import { useToolStreamStore } from '@/stores/toolStreamStore'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { EmailView } from '@/components/channels/EmailView'
import { SmsView } from '@/components/channels/SmsView'
import { VoiceView } from '@/components/voice/VoiceView'
import { UnifiedContext } from '@/components/context/UnifiedContext'

export function AppShell() {
  const { channel, setChannel, reset } = useAppStore()
  const { clearExecutions } = useToolStreamStore()

  const handleReset = () => {
    reset()
    clearExecutions()
  }

  return (
    <div className="h-screen flex bg-background">
      {/* Left Panel - Channel Views */}
      <main className="flex-1 flex flex-col min-w-0 border-r border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card">
          <div>
            <h1 className="text-lg font-semibold">Macrocenter Support</h1>
            <p className="text-xs text-muted-foreground">Multi-channel AI Agent Demo</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReset}
            className="gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </Button>
        </div>

        {/* Channel Tabs */}
        <Tabs
          value={channel}
          onValueChange={(v) => setChannel(v as Channel)}
          className="flex-1 flex flex-col min-h-0"
        >
          <div className="px-4 py-2 border-b border-border bg-muted/30">
            <TabsList className="w-full max-w-md">
              <TabsTrigger value="email" className="flex-1 gap-2">
                <Mail className="h-4 w-4" />
                Email
              </TabsTrigger>
              <TabsTrigger value="sms" className="flex-1 gap-2">
                <MessageSquare className="h-4 w-4" />
                SMS
              </TabsTrigger>
              <TabsTrigger value="voice" className="flex-1 gap-2">
                <Phone className="h-4 w-4" />
                Voice
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="email" className="flex-1 m-0 min-h-0">
            <EmailView />
          </TabsContent>
          <TabsContent value="sms" className="flex-1 m-0 min-h-0">
            <SmsView />
          </TabsContent>
          <TabsContent value="voice" className="flex-1 m-0 min-h-0">
            <VoiceView />
          </TabsContent>
        </Tabs>
      </main>

      {/* Right Panel - Unified Context */}
      <aside className="w-96 flex flex-col bg-card">
        <UnifiedContext />
      </aside>
    </div>
  )
}

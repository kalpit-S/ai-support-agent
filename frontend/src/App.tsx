import { AppShell } from '@/components/layout/AppShell'
import { usePolling } from '@/hooks/usePolling'

function App() {
  // Enable polling for customer data
  usePolling()

  return <AppShell />
}

export default App

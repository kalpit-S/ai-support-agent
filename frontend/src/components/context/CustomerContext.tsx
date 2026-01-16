import { useAppStore } from '@/stores/appStore'
import { Card, CardContent } from '@/components/ui/card'

export function CustomerContext() {
  const customerData = useAppStore((state) => state.customerData)

  if (!customerData?.extracted_data) {
    return (
      <div className="text-sm text-muted-foreground">
        Customer context will appear here as the conversation progresses.
      </div>
    )
  }

  const data = customerData.extracted_data as Record<string, string>

  return (
    <Card>
      <CardContent className="p-3 space-y-2">
        <h3 className="text-xs font-semibold uppercase text-muted-foreground">
          Extracted Data
        </h3>
        <div className="space-y-1">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="text-sm">
              <span className="text-muted-foreground capitalize">
                {key.replace(/_/g, ' ')}:
              </span>{' '}
              <span className="font-medium">{String(value)}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

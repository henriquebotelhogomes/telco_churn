import { Badge } from '@/components/ui/badge'
import { NIVEL_BADGE_CLASS } from '@/lib/format'

export function RiskBadge({ nivel }: { nivel: string }) {
  return (
    <Badge variant="outline" className={NIVEL_BADGE_CLASS[nivel] ?? ''}>
      {nivel}
    </Badge>
  )
}

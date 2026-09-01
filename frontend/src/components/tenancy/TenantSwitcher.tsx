import { useState, useEffect } from 'react'
import { Building2, Check, ChevronDown, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api, getTenantId, setTenantId } from '@/api/client'
import type { TenantItem } from '@/types'

export function TenantSwitcher() {
  const [tenants, setTenants] = useState<TenantItem[]>([])
  const [activeTenant, setActiveTenant] = useState<string>(getTenantId())
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    const fetchTenants = async () => {
      try {
        const res = await api.listTenants()
        setTenants(res.tenants || [])
      } catch (err) {
        console.error('Erro ao carregar tenants:', err)
      }
    }
    fetchTenants()
  }, [])

  const handleSelect = (tenantId: string) => {
    setTenantId(tenantId)
    setActiveTenant(tenantId)
    setIsOpen(false)
    // Recarrega os dados com o novo contexto de tenant
    window.location.reload()
  }

  const current = tenants.find((t) => t.tenant_id === activeTenant) || {
    tenant_id: activeTenant,
    name: activeTenant === 'tenant-default' ? 'RetainIQ Global' : activeTenant,
    plan: 'ENTERPRISE',
  }

  return (
    <div className="relative inline-block text-left">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="h-8 gap-2 border-border bg-card/80 hover:bg-muted/60 text-xs font-medium"
      >
        <Building2 className="h-3.5 w-3.5 text-indigo-500" />
        <span className="font-semibold text-foreground truncate max-w-[130px] sm:max-w-[180px]">
          {current.name}
        </span>
        <Badge
          variant="outline"
          className="hidden sm:inline-flex text-[9px] bg-emerald-500/10 text-emerald-600 border-emerald-500/30 gap-0.5 px-1 py-0 font-mono"
        >
          <ShieldCheck className="h-2.5 w-2.5" /> RLS
        </Badge>
        <ChevronDown className="h-3 w-3 text-muted-foreground opacity-60" />
      </Button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-64 rounded-lg border border-border bg-popover p-1.5 shadow-lg z-50 text-xs">
          <div className="px-2 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border/60 mb-1 flex justify-between items-center">
            <span>Operadora Ativa (Tenant)</span>
            <span className="text-[10px] lowercase text-emerald-600 font-mono">rls-isolado</span>
          </div>

          <div className="space-y-0.5">
            {tenants.map((t) => (
              <button
                key={t.tenant_id}
                onClick={() => handleSelect(t.tenant_id)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md flex items-center justify-between transition-colors ${
                  t.tenant_id === activeTenant
                    ? 'bg-indigo-500/15 text-indigo-600 font-semibold'
                    : 'hover:bg-muted/50 text-foreground'
                }`}
              >
                <div>
                  <div className="font-medium text-xs">{t.name}</div>
                  <div className="text-[10px] text-muted-foreground font-mono">{t.tenant_id}</div>
                </div>
                {t.tenant_id === activeTenant && (
                  <Check className="h-3.5 w-3.5 text-indigo-600" />
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

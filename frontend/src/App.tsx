import { HashRouter, NavLink, Route, Routes } from 'react-router-dom'
import { Activity, LayoutDashboard, ShieldCheck, Users } from 'lucide-react'

import { CustomersPage } from '@/pages/CustomersPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { MlopsPage } from '@/pages/MlopsPage'
import { TenantSwitcher } from '@/components/tenancy/TenantSwitcher'

const NAV = [
  { para: '/', rotulo: 'Dashboard Executivo', icone: LayoutDashboard, fim: true },
  { para: '/customers', rotulo: 'Risk Queue', icone: Users, fim: false },
  { para: '/mlops', rotulo: 'MLOps Health', icone: Activity, fim: false },
]

export default function App() {
  return (
    <HashRouter>
      <div className="flex min-h-svh">
        <aside className="hidden w-64 shrink-0 border-r bg-muted/30 md:block">
          <div className="flex h-14 items-center gap-2 border-b px-4">
            <ShieldCheck className="text-primary" aria-hidden />
            <span className="font-semibold">RetainIQ Cockpit</span>
          </div>
          <nav className="space-y-1 p-3" aria-label="Navegação principal">
            {NAV.map(({ para, rotulo, icone: Icone, fim }) => (
              <NavLink
                key={para}
                to={para}
                end={fim}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  }`
                }
              >
                <Icone size={16} aria-hidden /> {rotulo}
              </NavLink>
            ))}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex h-14 items-center justify-between border-b px-4 md:px-6">
            <h1 className="text-sm font-medium text-muted-foreground">
              Inteligência de Retenção · Multi-Tenant (B2B SaaS)
            </h1>
            <div className="flex items-center gap-3">
              <TenantSwitcher />
              <span className="text-xs text-muted-foreground font-mono hidden sm:inline">/api/v1</span>
            </div>
          </header>
          <main className="flex-1 p-4 md:p-6">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/customers" element={<CustomersPage />} />
              <Route path="/mlops" element={<MlopsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </HashRouter>
  )
}

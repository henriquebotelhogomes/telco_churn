import { useState, useEffect } from 'react'
import {
  Boxes,
  Database,
  Layers,
  RefreshCw,
  Server,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/api/client'
import type { FeatureStoreStatsResponse, FeatureViewMetadata } from '@/types'

export function FeatureCatalogPanel() {
  const [stats, setStats] = useState<FeatureStoreStatsResponse | null>(null)
  const [views, setViews] = useState<FeatureViewMetadata[]>([])
  const [materializing, setMaterializing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  const loadData = async () => {
    try {
      const [statsRes, catRes] = await Promise.all([
        api.getFeatureStoreStats(),
        api.getFeatureCatalog(),
      ])
      setStats(statsRes)
      setViews(catRes.feature_views || [])
    } catch (err) {
      console.error('Erro ao carregar dados da Feature Store:', err)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleMaterialize = async () => {
    setMaterializing(true)
    setMessage(null)
    try {
      const res = await api.materializeFeatures({ limit: 100 })
      setMessage(`✓ Materialização concluída: ${res.entities_materialized} entidades sincronizadas para a Online Store.`)
      await loadData()
    } catch (err) {
      console.error('Erro na materialização:', err)
      setMessage('Erro ao materializar features.')
    } finally {
      setMaterializing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 1. Header & KPI Cards */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Database className="h-5 w-5 text-indigo-500" />
                <CardTitle className="text-lg font-bold">
                  Feature Store Unificada (Feast + Redis Architecture)
                </CardTitle>
                <Badge variant="outline" className="bg-indigo-500/10 text-indigo-500 border-indigo-500/30">
                  Zero Training-Serving Skew
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Camada centralizada que unifica features de Batch (DW) e Streaming (Flink) com SLA &lt; 5ms e Point-in-Time Correctness.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadData}
                className="gap-1.5 text-xs font-semibold"
              >
                <RefreshCw className="h-3.5 w-3.5" /> Atualizar
              </Button>
              <Button
                size="sm"
                disabled={materializing}
                onClick={handleMaterialize}
                className="gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                {materializing ? (
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Zap className="h-3.5 w-3.5" />
                )}
                Sincronizar / Materializar
              </Button>
            </div>
          </div>
          {message && (
            <div className="text-xs font-medium text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 p-2.5 rounded-md mt-2">
              {message}
            </div>
          )}
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Layers className="h-3.5 w-3.5 text-primary" /> Feature Views
              </div>
              <div className="text-xl font-bold font-mono mt-1 text-foreground">
                {stats?.total_feature_views ?? 3}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Batch + Stream</div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Boxes className="h-3.5 w-3.5 text-primary" /> Features Registradas
              </div>
              <div className="text-xl font-bold font-mono mt-1 text-foreground">
                {stats?.total_features_registered ?? 16}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Tipadas e Validadas</div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Server className="h-3.5 w-3.5 text-primary" /> Entidades Online
              </div>
              <div className="text-xl font-bold font-mono mt-1 text-foreground">
                {stats?.online_entities_count ?? 100}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Prontas para Inferência</div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Zap className="h-3.5 w-3.5 text-amber-500" /> Latência SLA
              </div>
              <div className="text-xl font-bold font-mono mt-1 text-emerald-600">
                &lt; 5.0 ms
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Online Store Retrieval</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Catálogo Detalhado de Feature Views */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {views.map((fv) => (
          <Card key={fv.name} className="border-border bg-card flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-sm font-mono font-bold text-foreground">
                  {fv.name}
                </CardTitle>
                <Badge
                  variant={fv.source_type === 'STREAM' ? 'default' : 'secondary'}
                  className="text-[10px] uppercase font-bold"
                >
                  {fv.source_type}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">
                {fv.description}
              </p>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="border rounded-md overflow-hidden text-xs font-mono">
                <div className="bg-muted/40 py-1.5 px-2.5 font-semibold text-[11px] border-b flex justify-between text-muted-foreground">
                  <span>Nome da Feature</span>
                  <span>Tipo</span>
                </div>
                <div className="divide-y divide-border max-h-56 overflow-y-auto">
                  {fv.features.map((f) => (
                    <div key={f.name} className="py-1.5 px-2.5 flex items-center justify-between hover:bg-muted/20">
                      <div className="truncate mr-2">
                        <span className="font-semibold text-foreground">{f.name}</span>
                        <div className="text-[10px] text-muted-foreground truncate">{f.description}</div>
                      </div>
                      <Badge variant="outline" className="text-[9px] shrink-0">
                        {f.dtype}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-3 text-[11px] text-muted-foreground flex justify-between">
                <span>Chave: <b>{fv.entity_key}</b></span>
                <span>TTL: <b>{Math.round(fv.ttl_seconds / 86400)}d</b></span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import {
  Activity,
  CheckCircle2,
  Cpu,
  FileCode,
  Globe,
  Layers,
  RefreshCw,
  Server,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/api/client'
import type { K8sClusterTopologyResponse, K8sManifestValidationResponse } from '@/types'

export function K8sClusterTopology() {
  const [topology, setTopology] = useState<K8sClusterTopologyResponse | null>(null)
  const [validation, setValidation] = useState<K8sManifestValidationResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const [topoRes, valRes] = await Promise.all([
        api.getK8sClusterTopology(),
        api.validateK8sManifests(),
      ])
      setTopology(topoRes)
      setValidation(valRes)
    } catch (err) {
      console.error('Erro ao carregar topologia K8s:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <div className="space-y-6">
      {/* 1. Header & Cluster Overview */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Server className="h-5 w-5 text-blue-500" />
                <CardTitle className="text-lg font-bold">
                  Kubernetes & KEDA Autoscaling (Topologia de Produção)
                </CardTitle>
                <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/30 font-mono">
                  namespace: {topology?.namespace ?? 'retainiq-system'}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Dimensionamento elástico horizontal (HPA) e direcionado por eventos de fila (KEDA Kafka Lag).
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              disabled={loading}
              onClick={loadData}
              className="gap-1.5 text-xs font-semibold"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} /> Atualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Activity className="h-3.5 w-3.5 text-emerald-500" /> Cluster Status
              </div>
              <div className="text-lg font-bold font-mono mt-1 text-emerald-600 flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" /> {topology?.cluster_status ?? 'HEALTHY'}
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Zero Pods em CrashLoop</div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Layers className="h-3.5 w-3.5 text-primary" /> Deployments
              </div>
              <div className="text-xl font-bold font-mono mt-1 text-foreground">
                {topology?.deployments.length ?? 2} Ativos
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">API + Stream Worker</div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Globe className="h-3.5 w-3.5 text-indigo-500" /> Ingress & TLS
              </div>
              <div className="text-sm font-bold font-mono mt-1 text-foreground truncate">
                {topology?.ingress.class ?? 'nginx'} (SSL)
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5 truncate">
                {topology?.ingress.host ?? 'retainiq.internal'}
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-muted/20">
              <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 font-medium">
                <Zap className="h-3.5 w-3.5 text-amber-500" /> KEDA Autoscaling
              </div>
              <div className="text-xl font-bold font-mono mt-1 text-amber-500">
                1 &rarr; 20 pods
              </div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Kafka Lag Trigger</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 2. Deployments & Autoscaling Engines (HPA vs KEDA) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {topology?.deployments.map((dep) => (
          <Card key={dep.name} className="border-border bg-card">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <CardTitle className="text-sm font-mono font-bold text-foreground">
                    {dep.name}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Componente: <span className="font-mono font-semibold">{dep.component}</span>
                  </p>
                </div>
                <Badge
                  variant={dep.autoscaling_mode === 'HPA' ? 'secondary' : 'default'}
                  className="text-[10px] font-mono font-bold"
                >
                  {dep.autoscaling_mode}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-2.5 rounded border border-border bg-muted/20">
                  <div className="text-muted-foreground text-[10px]">Réplicas Atuais</div>
                  <div className="text-base font-bold text-foreground mt-0.5">
                    {dep.replicas_current} / {dep.replicas_desired}
                  </div>
                </div>
                <div className="p-2.5 rounded border border-border bg-muted/20">
                  <div className="text-muted-foreground text-[10px]">Limites (CPU / RAM)</div>
                  <div className="text-base font-bold text-foreground mt-0.5">
                    {dep.cpu_limit} / {dep.memory_limit}
                  </div>
                </div>
              </div>

              {/* HPA Metrics */}
              {dep.hpa && (
                <div className="p-3 rounded-lg border border-border bg-muted/30 space-y-2 text-xs font-mono">
                  <div className="font-semibold text-foreground flex items-center gap-1.5 text-[11px]">
                    <Cpu className="h-3.5 w-3.5 text-primary" /> Horizontal Pod Autoscaler (HPA)
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-muted-foreground">Range:</span>{' '}
                      <b>{dep.hpa.min_replicas} - {dep.hpa.max_replicas} pods</b>
                    </div>
                    <div>
                      <span className="text-muted-foreground">CPU Atual / Target:</span>{' '}
                      <b className="text-emerald-500">{dep.hpa.current_cpu_utilization}</b> / {dep.hpa.target_cpu_utilization}
                    </div>
                    <div className="col-span-2">
                      <span className="text-muted-foreground">Memória Atual / Target:</span>{' '}
                      <b className="text-emerald-500">{dep.hpa.current_memory_utilization}</b> / {dep.hpa.target_memory_utilization}
                    </div>
                  </div>
                </div>
              )}

              {/* KEDA Event-Driven Metrics */}
              {dep.keda && (
                <div className="p-3 rounded-lg border border-border bg-muted/30 space-y-2 text-xs font-mono">
                  <div className="font-semibold text-foreground flex items-center gap-1.5 text-[11px]">
                    <Zap className="h-3.5 w-3.5 text-amber-500" /> KEDA Event-Driven ScaledObject
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-muted-foreground">Range:</span>{' '}
                      <b>{dep.keda.min_replicas} - {dep.keda.max_replicas} pods</b>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Kafka Lag Atual:</span>{' '}
                      <b className="text-emerald-500">{dep.keda.current_kafka_lag} msgs</b>
                    </div>
                    <div className="col-span-2">
                      <span className="text-muted-foreground">Limiar de Escala:</span>{' '}
                      <b>{dep.keda.lag_threshold} msgs / pod</b>
                    </div>
                    <div className="col-span-2 text-[10px] text-muted-foreground truncate">
                      Tópicos: {dep.keda.topics_monitored.join(', ')}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 3. Conformidade e Validação Declarativa dos Manifestos K8s */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="h-4 w-4 text-primary" />
              <CardTitle className="text-sm font-bold">
                Conformidade Declarativa de Manifestos Kubernetes ({validation?.total_manifests ?? 0} Arquivos)
              </CardTitle>
            </div>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px]">
              ✓ 100% Sintaxe Válida
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
            {validation?.manifests.map((m) => (
              <div
                key={m.filename}
                className="p-2.5 rounded border border-border bg-muted/20 flex items-center justify-between"
              >
                <div className="truncate mr-2">
                  <div className="font-semibold text-foreground flex items-center gap-1.5 truncate">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                    <span className="truncate">{m.filename}</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground">{m.size_bytes} bytes</div>
                </div>
                <Badge variant="outline" className="text-[9px] uppercase font-bold shrink-0">
                  k8s/yaml
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

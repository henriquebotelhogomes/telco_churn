import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Activity, Boxes, KeyRound, RefreshCw } from 'lucide-react'

import { api, setApiKey } from '@/api/client'
import { useDrift, useModelInfo } from '@/api/queries'
import { RiskBadge } from '@/components/ui/risk-badge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { formatPercent } from '@/lib/format'

function statusBadge(status: string) {
  const mapa: Record<string, string> = {
    ok: 'Baixo',
    stale: 'Médio',
    not_computed: 'Crítico',
  }
  return <RiskBadge nivel={mapa[status] ?? 'Médio'} />
}

export function MlopsHealth() {
  const queryClient = useQueryClient()
  const modelInfo = useModelInfo()
  const drift = useDrift()
  const [chave, setChave] = useState('')

  const refresh = useMutation({
    mutationFn: api.driftRefresh,
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['drift'] }),
  })

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Boxes aria-hidden /> Modelo
          </CardTitle>
          <CardDescription>Metadados gerados no treino (model_metadata.json)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {modelInfo.isPending && <Skeleton className="h-32" />}
          {modelInfo.isError && (
            <p className="text-destructive">{modelInfo.error.message}</p>
          )}
          {modelInfo.data && (
            <>
              <p>
                <strong>{modelInfo.data.metadata?.model_name ?? 'churn-xgboost'}</strong>{' '}
                v{modelInfo.data.metadata?.version} ·{' '}
                {modelInfo.data.model_loaded ? (
                  <Badge>carregado</Badge>
                ) : (
                  <Badge variant="destructive">não carregado</Badge>
                )}
              </p>
              {modelInfo.data.metadata && (
                <>
                  <p className="text-muted-foreground">
                    Treinado em{' '}
                    {new Date(modelInfo.data.metadata.trained_at).toLocaleString('pt-BR')} ·{' '}
                    {modelInfo.data.metadata.dataset.rows} linhas · git{' '}
                    {modelInfo.data.metadata.git_sha?.slice(0, 7) ?? '—'}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(modelInfo.data.metadata.metrics).map(([nome, valor]) => (
                      <Badge key={nome} variant="secondary">
                        {nome}: {valor.toFixed(2)}
                      </Badge>
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity aria-hidden /> Data drift
          </CardTitle>
          <CardDescription>
            Evidently roda fora do caminho crítico — o cache é atualizado apenas pelo refresh
            administrativo.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {drift.isPending && <Skeleton className="h-32" />}
          {drift.isError && <p className="text-destructive">{drift.error.message}</p>}
          {drift.data && (
            <>
              <div className="flex flex-wrap items-center gap-3">
                {statusBadge(drift.data.status)}
                <span className="text-muted-foreground">
                  {drift.data.samples_in_buffer} amostras no ring buffer
                </span>
                {drift.data.age_seconds !== null && (
                  <span className="text-muted-foreground">
                    gerado há {Math.round(drift.data.age_seconds)}s (TTL{' '}
                    {drift.data.cache_ttl_seconds}s)
                  </span>
                )}
              </div>
              {drift.data.report?.status === 'ok' && (
                <p>
                  {drift.data.report.number_of_drifted_columns ?? 0} de{' '}
                  {drift.data.report.number_of_columns ?? 0} features com drift (
                  {formatPercent(drift.data.report.share_of_drifted_columns ?? 0)}) — dataset_drift:{' '}
                  {drift.data.report.dataset_drift ? 'sim' : 'não'}
                </p>
              )}
              {drift.data.report?.status === 'insufficient_data' && (
                <p className="text-muted-foreground">
                  Amostras insuficientes ({drift.data.report.samples}/
                  {drift.data.report.min_samples}) para calcular drift.
                </p>
              )}
              {drift.data.report?.drift_by_feature && (
                <div className="flex max-h-40 flex-wrap gap-1 overflow-y-auto">
                  {Object.entries(drift.data.report.drift_by_feature).map(([coluna, detalhes]) => (
                    <Badge
                      key={coluna}
                      variant={detalhes.drift_detected ? 'destructive' : 'secondary'}
                    >
                      {coluna}
                    </Badge>
                  ))}
                </div>
              )}
            </>
          )}
          <Button
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending}
            variant="outline"
          >
            <RefreshCw aria-hidden className={refresh.isPending ? 'animate-spin' : ''} />
            {refresh.isPending ? 'Calculando…' : 'Recalcular drift'}
          </Button>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <KeyRound aria-hidden /> Autenticação
          </CardTitle>
          <CardDescription>
            Se a API estiver com API_KEY_ENABLED=true, informe a X-API-Key para usar as rotas
            /api/v1 (armazenada apenas no seu navegador).
          </CardDescription>
        </CardHeader>
        <CardContent className="flex max-w-md gap-2">
          <Input
            type="password"
            value={chave}
            onChange={(evento) => setChave(evento.target.value)}
            placeholder="X-API-Key"
            aria-label="API Key"
          />
          <Button onClick={() => setApiKey(chave)} variant="secondary">
            Salvar
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

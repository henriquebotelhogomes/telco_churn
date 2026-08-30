import type { ReactNode } from 'react'
import { AlertTriangle, Database, Loader2, Upload } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAnalysis, type AnalysisResult } from '@/api/queries'
import { Skeleton } from '@/components/ui/skeleton'

interface AnalysisGateProps {
  children: (resultado: AnalysisResult) => ReactNode
}

/** Estados idle/loading/erro da análise em lote; renderiza children com o resultado. */
export function AnalysisGate({ children }: AnalysisGateProps) {
  const { resultado, carregando, erro, isIdle, analisarBundled, analisarUpload } = useAnalysis()

  if (isIdle) {
    return (
      <Card className="mx-auto mt-10 max-w-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database aria-hidden /> Análise de base de clientes
          </CardTitle>
          <CardDescription>
            O MVP é stateless: os KPIs vêm de uma única predição em lote. Envie um CSV EN-US ou
            analise a base Telco de exemplo.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button onClick={analisarBundled}>
            <Database aria-hidden /> Analisar base Telco (7.043 clientes)
          </Button>
          <input
            id="upload-csv"
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            onChange={(evento) => {
              const arquivo = evento.target.files?.[0]
              if (arquivo) analisarUpload(arquivo)
              evento.target.value = ''
            }}
          />
          <Button
            variant="outline"
            onClick={() => document.getElementById('upload-csv')?.click()}
          >
            <Upload aria-hidden /> Enviar CSV
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (carregando) {
    return (
      <div className="space-y-4" role="status" aria-label="Analisando lote">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="animate-spin" aria-hidden /> Rodando predição em lote…
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-72 rounded-xl" />
      </div>
    )
  }

  if (erro || !resultado) {
    return (
      <Card className="mx-auto mt-10 max-w-xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle aria-hidden /> Falha na análise
          </CardTitle>
          <CardDescription>{erro?.message ?? 'Erro inesperado.'}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={analisarBundled}>
            Tentar novamente
          </Button>
        </CardContent>
      </Card>
    )
  }

  return <>{children(resultado)}</>
}

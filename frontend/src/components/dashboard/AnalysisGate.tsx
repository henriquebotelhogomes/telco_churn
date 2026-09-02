import { useState, type ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Database, Loader2, Sparkles, Upload, Zap } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAnalysis, type AnalysisResult } from '@/api/queries'
import { api } from '@/api/client'
import { Skeleton } from '@/components/ui/skeleton'

interface AnalysisGateProps {
  children: (resultado: AnalysisResult) => ReactNode
}

/** Estados idle/loading/erro da análise em lote; renderiza children com o resultado. */
export function AnalysisGate({ children }: AnalysisGateProps) {
  const { resultado, carregando, erro, isIdle, analisarBundled, analisarUpload, carregarDatasetTexto } = useAnalysis()
  const [synthesizing, setSynthesizing] = useState(false)
  const [showSynthModal, setShowSynthModal] = useState(false)
  const [sampleSize, setSampleSize] = useState(7043)
  const [chaosRatio, setChaosRatio] = useState(0.12)
  const [synthFeedback, setSynthFeedback] = useState<string | null>(null)

  const handleSynthesize = async () => {
    try {
      setSynthesizing(true)
      setSynthFeedback(null)
      const res = await api.synthesizeEnterpriseDataset({
        num_samples: sampleSize,
        chaos_ratio: chaosRatio,
        save_as_default: true,
      })
      setSynthFeedback(`Base Telco 360 gerada: ${res.total_records} clientes com ${res.total_columns} colunas de telemetria!`)
      setShowSynthModal(false)
      if (res.csv_content) {
        carregarDatasetTexto(`telco_enterprise_${res.total_records}_clientes.csv`, res.csv_content)
      } else {
        analisarBundled()
      }
    } catch (err) {
      console.error(err)
      setSynthFeedback('Erro ao gerar base sintética.')
    } finally {
      setSynthesizing(false)
    }
  }

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

  return (
    <div className="space-y-4">
      {synthFeedback && (
        <div className="flex items-center gap-2 text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 p-2.5 rounded-lg border border-emerald-500/30">
          <CheckCircle2 size={14} />
          <span>{synthFeedback}</span>
        </div>
      )}

      {/* Modal de Customização de Geração de Base Sintética */}
      {showSynthModal && (
        <div className="p-4 rounded-xl border border-primary/30 bg-primary/5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <Sparkles size={16} className="text-primary" />
              Sintetizador de Dados Telco 360 Enterprise (LGPD Compliant)
            </h3>
            <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={() => setShowSynthModal(false)}>
              ✕
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Gere uma nova base sintética com 40 atributos de telemetria de rede FTTH/5G (latência, perda de pacotes, quedas), sentimento de CRM WhatsApp, notas de NPS e faturamento BRL.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Tamanho da Base:</label>
              <select
                value={sampleSize}
                onChange={(e) => setSampleSize(Number(e.target.value))}
                className="w-full h-8 px-2 rounded border bg-background text-xs"
              >
                <option value={5000}>5.000 clientes (Rápido)</option>
                <option value={7043}>7.043 clientes (Padrão Telco)</option>
                <option value={15000}>15.000 clientes (Carga Média)</option>
                <option value={25000}>25.000 clientes (Escala Enterprise)</option>
              </select>
            </div>
            <div>
              <label className="font-semibold block mb-1">Nível de Instabilidade / Caos:</label>
              <select
                value={chaosRatio}
                onChange={(e) => setChaosRatio(Number(e.target.value))}
                className="w-full h-8 px-2 rounded border bg-background text-xs"
              >
                <option value={0.05}>Baixo (5% instabilidade)</option>
                <option value={0.12}>Moderado / Realista (12% instabilidade)</option>
                <option value={0.25}>Alto / Crise Regional (25% instabilidade)</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t">
            <Button size="sm" variant="outline" onClick={() => setShowSynthModal(false)}>
              Cancelar
            </Button>
            <Button size="sm" disabled={synthesizing} onClick={handleSynthesize} className="gap-1.5 font-semibold">
              {synthesizing ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
              {synthesizing ? 'Sintetizando Base…' : 'Gerar e Carregar Agora'}
            </Button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-muted/40 px-4 py-2 text-xs">
        <div className="flex items-center gap-2">
          <Database size={14} className="text-primary" />
          <span>
            Base em análise: <strong>{resultado.fonte}</strong> ({resultado.linhas.length} clientes)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs gap-1 border-primary/40 text-primary hover:bg-primary/10 font-semibold"
            onClick={() => setShowSynthModal(!showSynthModal)}
          >
            <Sparkles size={12} /> ⚡ Sintetizar Base Telco 360
          </Button>
          <input
            id="upload-csv-gate"
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
            size="sm"
            variant="ghost"
            className="h-7 text-xs gap-1"
            onClick={() => document.getElementById('upload-csv-gate')?.click()}
          >
            <Upload size={12} /> Enviar outro CSV
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="h-7 text-xs gap-1"
            onClick={analisarBundled}
          >
            <Database size={12} /> Recarregar Base Telco
          </Button>
        </div>
      </div>
      {children(resultado)}
    </div>
  )
}


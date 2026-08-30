import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Bot,
  PhoneCall,
  MessageSquare,
  Mail,
  Copy,
  Check,
  Sparkles,
  Zap,
  RefreshCw,
} from 'lucide-react'

import { api } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { GenerateCopilotScriptResponse, PrevisaoChurnResponse } from '@/types'

interface CopilotRetentionAssistantProps {
  customerId: string
  cliente: Record<string, string>
  previsao?: PrevisaoChurnResponse
  playbookSugerido?: string
  economiaEsperada?: number
  onAplicarPlaybook?: () => void
}

export function CopilotRetentionAssistant({
  customerId,
  cliente,
  previsao,
  playbookSugerido,
  economiaEsperada = 120.0,
}: CopilotRetentionAssistantProps) {
  const [canal, setCanal] = useState<'call_center' | 'whatsapp' | 'email'>('call_center')
  const [tom, setTom] = useState<'empatico' | 'direto' | 'consultivo'>('empatico')
  const [copiado, setCopiado] = useState(false)
  const [scriptData, setScriptData] = useState<GenerateCopilotScriptResponse | null>(null)

  const playbookFinal =
    playbookSugerido || previsao?.acao_recomendada?.playbook || 'FIDELIZACAO_CONTRATO_ANUAL'
  const reducaoRisco = previsao?.acao_recomendada?.reducao_estimada_risco || 0.2

  const generateMutation = useMutation({
    mutationFn: (vars: {
      canal: 'call_center' | 'whatsapp' | 'email'
      tom: 'empatico' | 'direto' | 'consultivo'
    }) =>
      api.generateCopilotScript({
        customer_id: customerId,
        canal: vars.canal,
        tom: vars.tom,
        cliente,
        fatores_shap: previsao?.top_fatores_risco?.map((f) => ({
          fator: f.fator,
          impacto: f.impacto,
          shap_value: f.shap_value,
          direcao: f.direcao,
        })),
        playbook: playbookFinal,
        reducao_estimada_risco: reducaoRisco,
        economia_esperada: economiaEsperada,
      }),
    onSuccess: (data) => {
      setScriptData(data)
    },
  })

  // Gera automaticamente no primeiro carregamento do cliente
  useEffect(() => {
    generateMutation.mutate({ canal, tom })
  }, [customerId, canal, tom])

  const handleCopy = () => {
    if (!scriptData) return
    navigator.clipboard.writeText(scriptData.mensagem_completa)
    setCopiado(true)
    setTimeout(() => setCopiado(false), 3000)
  }

  return (
    <Card className="border-primary/30 bg-primary/5">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              <Bot className="text-primary" size={20} />
              Copilot AI de Retenção & Negociação
            </CardTitle>
            <CardDescription className="text-xs">
              Roteiro de atendimento e proposta personalizada baseada nos drivers de risco SHAP.
            </CardDescription>
          </div>
          {scriptData && (
            <Badge variant="outline" className="text-xs font-mono gap-1.5">
              {scriptData.provider_used.includes('gemini') ? (
                <>
                  <Sparkles size={12} className="text-amber-500" />
                  Gemini AI ({scriptData.latency_ms}ms)
                </>
              ) : (
                <>
                  <Zap size={12} className="text-primary" />
                  Rules Engine ({scriptData.latency_ms}ms)
                </>
              )}
            </Badge>
          )}
        </div>

        {/* Seletores de Canal e Tom */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          {/* Canais */}
          <div className="flex items-center gap-1.5 rounded-lg border bg-background p-1 text-xs">
            <button
              type="button"
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-colors ${
                canal === 'call_center'
                  ? 'bg-primary text-primary-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setCanal('call_center')}
            >
              <PhoneCall size={13} />
              Call Center
            </button>
            <button
              type="button"
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-colors ${
                canal === 'whatsapp'
                  ? 'bg-primary text-primary-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setCanal('whatsapp')}
            >
              <MessageSquare size={13} />
              WhatsApp
            </button>
            <button
              type="button"
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-colors ${
                canal === 'email'
                  ? 'bg-primary text-primary-foreground font-medium'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setCanal('email')}
            >
              <Mail size={13} />
              E-mail
            </button>
          </div>

          {/* Tons */}
          <div className="flex items-center gap-1 text-xs">
            <span className="text-muted-foreground text-xs">Tom:</span>
            {(['empatico', 'direto', 'consultivo'] as const).map((t) => (
              <Button
                key={t}
                size="sm"
                variant={tom === t ? 'secondary' : 'ghost'}
                className="h-7 px-2 text-xs capitalize"
                onClick={() => setTom(t)}
              >
                {t}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 text-xs">
        {generateMutation.isPending ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground gap-2">
            <RefreshCw size={16} className="animate-spin text-primary" />
            <span>Gerando roteiro de negociação personalizado com IA…</span>
          </div>
        ) : scriptData ? (
          <>
            {/* Visualização de Roteiro de Call Center estruturado */}
            {canal === 'call_center' && scriptData.roteiro_etapas ? (
              <div className="space-y-2.5">
                <div className="rounded-lg border bg-background p-3 space-y-1.5">
                  <div className="font-semibold text-primary flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/10 text-[10px]">
                      1
                    </span>
                    Abertura & Vínculo
                  </div>
                  <p className="text-muted-foreground text-xs leading-relaxed">
                    {scriptData.roteiro_etapas.etapa_1_abertura}
                  </p>
                </div>

                <div className="rounded-lg border bg-background p-3 space-y-1.5">
                  <div className="font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-amber-500/10 text-[10px]">
                      2
                    </span>
                    Sondagem das Dores (SHAP Drivers)
                  </div>
                  <p className="text-muted-foreground text-xs leading-relaxed">
                    {scriptData.roteiro_etapas.etapa_2_sondagem}
                  </p>
                </div>

                <div className="rounded-lg border bg-background p-3 space-y-1.5">
                  <div className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/10 text-[10px]">
                      3
                    </span>
                    Proposta Irrecusável ({scriptData.playbook_aplicado})
                  </div>
                  <p className="text-muted-foreground text-xs leading-relaxed">
                    {scriptData.roteiro_etapas.etapa_3_proposta_valor}
                  </p>
                </div>

                <div className="rounded-lg border bg-background p-3 space-y-1.5">
                  <div className="font-semibold text-primary flex items-center gap-1.5">
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-primary/10 text-[10px]">
                      4
                    </span>
                    Fechamento & Call to Action
                  </div>
                  <p className="text-muted-foreground text-xs leading-relaxed">
                    {scriptData.roteiro_etapas.etapa_4_fechamento}
                  </p>
                </div>
              </div>
            ) : (
              /* WhatsApp / Email Box */
              <div className="relative rounded-lg border bg-background p-3 font-sans leading-relaxed whitespace-pre-wrap">
                {scriptData.mensagem_completa}
              </div>
            )}

            {/* Destaques Estratégicos & Botão de Copiar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t">
              <div className="space-y-1">
                <span className="font-semibold text-foreground">Pilares da Negociação:</span>
                <ul className="list-disc list-inside space-y-0.5 text-muted-foreground">
                  {scriptData.argumentos_chave.map((arg, idx) => (
                    <li key={idx}>{arg}</li>
                  ))}
                </ul>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 text-xs"
                  onClick={handleCopy}
                >
                  {copiado ? (
                    <>
                      <Check size={14} className="text-emerald-500" />
                      Copiado!
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      Copiar Comunicação
                    </>
                  )}
                </Button>
              </div>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  )
}

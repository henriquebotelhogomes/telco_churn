# 06 — Observabilidade e Rastreabilidade

> Como o RetainIQ enxerga a si mesmo. A estratégia cobre os **três pilares**
> (logs, métricas, traces) **mais** o pilar específico de ML: **monitoramento de
> modelo** (qualidade e drift). Atende `RNF-40`–`RNF-43`.

---

## 1. Princípios

1. **Instrumentação padronizada** com **OpenTelemetry** (vendor-neutral) — `ADR-05`.
2. **Correlação total**: todo log, métrica e span carrega `trace_id` e `tenant_id`.
3. **Observabilidade orientada a SLO**: medimos o que importa para o usuário.
4. **MLOps observability**: o modelo é um cidadão monitorável, não uma caixa-preta.

---

## 2. Stack de Observabilidade

| Pilar | Ferramenta | Observação |
|-------|-----------|------------|
| Instrumentação | **OpenTelemetry SDK + Collector** | Único ponto de coleta |
| Métricas | **Prometheus** + Grafana | Scrape de `/metrics` |
| Logs | **Loki** (ou ELK) | Logs estruturados JSON |
| Traces | **Tempo** (ou Jaeger) | Tracing distribuído |
| Dashboards | **Grafana** | Painéis por domínio e SLO |
| Alertas | **Alertmanager** | Roteamento para Slack/e-mail |
| Erros (app) | **Sentry** | Stack traces e regressões |
| ML monitoring | **Evidently** / Prometheus | Drift e performance do modelo |

---

## 3. Logs Estruturados

- **Formato:** JSON, um evento por linha.
- **Campos obrigatórios:** `timestamp`, `level`, `service`, `env`, `tenant_id`,
  `trace_id`, `span_id`, `message`.
- **Eventos de domínio:** `prediction.created` (com `model_version`),
  `action.recorded`, `drift.detected`, `model.promoted`.
- **PII:** nunca logar dados pessoais brutos; aplicar *masking/redaction*.

```jsonc
{
  "timestamp": "2026-06-22T12:00:00.123Z",
  "level": "INFO",
  "service": "inference",
  "env": "prod",
  "tenant_id": "t_acme",
  "trace_id": "f1a2b3c4d5e6",
  "span_id": "a1b2c3",
  "event": "prediction.created",
  "model_version": "xgb-2024.11.0",
  "churn_probability": 0.78,
  "latency_ms": 142
}
```

---

## 4. Métricas (RED + USE + ML)

### 4.1 RED (por endpoint)
- **Rate** — requisições/seg.
- **Errors** — % de respostas 4xx/5xx.
- **Duration** — histograma de latência (p50/p95/p99).

### 4.2 USE (recursos)
- **Utilization / Saturation / Errors** de CPU, memória, fila Redis, conexões DB.

### 4.3 Métricas de Negócio e ML
| Métrica | Tipo | Uso |
|---------|------|-----|
| `predictions_total{model_version,risk_class}` | Counter | Volume por classe |
| `model_inference_latency_seconds` | Histogram | SLO de latência |
| `model_score_distribution` | Histogram | Detecção de prediction drift |
| `model_rocauc_rolling` | Gauge | Performance ao vivo (quando há label) |
| `data_drift_score{feature}` | Gauge | Drift por feature |
| `actions_recorded_total{outcome}` | Counter | Eficácia de retenção |
| `revenue_at_risk` | Gauge | KPI de negócio (North Star) |

---

## 5. Tracing Distribuído

- **Propagação W3C Trace Context** entre Frontend → BFF → Inference → DB/Workers.
- Spans nomeados por operação de domínio (`predict`, `explain`, `persist`).
- Atributos de span: `tenant_id`, `model_version`, `customer_id` (hash), `risk_class`.
- **Trace exemplar** anexado a métricas de latência (exemplars no Prometheus)
  para navegar do gráfico ao trace específico em um clique.

---

## 6. Rastreabilidade (Lineage e Auditoria)

A rastreabilidade vai além de observabilidade técnica — é **auditabilidade do
negócio e do modelo**:

| Dimensão | O que é rastreado |
|----------|-------------------|
| **Predição → Modelo** | Cada predição grava `model_version`, `scored_at`, `trace_id` |
| **Modelo → Dados** | Cada modelo aponta para o dataset/version (DVC/snapshot) que o treinou |
| **Modelo → Métricas** | MLflow guarda métricas de treino/validação por versão |
| **Ação → Resultado** | Ação de retenção ligada à predição que a motivou e ao desfecho |
| **Usuário → Mudança** | Trilha de auditoria (quem alterou config, papéis, modelos) |
| **Requisição → Logs** | `trace_id` correlaciona toda a jornada |

> Resultado: dada *qualquer* predição em produção, é possível responder
> **"qual modelo, treinado com quais dados, gerou este score, e que ação humana
> resultou disso?"** — um forte sinal de maturidade de engenharia de ML.

---

## 7. Monitoramento de Modelo (MLOps)

| Tipo | Detecção | Resposta |
|------|----------|----------|
| **Data drift** | Distribuição de features de entrada vs. baseline de treino (PSI/KL) | Alerta + agenda re-treino (RF-70) |
| **Prediction drift** | Mudança na distribuição de scores | Alerta + investigação |
| **Concept drift** | Queda de AUC/recall quando labels chegam | Re-treino + rollback se necessário |
| **Data quality** | Schema/nulos/ranges (Pandera/GE) | Bloqueio de ingestão + relatório |

---

## 8. SLOs e Error Budget

| SLO | Objetivo | Janela | Error Budget |
|-----|----------|--------|--------------|
| Disponibilidade scoring | 99.9% | 30d | 43 min/mês |
| Latência p95 scoring | < 200 ms | 30d | 1% das req |
| Frescor do modelo | re-treino ≤ 30d ou on-drift | — | — |

- **Política:** ao esgotar o error budget, congela-se feature work e prioriza-se
  confiabilidade (cultura SRE).

---

## 9. Dashboards (Grafana — mínimo)

1. **API Overview** — RED por endpoint, status, latência.
2. **Inference & ML** — volume por risk_class, latência SHAP, distribuição de score.
3. **Model Health** — drift por feature, AUC/recall rolling, frescor do modelo.
4. **Business** — receita em risco, ações registradas, taxa de retenção.
5. **Infra/SLO** — saturação de recursos, error budget burn-down.

---

## 10. Alertas (exemplos)

| Alerta | Condição | Severidade |
|--------|----------|-----------|
| `HighErrorRate` | erros 5xx > 2% por 5 min | 🔴 Crítico |
| `LatencyP95Breach` | p95 > 200 ms por 10 min | 🟠 Alto |
| `ModelDriftDetected` | PSI > 0.2 em feature-chave | 🟠 Alto |
| `ModelPerfDrop` | AUC rolling < 0.79 | 🔴 Crítico |
| `QueueBacklog` | fila batch > limite por 15 min | 🟡 Médio |


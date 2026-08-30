# 07 — Performance e Escalabilidade

> Estratégia para atender aos SLOs de performance (`RNF-10`–`RNF-14`) e escalar
> de uma demo a milhões de clientes monitorados sem reescrita estrutural.

---

## 1. Metas (recapitulação dos SLOs)

| Cenário | Métrica | Alvo |
|---------|---------|------|
| Scoring individual | p95 latência | < 200 ms |
| Scoring + SHAP | p95 latência | < 600 ms |
| Throughput | por réplica | ≥ 150 req/s |
| Batch 100k | duração | < 10 min |
| Cold start | carregar modelo | < 5 s |

---

## 2. Otimização de Latência (caminho de inferência)

1. **Modelo em memória** — carregado no *lifespan* (já implementado), evitando
   I/O de disco por requisição.
2. **SHAP sob demanda** — drivers calculados apenas quando solicitados (detalhe do
   cliente), não na listagem; uso de `TreeExplainer` (rápido para XGBoost).
3. **Vetorização** — inferência em lote usa DataFrames vetorizados, não loop linha
   a linha.
4. **Payload enxuto** — respostas mínimas; campos opcionais sob `?include=drivers`.
5. **Connection pooling** — Postgres/Redis com pools dimensionados.
6. **Serialização eficiente** — Pydantic V2 (Rust core) já adotado; considerar
   `orjson` no FastAPI.
7. **Async I/O** — endpoints I/O-bound assíncronos; CPU-bound (inferência) em
   *thread/worker pool* para não bloquear o event loop.

---

## 3. Estratégia de Caching

| Camada | O que | TTL/Política | Ganho |
|--------|-------|--------------|-------|
| **Resultado de predição** | score por (customer hash + model_version + feature hash) | Invalida ao mudar dados/modelo | Evita recomputar |
| **Explicações SHAP** | drivers por predição | Igual ao score | SHAP é o passo mais caro |
| **Listas/fila priorizada** | página de clientes por filtro | Curto (segundos) | Reduz carga de leitura |
| **HTTP/CDN** | assets do frontend | Longo + hash de build | Web vitals |
| **Model registry** | metadados do modelo ativo | Até nova promoção | Evita round-trips ao MLflow |

- **Stampede protection:** *single-flight*/lock ao recomputar entradas caras.
- **Cache key versionada por `model_version`** — promoção de modelo invalida
  naturalmente o cache.

---

## 4. Processamento Assíncrono e em Lote

- **Batch scoring** desacoplado via fila (Redis + Celery/Arq):
  - API cria *job* → retorna `jobId` (202 Accepted) → cliente faz *poll* ou recebe webhook.
  - Particionamento em *chunks* processados em paralelo por múltiplos workers.
- **Backpressure:** limites de fila e *rate limiting* por tenant evitam que um
  tenant degrade os demais (*noisy neighbor*).
- **Idempotência:** jobs idempotentes por chave para retries seguros.

---

## 5. Escalabilidade Horizontal

| Componente | Estratégia |
|------------|-----------|
| Web / BFF / Inference | **HPA** por CPU + latência custom (KEDA/Prometheus) |
| Workers de batch | **KEDA** escalando por profundidade de fila (scale-to-zero) |
| PostgreSQL | Réplicas de leitura para analytics; particionamento por tenant em escala |
| Redis | Cluster/replica; separar cache de broker |
| Object storage | Escala gerenciada (S3) |

- **Stateless services** (`RNF-20`) permitem adicionar réplicas sem coordenação.
- **Sharding por tenant** disponível como evolução para tenants muito grandes.

---

## 6. Escalabilidade de Dados

- **Particionamento** de tabelas de predições por `tenant_id` + tempo.
- **Retenção em camadas:** dados quentes em Postgres, históricos em object
  storage/warehouse (Parquet) para analytics de baixo custo.
- **CQRS leve:** leituras analíticas separadas das escritas operacionais.
- **Feature Store (V1+)** para reuso consistente de features online/offline e
  redução de recomputação.

---

## 7. Eficiência de Custo (FinOps)

- **Scale-to-zero** em workers ociosos (KEDA).
- **Right-sizing** guiado por métricas USE.
- **Cache agressivo** reduz computação de SHAP (passo mais caro).
- **Spot/preemptible** para jobs de re-treino tolerantes a interrupção.
- **Orçamento por tenant** evita custos descontrolados.

---

## 8. Teste de Performance e Capacidade

| Tipo | Ferramenta | Objetivo |
|------|-----------|----------|
| Carga | k6 / Locust | Validar p95 e throughput nos SLOs |
| Estresse | k6 | Encontrar ponto de saturação |
| Soak | k6 | Vazamentos de memória / degradação no tempo |
| Spike | k6 | Comportamento sob picos súbitos |

- **Planejamento de capacidade:** curva req/s × réplicas documentada; alvo de
  utilização ~60–70% para absorver picos.
- **Gate de performance no CI:** teste de carga em staging bloqueia regressões de
  latência além do limiar.

---

## 9. Resiliência sob Carga

- **Timeouts** e **retries com backoff + jitter** em dependências externas.
- **Circuit breaker** para fontes de dados/serviços instáveis.
- **Bulkheads:** pools isolados por tipo de carga (inferência vs. ingestão).
- **Graceful degradation:** sob estresse, prioriza scoring; SHAP/analytics podem
  ser adiados (`RNF-05`).

---

## 10. Roadmap de Escala (resumo)

| Estágio | Clientes monitorados | Topologia |
|---------|----------------------|-----------|
| Demo/MVP | até ~100k | Monólito modular + 1 worker |
| V1 | ~1M | HPA + KEDA + réplica de leitura |
| Escala | 5M+ | Sharding por tenant + warehouse + feature store |


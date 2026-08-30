# 📄 Product Requirement Document (PRD) — RetainIQ Fase 2: Global Scale-Up Architecture (Enterprise Tier-1)

> **De SaaS Especialista a Plataforma Global de Alta Concorrência & Escala Planetária**  
> **Versão:** 3.0.0-ENTERPRISE | **Status:** Aprovado para Planejamento & Execução | **Padrão:** Big Tech / Global Scale-Up (Nubank, Uber, Netflix Tier-1)  
> **Guia para Implementação:** Este PRD formaliza a arquitetura, padrões de engenharia, schemas e contratos necessários para escalar o RetainIQ de dezenas de milhares para **dezenas de milhões de clientes ativos**, com **$100.000\text{ req/s}$**, latência **$p99 < 15\text{ms}$**, isolamento multi-tenant seguro e segurança GenAI de nível corporativo.

---

## 1. Visão Executiva & Contexto de Escala Global

O **RetainIQ (Fase 1 - Marcos M0 a M10)** consolidou uma arquitetura moderna de MLOps, inferência em tempo real, explicabilidade TreeSHAP, simulador prescritivo, persistência relacional assíncrona, Copilot GenAI e Continuous Training.

A **Fase 2 (Global Scale-Up)** eleva o ecossistema para suportar os requisitos de telecomunicações e fintechs globais de hiperescala:
1. **Alta Volumetria de Eventos:** Milhões de interações por segundo (quedas de chamada, telemetria de rede, faturas em atraso, interações no app).
2. **Features em Tempo Real (Zero Skew):** Cálculo instantâneo de agregações temporais (janelas deslizantes de 1h, 24h, 7d) sem divergência entre treino e inferência.
3. **Multi-Tenancy Corporativo:** Suporte a múltiplas operadoras e filiais globais na mesma infraestrutura com isolamento criptográfico e conformidade rigorosa (LGPD / GDPR / SOC2).
4. **Resiliência & Zero-Downtime:** Topologia multi-região com failover ativo-ativo, canary releases inteligentes e autoscaling com KEDA.
5. **Governança & AI Safety:** Blindagem do Copilot GenAI contra alucinações comerciais, violações de PII e geração fora de conformidade jurídica.

---

## 2. Diagrama da Arquitetura Global (Fase 2)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EVENT SOURCES & STREAMING INGESTION                                   │
│  [Network Probes]      [Billing Systems]      [CRM / App Events]      [Call Center IVR]               │
│          │                    │                       │                      │                        │
│          └────────────────────┼───────────────────────┴──────────────────────┘                        │
│                               ▼                                                                       │
│               APACHE KAFKA / AWS KINESIS (Partitioned by customer_id)                                  │
└───────────────────────────────┬───────────────────────────────────────────────────────────────────────┘
                                │ Stream Ingestion
                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              STREAM PROCESSING & STATEFUL COMPUTATION                                 │
│                                       (Apache Flink Cluster)                                          │
│  • Sliding Windows (1h, 24h, 7d)  • Network Degradation Score  • Payment Failure Counter              │
└───────────────────────────────┬───────────────────────────────────────────────────────────────────────┘
                                │ Dual-Write Ingestion
                ┌───────────────┴────────────────┐
                ▼                                ▼
┌───────────────────────────────┐  ┌────────────────────────────────────────────────────────────────────┐
│      ONLINE FEATURE STORE     │  │                    OFFLINE LAKEHOUSE / DWH                         │
│     (Feast + Redis Cluster)   │  │              (BigQuery / Snowflake / Apache Iceberg)               │
│  • Low Latency (< 2ms)        │  │  • Historical Point-in-Time Joins                                  │
│  • Real-time Feature Serving  │  │  • Continuous Training Datasets (Zero Data Leakage)                │
└───────────────┬───────────────┘  └─────────────────────┬──────────────────────────────────────────────┘
                │                                        │
                │ Real-time Features                     │ Offline Training
                ▼                                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          KUBERNETES CLOUD-NATIVE SERVING & ORCHESTRATION                              │
│                               (EKS / GKE + Istio Service Mesh + KEDA)                                 │
│                                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              API GATEWAY (OAuth2 / OIDC Keycloak)                               │  │
│  │  • Multi-Tenancy Resolution (Tenant Context Injection)  • Rate Limiting & JWT Validation        │  │
│  └────────────────────────────────────────────────┬────────────────────────────────────────────────┘  │
│                                                   │                                                   │
│      ┌────────────────────────────────────────────┴────────────────────────────────────────────┐      │
│      ▼                                                                                         ▼      │
│  ┌─────────────────────────────────────────────────┐   ┌───────────────────────────────────────────┐  │
│  │         INFERENCE PODS (HPA / KEDA)             │   │        GENAI COPILOT PODS (NVIDIA NeMo)   │  │
│  │  • Champion / Challenger Routing (Istio Canary) │   │  • PII Masking (Microsoft Presidio)       │  │
│  │  • Caching Inteligente (Dragonfly / Redis)      │   │  • Guardrails Anti-Alucinação             │  │
│  │  • Multi-Model Serving (Triton / TorchServe)    │   │  • Multi-Agent Negotiation (LangGraph)    │  │
│  └────────────────────────┬────────────────────────┘   └─────────────────────┬─────────────────────┘  │
└───────────────────────────┼──────────────────────────────────────────────────┼────────────────────────┘
                            │                                                  │
                            ▼                                                  ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                            ENTERPRISE PERSISTENCE & DATA GOVERNANCE                                   │
│  ┌─────────────────────────────────────────────────┐   ┌───────────────────────────────────────────┐  │
│  │       POSTGRESQL CLUSTER (Row-Level Security)   │   │         AI EVALUATION & OBSERVABILITY     │  │
│  │  • Strict Tenant Isolation (RLS Policies)       │   │  • Continuous Evaluation com Ragas        │  │
│  │  • Imutabilidade de Auditoria & CDC (Debezium)  │   │  • Prometheus + Grafana + OpenTelemetry   │  │
│  │  • GDPR / LGPD Cryptographic Erasure            │   │  • Evidently Data & Prediction Drift      │  │
│  └─────────────────────────────────────────────────┘   └───────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Os 6 Pilares de Engenharia & Épicos da Fase 2

### 🌊 Pilar 1: Ingestão em Streaming & Feature Engineering em Tempo Real (Kafka + Flink)
- **Desafio:** Cálculos como *"número de falhas de conexão nos últimos 15 minutos"* ou *"tentativas de recarga falhadas nas últimas 2 horas"* não podem esperar batches noturnos.
- **Solução Técnica:**
  - Tópicos Kafka particionados por `customer_id` com chaves semânticas: `telemetry.network.events`, `billing.payment.events`, `crm.interaction.events`.
  - Jobs em **Apache Flink (PyFlink)** com estado persistido (*RocksDB State Backend*) processando janelas deslizantes (*sliding windows*) e *tumbling windows*.
  - Emissão contínua para o Online Store do Feast e para o Data Lake via Apache Iceberg.

### 🏪 Pilar 2: Feature Store Enterprise (Feast + Redis + BigQuery)
- **Desafio:** Prevenir *Train-Serving Skew* e inconsistências temporais durante o treinamento de modelos.
- **Solução Técnica:**
  - Repositório central de definições `feature_store.yaml` com Feast 0.40+.
  - **Online Store:** Redis Cluster / DragonflyDB com latência de leitura sub-milissegundo ($< 2\text{ms}$).
  - **Offline Store:** BigQuery / Snowflake com suporte a `get_historical_features()` garantindo junções *point-in-time* matematicamente imunes a data leakage.

```python
# Exemplo de Contrato de Feature Feast (src/churn_prediction/feature_store/features.py)
from datetime import timedelta
from feast import Entity, FeatureView, Field, ValueType
from feast.types import Float32, Int64

customer = Entity(name="customer_id", value_type=ValueType.STRING, join_keys=["customer_id"])

customer_realtime_stats = FeatureView(
    name="customer_realtime_stats",
    entities=[customer],
    ttl=timedelta(days=30),
    schema=[
        Field(name="failed_recharges_last_24h", dtype=Int64),
        Field(name="dropped_calls_last_1h", dtype=Int64),
        Field(name="avg_data_speed_mbps_last_7d", dtype=Float32),
    ],
    online=True,
    source=...,  # Kafka Source / Flink Output Table
)
```

---

### 🛡️ Pilar 3: Segurança Corporativa, Multi-Tenancy & LGPD/GDPR
- **Desafio:** Atender grandes corporações que exigem isolamento estrito de dados por operadora/filial (*multi-tenancy*) e conformidade com leis de privacidade.
- **Solução Técnica:**
  - **Autenticação OIDC:** Integração com Keycloak / Auth0 / Azure AD via tokens JWT assinados com RS256.
  - **Row-Level Security (RLS) no PostgreSQL:** Todas as tabelas contêm a coluna `tenant_id`. Nenhuma query SQL manual precisa filtrar por tenant; o banco aplica o filtro em nível de kernel através de variáveis de sessão da conexão:
    ```sql
    ALTER TABLE customer_predictions ENABLE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_policy ON customer_predictions
        FOR ALL USING (tenant_id = current_setting('app.current_tenant_id'));
    ```
  - **Direito ao Esquecimento (Art. 17 GDPR / LGPD):** Pipeline assíncrono de anonimização criptográfica com destruição de chaves de decriptação (Crypto-Shredding).

---

### ☁️ Pilar 4: Infraestrutura Cloud-Native Kubernetes (K8s + KEDA + Istio)
- **Desafio:** Escalar instantaneamente de 10 pods para 500 pods durante picos de tráfego (ex: Black Friday) sem aumentar latência ou custos ociosos.
- **Solução Técnica:**
  - **Autoscaling com KEDA:** Escalonamento baseado no atraso de processamento de mensagens no Kafka (*Kafka Lag Consumer*) e latência Prometheus ($p99 > 20\text{ms}$).
  - **Service Mesh (Istio):**
    - Encriptação mTLS ponta a ponta entre todos os microserviços.
    - *Canary Deployment* avançado: 95% do tráfego para `v1-champion`, 5% para `v2-challenger`, com espelhamento transparente (*shadow traffic mirroring*).
    - Circuit Breaking automático caso a taxa de erros ultrapasse 1%.

---

### 🤖 Pilar 5: AI Safety & GenAI Guardrails (NVIDIA NeMo + Presidio)
- **Desafio:** O Copilot de negociação não pode inventar descontos fora da alçada permitida, falar palavrões ou expor CPFs/dados sensíveis de clientes.
- **Solução Técnica:**
  - **Microsoft Presidio:** Intercepta e anonimiza dados sensíveis (PII) antes que o prompt seja enviado ao LLM.
  - **NeMo Guardrails (NVIDIA):**
    - *Input Rails:* Validação de injeção de prompt e jailbreak.
    - *Output Rails:* Validação determinística de regras comerciais (ex: "O desconto máximo permitido é 20% do MRR").
    - *Hallucination Check:* Verificação semântica de consistência contra as predições de TreeSHAP e o playbook prescrito.

---

### 📈 Pilar 6: Continuous Evaluation & Multi-Agent Retention Loop (LangGraph + Ragas)
- **Desafio:** Garantir que o Copilot continue gerando mensagens empáticas, persuasivas e factuais ao longo do tempo.
- **Solução Técnica:**
  - **Framework Ragas:** Avaliação automatizada de 100% das respostas geradas em background com métricas:
    - *Faithfulness* (Fidelidade aos dados cadastrais e SHAP).
    - *Answer Relevance* (Relevância da resposta para o canal escolhido).
    - *Tone Adherence* (Aderência ao tom selecionado: Empático, Direto ou Consultivo).
  - **Orquestração Multi-Agente com LangGraph:** Fluxo de retenção com agentes especializados (Agente de Diagnóstico SHAP, Agente de Otimização Financeira e Agente de Negociação).

---

## 4. Estrutura de Arquivos da Fase 2 (Árvore Alvo)

```
telco_churn/
├── infra/
│   ├── k8s/
│   │   ├── base/                    # Deployments, Services, ConfigMaps, Ingress
│   │   ├── overlays/
│   │   │   ├── staging/             # Configurações de Staging
│   │   │   └── prod/                # Configurações de Produção Multi-Região
│   │   ├── istio/                   # VirtualServices, DestinationRules, Canary Routing
│   │   └── keda/                    # ScaledObjects orientados a Kafka Lag
│   └── terraform/                   # Provisão EKS/GKE, Kafka MSK, Redis Cluster, Postgres RDS
├── specs/
│   ├── 00_index.md
│   ├── ...
│   └── 12_global_scaleup_architecture.md # Especificação Técnica Detalhada
├── src/
│   └── churn_prediction/
│       ├── feature_store/           # Feast Feature Views, Entities e Offline/Online configs
│       │   ├── __init__.py
│       │   ├── feature_store.yaml
│       │   └── definitions.py
│       ├── streaming/               # Ingestão de Streaming e PyFlink jobs
│       │   ├── __init__.py
│       │   ├── flink_job.py
│       │   └── kafka_producer.py
│       ├── security/                # Autenticação OIDC, Multi-Tenancy RLS e GDPR
│       │   ├── __init__.py
│       │   ├── oidc.py
│       │   ├── tenant_context.py
│       │   └── crypto_shredding.py
│       ├── guardrails/              # NeMo Guardrails & Presidio PII Masking
│       │   ├── __init__.py
│       │   ├── rails_config.co
│       │   └── safety_checker.py
│       └── evaluation/              # Ragas Continuous Evaluation para GenAI
│           ├── __init__.py
│           └── ragas_evaluator.py
├── PRD.md                           # PRD Fase 1 (M0 a M10 - Concluído)
├── PRD_PHASE_2_GLOBAL_SCALEUP.md    # Este documento (Fase 2 - Enterprise Tier-1)
└── pyproject.toml
```

---

## 5. Matriz de Épicos & Roadmap da Fase 2

| Épico | Título | Entregáveis Principais | SLA / Métrica de Sucesso |
|:---:|---|---|---|
| **E1** | **Streaming & Real-time Features** | Kafka Producers/Consumers, PyFlink State Engine, Feature View Feast. | Ingestão e agregações calculadas em $< 500\text{ms}$. |
| **E2** | **Feature Store Online & Offline** | Redis Cluster Online Store, BigQuery Offline Store, Historical Point-in-time joins. | Leitura online $< 2\text{ms}$; 0% de data leakage. |
| **E3** | **Multi-Tenancy & Segurança OIDC** | Autenticação Keycloak OIDC, Postgres RLS habilitado, pipeline de deleção GDPR. | 100% de isolamento entre tenants; 0 vazamento de dados. |
| **E4** | **Kubernetes KEDA & Istio Service Mesh** | Helm Charts, ScaledObject KEDA (Kafka Lag), Canary Routing 95/5 no Istio. | Autoscaling de 10 a 500 réplicas em $< 60\text{s}$. |
| **E5** | **AI Safety & Guardrails Corporativos** | Microsoft Presidio PII, NeMo Guardrails para regras de negócio e bloqueio de alucinação. | 100% de bloqueio de PII não autorizado e descontos ilegais. |
| **E6** | **Continuous Evaluation com Ragas** | Pipeline assíncrono de avaliação Ragas, monitor de Faithfulness e Tone Adherence. | Faithfulness Score $\ge 0.92$; Relevância $\ge 0.90$. |

---

## 6. Métricas de Sucesso & SLAs da Fase 2

1. **Disponibilidade Global:** $\ge 99.99\%$ (menos de 4.3 minutos de downtime por mês).
2. **Latência de Inferência em Pico:** $p50 < 4\text{ms}$, $p95 < 10\text{ms}$, $p99 < 15\text{ms}$.
3. **Throughput de Pico:** Suporte a $\ge 100.000\text{ requisições/segundo}$ contínuas.
4. **Fidelidade GenAI:** Score de Faithfulness no Ragas $\ge 92\%$.
5. **Conformidade Legal:** 100% de conformidade com LGPD, GDPR e auditoria SOC2 Tipo II.

---

Este documento serve como a **Especificação Mestre da Fase 2**, pronta para guiar times de engenharia, arquitetos de software e agentes autônomos na evolução contínua da plataforma **RetainIQ**.

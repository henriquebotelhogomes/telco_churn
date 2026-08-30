# 12 — Arquitetura de Nível Global Scale-Up / Enterprise Tier-1

> **Documento Arquitetural de Referência:** Diretrizes, blueprints e especificações técnicas para escalar o **RetainIQ** de uma aplicação de alto desempenho para uma plataforma distribuída multi-região no padrão de Big Techs e Scale-ups globais (ex: Nubank, Stripe, Uber, DoorDash, Databricks).

---

## 1. Visão Geral da Arquitetura Alvo

```
                                      ┌──────────────────────────────────────┐
                                      │     CLOUDFLARE / AWS CLOUDFRONT      │
                                      │   (WAF, DDoS, SSL Termination, CDN)   │
                                      └──────────────────┬───────────────────┘
                                                         │
                                                         ▼
                                      ┌──────────────────────────────────────┐
                                      │      KONG / ISTIO INGRESS GATEWAY    │
                                      │  (Rate Limiting, OIDC Auth, Routing) │
                                      └──────────────────┬───────────────────┘
                                                         │
                        ┌────────────────────────────────┴────────────────────────────────┐
                        │                                                                 │
                        ▼ (Inferência Síncrona / UI)                                      ▼ (Eventos em Tempo Real)
         ┌──────────────────────────────┐                                  ┌──────────────────────────────┐
         │     RETAINIQ API PODS        │                                  │   APACHE KAFKA / KINESIS     │
         │ (Kubernetes HPA, 3..100 pods)│                                  │  (Event Ingestion Cluster)   │
         └──────────────┬───────────────┘                                  └──────────────┬───────────────┘
                        │                                                                 │
         ┌──────────────┴──────────────┐                                                  ▼
         │                             │                                   ┌──────────────────────────────┐
         ▼                             ▼                                   │    APACHE FLINK STREAMING    │
┌─────────────────┐           ┌─────────────────┐                          │  (Real-Time Feature Compute) │
│ ONLINE FEATURE  │           │   RELATIONAL DB │                          └──────────────┬───────────────┘
│ STORE (REDIS)   │           │ (POSTGRES HA /  │                                         │
│ Latência < 5ms  │           │ AURORA MULTI-AZ)│                                         ▼
└─────────────────┘           └─────────────────┘                          ┌──────────────────────────────┐
                                                                           │    FEAST FEATURE STORE       │
                                                                           │ (Online: Redis | Offline: BQ)│
                                                                           └──────────────┬───────────────┘
                                                                                          │
                                                                                          ▼
                                                                           ┌──────────────────────────────┐
                                                                           │ KUBEFLOW / AIRFLOW PIPELINES │
                                                                           │ (Continuous Training & Eval) │
                                                                           └──────────────────────────────┘
```

---

## 2. Os 6 Pilares da Arquitetura Global

### 1. Ingestão em Streaming & Processamento de Eventos (Event-Driven)
- **Problema resolvido:** O churn de clientes é precedido por micro-sinais (quedas de sinal repetidas, falhas no pagamento via cartão, abertura de tickets de suporte). Esperar a virada do mês é tarde demais.
- **Tecnologias:**
  - **Apache Kafka / AWS Kinesis / GCP Pub/Sub:** Ingestão desacoplada de até 500k eventos/segundo particionada por `customer_id`.
  - **Apache Flink:** Janelamento de eventos em tempo real (ex: *"número de falhas de conexão nos últimos 30 minutos"* ou *"frequência de chamados ao suporte nas últimas 24h"*).
  - **Dead Letter Queue (DLQ):** Reprocessamento resiliente de mensagens com payload corrompido sem travar o pipeline.

### 2. Feature Store Centralizada (Consistência Online/Offline)
- **Problema resolvido:** *Train-Serve Skew* (inconsistência onde o modelo é treinado com uma definição de feature e consome outra em produção).
- **Tecnologias:**
  - **Feast / Hopsworks:** Registro central declarativo de features.
  - **Online Store (Redis Enterprise / AWS ElastiCache Cluster):** Recuperação de variáveis em sub-5ms para a API de inferência, recebendo apenas `customer_id` via HTTP.
  - **Offline Store (Snowflake / BigQuery / Databricks Delta Lake):** Armazenamento histórico pontual (*Point-in-Time Joins*) para retreinamento sem vazamento temporal de dados.

### 3. Governança, Segurança & Conformidade Global (GDPR / LGPD / SOC2)
- **Problema resolvido:** Riscos de vazamento de dados, sanções regulatórias e exigências contratuais de clientes enterprise.
- **Tecnologias e Padrões:**
  - **Autenticação & SSO:** OAuth2.0 / OpenID Connect (OIDC) com SAML 2.0 integrado a provedores como Okta, Google Workspace e Microsoft Entra ID (Azure AD).
  - **Multi-Tenancy com RLS:** *Row-Level Security* nativo no PostgreSQL garantindo isolamento criptográfico por organização cliente.
  - **Mascaramento e Anonimização de PII:** Hashing e tokenização irreversível de CPFs, telefones e nomes antes de entrarem no lake de treinamento.
  - **Direito ao Esquecimento (GDPR Art. 17 / LGPD Art. 18):** Endpoint assíncrono para expurgo completo e anonimização de registros do cliente sob demanda.

### 4. Infraestrutura em Nuvem, Kubernetes & Resiliência (Cloud-Native)
- **Problema resolvido:** Disponibilidade de 99.99% (SLA Tier-1) e suporte a picos sazonais sem desperdício financeiro (FinOps).
- **Especificações:**
  - **Deploy em Kubernetes (EKS/GKE):** Manifesto orquestrado via Helm Charts com **ArgoCD (GitOps)**.
  - **Autoscaling Horizontal (HPA / KEDA):** Escala de pods baseada em métricas customizadas do Prometheus (ex: latência P95 > 50ms ou fila de inferência).
  - **Multi-Region Ativo-Passivo com failover DNS via Cloudflare.**
  - **Service Mesh (Istio / Envoy):** Circuit breaking, mTLS (criptografia pod-to-pod) e injeção controlada de falhas (Chaos Engineering via Chaos Mesh).

### 5. Continuous Training (CT) Automatizado com Canary Deploy
- **Problema resolvido:** Degradação silenciosa da acurácia do modelo devido a mudanças macroeconômicas ou de comportamento de consumo.
- **Fluxo Automatizado:**
  ```
  [Evidently / Prometheus Drift Alert] 
          │
          ▼
  [Airflow / Kubeflow Pipeline Trigger] ──▶ [Extração de Dados da Feature Store]
                                                           │
                                                           ▼
  [Canary Rollback] ◀── [A/B Gate: PR-AUC > Champion?] ◀── [Treino & Validação Cruzada]
          │                        │ (Sim)
          │                        ▼
          │               [Deploy Canary 5% do tráfego]
          │                        │
          │                        ▼
          └────────────── [Promoção Automática a 100%]
  ```
  - **Rollback Automático:** Caso a taxa de erro ou latência do modelo novo supere o threshold em produção, o sistema restaura o modelo anterior em < 2 segundos.

### 6. IA Generativa Corporativa (GenAI Safety & FinOps)
- **Problema resolvido:** Alucinação de ofertas de desconto não autorizadas ou estouro de custos de API de LLMs em escala.
- **Padrões:**
  - **Guardrails Semânticos (NeMo Guardrails / Llama Guard):** Validação estrita das saídas da LLM antes de exibir ao atendente (ex: impedir concessão de descontos acima de 20%).
  - **Roteamento Semântico e Caching (GPTCache / Semantic Cache):** Respostas de scripts frequentes são cacheadas por similaridade vetorial, reduzindo custos de API em até 60%.
  - **Fallback Determinístico Local:** Se a API de nuvem (Gemini / OpenAI) falhar ou sofrer throttling, o motor ativa templates determinísticos instantaneamente.

---

## 3. Matriz de Maturidade Técnica (MLOps Maturity Model)

| Dimensão | Estado Atual do RetainIQ | Estado Global Scale-Up (Tier-1) |
|---|---|---|
| **Ingestão** | REST síncrono (JSON / CSV Batch) | Event-Driven Streaming (Kafka + Flink) |
| **Features** | Extração inline no pipeline scikit-learn | Feature Store unificada (Feast / Redis / Snowflake) |
| **Model Registry** | Dinâmico local com `registry.json` e Shadow Scoring | MLflow / Vertex AI Model Registry + Canary Kubernetes |
| **Observabilidade** | Prometheus + Evidently (Ring Buffer TTL) | Datadog / Grafana MLOps + OpenTelemetry Tracing distribuído |
| **Retreinamento** | Manual via script / endpoint admin | Continuous Training (CT) automatizado por Drift Triggers |
| **Segurança** | API Key + Trilha de Auditoria Relacional | OAuth2/OIDC + Multi-Tenancy RLS + Mascaramento PII |

---

## 4. Guia Rápido para Entrevistas de System Design (Staff / Lead)

Ao defender esta arquitetura em sabatinas técnicas:
1. **Destaque o desacoplamento:** *"Separamos a camada de inferência stateless da Feature Store para garantir latência P95 < 40ms independente do tamanho do histórico do cliente."*
2. **Defenda o Shadow Scoring:** *"Adotamos Shadow Scoring antes de qualquer promoção de modelo para comparar divergência de distribuição e latência sem arriscar o faturamento da empresa."*
3. **Aborde FinOps:** *"O cálculo de ROI anual esperado no simulador What-If orienta a priorização da fila de risco, maximizando o MRR preservado por hora de atendimento."*

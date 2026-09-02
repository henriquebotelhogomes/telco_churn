# 📉 RetainIQ — Customer Retention Intelligence & MLOps Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Streaming](https://img.shields.io/badge/Streaming-Kafka%20%7C%20Flink%20%7C%20SSE-FF6F00?style=flat&logo=apachekafka&logoColor=white)](https://github.com/henriquebotelhogomes/telco_churn)
[![Feature Store](https://img.shields.io/badge/Feature_Store-Feast%20%2B%20Redis-red?style=flat&logo=redis&logoColor=white)](https://feast.dev/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-KEDA_Autoscaling-326CE5?style=flat&logo=kubernetes&logoColor=white)](https://keda.sh/)
[![AI Safety](https://img.shields.io/badge/AI_Safety-Guardrails%20%26%20Ragas-6C5CE7?style=flat)](https://github.com/henriquebotelhogomes/telco_churn)
[![Tests](https://img.shields.io/badge/Tests-102_Passing_(100%25)-success?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Coverage](https://img.shields.io/badge/Coverage-90.32%25-brightgreen?style=flat)](https://github.com/henriquebotelhogomes/telco_churn)
[![Docs](https://img.shields.io/badge/Docs-MkDocs_Material-526CFE?style=flat&logo=material-for-mkdocs&logoColor=white)](https://henriquebotelhogomes.github.io/telco_churn/)

> **Plataforma Enterprise de Inteligência de Retenção, Streaming em Tempo Real e MLOps:** Uma solução completa de Machine Learning e Inteligência Artificial que fecha o ciclo operacional corporativo: **Ingestão em Streaming $\rightarrow$ Feature Store (Feast) $\rightarrow$ Predição de Risco de Churn $\rightarrow$ Explicabilidade com TreeSHAP $\rightarrow$ Prescrição com ROI Anual $\rightarrow$ Copilot GenAI com AI Safety $\rightarrow$ Closed-Loop com Desfecho Real $\rightarrow$ Continuous Training com Quality Gate**.

---

## 📌 Índice

1. [Visão Executiva e Problema de Negócio](#-visão-executiva-e-problema-de-negócio)
2. [Arquitetura Geral do Sistema (Tier-1 Scale-Up)](#-arquitetura-geral-do-sistema-tier-1-scale-up)
3. [Diferenciais de Engenharia de Dados & ML](#-diferenciais-de-engenharia-de-dados--ml)
4. [Live Streaming Engine & Cockpit Reativo](#-live-streaming-engine--cockpit-reativo)
5. [Feature Store Unificada (Feast + Redis)](#-feature-store-unificada-feast--redis)
6. [Multi-Tenancy & Row-Level Security (B2B SaaS)](#-multi-tenancy--row-level-security-b2b-saas)
7. [Engenharia de Dados Sintéticos (Telco 360 Enterprise)](#-engenharia-de-dados-sintéticos-telco-360-enterprise)
8. [Benchmarks de Modelos & TreeSHAP](#-benchmarks-de-modelos--treeshap)
9. [Copilot GenAI, AI Safety Guardrails & Ragas Eval](#-copilot-genai-ai-safety-guardrails--ragas-eval)
10. [Kubernetes, KEDA Autoscaling & MLOps](#-kubernetes-keda-autoscaling--mlops)
11. [🎙️ Como Apresentar Este Projeto em Entrevistas Técnicas (Pitch Script)](#-como-apresentar-este-projeto-em-entrevistas-técnicas-pitch-script)
12. [Qualidade de Código & Bateria de Testes](#-qualidade-de-código--bateria-de-testes)
13. [Como Executar o Projeto Localmente e com Docker](#-como-executar-o-projeto-localmente-e-com-docker)

---

## 💼 Visão Executiva e Problema de Negócio

Em operadoras de telecomunicações e serviços por assinatura, reter um cliente custa de **5 a 7 vezes menos** do que adquirir um novo (CAC vs. LTV). 

A imensa maioria dos projetos de Data Science limita-se a um arquivo `.ipynb` estático calculando probabilidades desconectadas da realidade corporativa. O **RetainIQ** foi desenhado seguindo padrões de engenharia de Big Techs e Scale-ups globais:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 1. STREAMING    │       │ 2. PREDIZER     │       │ 3. EXPLICAR     │
│ Kafka + Flink   ├──────►│ Risco e MRR     ├──────►│ TreeSHAP        │
│ Telemetria Rede │       │ em risco (R$)   │       │ Fatores Reais   │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
┌─────────────────┐       ┌─────────────────┐       ┌────────▼────────┐
│ 6. RETREINAR    │       │ 5. APRENDER     │       │ 4. PRESCREVER   │
│ Continuous MLOps│◄──────┤ Closed-Loop     │◄──────┤ What-If & GenAI │
│ Quality Gate PR │       │ Ground Truth    │       │ Copilot Safe    │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

## 🏛️ Arquitetura Geral do Sistema (Tier-1 Scale-Up)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     FRONTEND COCKPIT                                        │
│                 (React 19 + TypeScript + Vite + Tailwind CSS + TanStack Query)              │
│  ┌─────────────────────────┬──────────────────────────┬──────────────────────────────────┐  │
│  │   Dashboard Executivo   │   Fila de Riscos (Table) │   Live Streaming Ticker (SSE)    │  │
│  │   • KPIs em Reais (R$)  │   • Tooltips Explicativos│   • Recálculo Dinâmico < 5ms     │  │
│  │   • Dossiê C-Level      │   • TreeSHAP Waterfall   │   • Chaos Studio Injection       │  │
│  │   • Switch Multi-Tenant │   • Simulador What-If    │   • Telemetria FTTH / 5G         │  │
│  └─────────────────────────┴──────────────────────────┴──────────────────────────────────┘  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ HTTP REST & SSE EventSource (Porta 8000)
┌──────────────────────────────────────────────▼──────────────────────────────────────────────┐
│                                     FASTAPI ENGINE                                          │
│                                                                                             │
│  ┌───────────────────────────────┐  ┌─────────────────────────────┐  ┌───────────────────┐  │
│  │  Streaming Consumer & SSE Hub │  │   Feast Online Store (Redis)│  │ Model Registry    │  │
│  │  • Broadcast de Eventos       │  │   • Latência < 3ms          │  │ • CatBoost (Champ)│  │
│  │  • Janelas Deslizantes Flink  │  │   • Time-Travel Offline     │  │ • XGBoost / LGBM  │  │
│  └───────────────┬───────────────┘  └──────────────┬──────────────┘  └─────────▲─────────┘  │
│                  │                                 │                           │            │
│  ┌───────────────▼───────────────┐  ┌──────────────▼──────────────┐  ┌─────────┴─────────┐  │
│  │   AI Safety & Ragas Judge     │  │  Synthetic Data Generator   │  │ Continuous MLOps  │  │
│  │   • Detecção PII (Regex/NER)  │  │  • 40 Atributos Telco 360   │  │ • Quality Gate PR │  │
│  │   • Bloqueio Prompt Injection │  │  • Causalidade de Redes     │  │ • Promoção Atômica│  │
│  └───────────────────────────────┘  └─────────────────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Live Streaming Engine & Cockpit Reativo

- **Event Generator com Chaos Studio:** Simula telemetria de sinal óptico (dBm), latência (ms), perda de pacotes e reclamações de CRM via Kafka.
- **Injeção de Cenários de Caos:** Queda massiva de fibra regional, degradação de latência 5G e falhas de débito automático acionáveis via API e UI.
- **SSE Broadcaster Hub:** Distribui eventos de streaming para navegadores conectados com heartbeat a cada 10s e isolamento por Tenant.
- **Live Scorer Engine:** Recalcula o risco de churn ($p_{\text{live}}$) em menos de **$5\text{ms}$** combinando o modelo com as janelas temporais de Flink.

---

## 🏬 Feature Store Unificada (Feast + Redis)

- **Consistência Online/Offline:** Elimina o *training-serving skew* compartilhando as mesmas definições de entidades e feature views.
- **Online Store de Baixa Latência:** Busca de vetores de features de clientes em sub-milissegundos via Redis.
- **Materialização Periódica:** Pipeline automatizado para sincronização de features batch para a camada operacional.

---

## 🏢 Multi-Tenancy & Row-Level Security (B2B SaaS)

- **Isolamento de Dados por Operadora:** Suporte nativo a partições isoladas para **Vivo**, **Claro**, **TIM** e visão Global.
- **Row-Level Security (RLS):** Garantia matemática de que atendentes de uma operadora nunca acessem clientes ou KPIs de outra.
- **Switch de Tenant em Tempo Real:** O Cockpit reconfigura cabeçalhos `X-Tenant-ID` e recarrega os dados instantaneamente.

---

## 🇧🇷 Engenharia de Dados Sintéticos (Telco 360 Enterprise)

Em conformidade rigorosa com a **LGPD** e sigilo de telecomunicações, o RetainIQ incorpora um gerador probabilístico causal:
- **40 Atributos de Alta Fidelidade:** Telemetria FTTH/5G (`avg_latency_ms`, `fiber_outages_count_90d`, `packet_loss_pct`), CRM WhatsApp (`whatsapp_sentiment_score`, `nps_score`, `csat_score`) e financeiro (`pix_payment_enabled`, `billing_disputes`).
- **Botão de Síntese Reativa no Cockpit:** Gere bases de `5.000` a `25.000` clientes com 1 clique, com injeção direta em memória sem bloqueio de cache.

---

## 📊 Benchmarks de Modelos & TreeSHAP

| Algoritmo | ROC-AUC | PR-AUC | Acurácia | Latência $p99$ | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 🥇 **CatBoost Classifier** | **0.864** | **0.672** | **81.4%** | **4.2 ms** | **Champion Atual** |
| 🥈 **LightGBM Classifier** | 0.859 | 0.665 | 80.8% | 3.1 ms | Challenger 1 |
| 🥉 **XGBoost Classifier** | 0.851 | 0.658 | 80.2% | 4.8 ms | Challenger 2 |

- **Explicabilidade com TreeSHAP:** Decompõe a probabilidade de cada cliente em forças aditivas, indicando os principais fatores que aumentam ou reduzem o risco.

---

## 🛡️ Copilot GenAI, AI Safety Guardrails & Ragas Eval

- **Abordagens Comerciais Automatizadas:** Gera roteiros customizados para WhatsApp, E-mail e Call Center com cálculo de ROI anual.
- **AI Safety Guardrails:** Sanitização automática de dados pessoais sensíveis (PII: CPFs, e-mails, cartões), detecção de *prompt injection* e teto de desconto financeiro.
- **Avaliação Contínua com Ragas:** LLM-as-a-Judge avaliando fidelidade factual (*faithfulness*), relevância da resposta e alinhamento de segurança.

---

## ☸️ Kubernetes, KEDA Autoscaling & MLOps

- **Manifestos K8s Prontos para Produção:** `Deployment`, `Service`, `HPA`, `ScaledObject` (KEDA) e `ConfigMap`.
- **KEDA ScaledObject:** Escala horizontal de pods baseada na taxa de requisições por segundo e no tamanho da fila Kafka.
- **Monitoramento de Drift com Evidently & Prometheus:** Exportador de métricas para Grafana com alertas de desvio de distribuição de dados.

---

## 🎙️ Como Apresentar Este Projeto em Entrevistas Técnicas (Pitch Script)

> *"O RetainIQ é uma plataforma de Inteligência de Retenção e MLOps desenvolvida para o setor de telecomunicações. Ao invés de ser apenas um modelo preditivo isolado, ele cobre todo o ciclo de vida analítico e operacional.*
>
> *Na ingestão, conectamos um pipeline de streaming com Kafka e Flink para capturar telemetria de rede e sentimento de CRM em tempo real, servidos por uma Feature Store Feast sobre Redis. O motor de inferência utiliza CatBoost com explicabilidade TreeSHAP em milissegundos e prioriza a fila de atendimento por MRR em Risco monetário (R$).*
>
> *Na ponta da ação comercial, integramos um Copilot GenAI protegido por Guardrails de AI Safety e avaliado via Ragas. A plataforma suporta Multi-Tenancy com Row-Level Security, retreino contínuo com Quality Gate e orquestração em Kubernetes com KEDA, contando com 100% de testes automatizados e mais de 90% de cobertura de código."*

---

## 🧪 Qualidade de Código & Bateria de Testes

```bash
# Executar suíte completa de testes com cobertura
uv run pytest tests/ -v --cov=churn_prediction --cov-fail-under=80

# Linting e Checagem de Tipos Estrita
uv run ruff check src tests
uv run mypy src
```

- ✅ **102 Testes Automatizados (100% Passing)**
- 📈 **90.32% de Cobertura de Código**
- ⚡ **Tempo Médio de Execução:** ~20s

---

## 🚀 Como Executar o Projeto

### Opção 1: Via Docker (Recomendado)
```bash
docker build -t retainiq:latest .
docker run -p 8000:8000 retainiq:latest
```
Acesse [`http://localhost:8000`](http://localhost:8000) no seu navegador.

### Opção 2: Localmente para Desenvolvimento
```bash
# 1. Instalar dependências Python
uv sync

# 2. Compilar Frontend React
cd frontend
npm install
npm run build
cd ..

# 3. Iniciar API FastAPI e Cockpit
uv run uvicorn churn_prediction.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📚 Documentação Completa

Acesse a documentação interativa gerada com **Material for MkDocs**:
- **Portal Online:** [`https://henriquebotelhogomes.github.io/telco_churn/`](https://henriquebotelhogomes.github.io/telco_churn/)
- **Swagger / OpenAPI:** [`http://localhost:8000/docs`](http://localhost:8000/docs)
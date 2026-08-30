# 📉 RetainIQ — Enterprise AI & MLOps Retention Platform (Telco Churn)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-19.2+-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6?style=flat&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-F37626?style=flat&logo=xgboost&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-Async_ORM-D71F00?logo=sqlalchemy&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ED?style=flat&logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-72_Passing-success?logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-90.88%25-brightgreen)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

> **De Modelo Preditivo a Plataforma Enterprise de Retenção & MLOps:** Uma solução completa de Inteligência Artificial aplicada ao negócio, combinando Engenharia de Software robusta, Governança Multi-Modelo, Copilot GenAI, Continuous Training automatizado e Relatórios Executivos C-Level.

---

## 🏛️ Arquitetura de Ponta a Ponta

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND COCKPIT                                     │
│                     (React 19 + TypeScript + Vite + Tailwind CSS + shadcn)              │
│  ┌─────────────────────────┬──────────────────────────┬──────────────────────────────┐  │
│  │   Dashboard Executivo   │   Risk Queue (Table)     │   MLOps Lab & CT Panel       │  │
│  │   • KPIs de MRR Salvo   │   • Customer 360 & SHAP  │   • Multi-Model Registry     │  │
│  │   • Dossiê Executivo    │   • Simulador What-If    │   • Continuous Training (CT) │  │
│  │   • Evolução Temporal   │   • Copilot GenAI        │   • Evidently Data Drift     │  │
│  └─────────────────────────┴──────────────────────────┴──────────────────────────────┘  │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ HTTP REST / WebSocket (Porta 8000)
┌────────────────────────────────────────────▼────────────────────────────────────────────┐
│                                   FASTAPI APPLICATION                                   │
│                                                                                         │
│  ┌─────────────────────────────────┐       ┌─────────────────────────────────────────┐  │
│  │      Data Ingestion Layer       │       │       Continuous Training (CT) Engine   │  │
│  │  • Pandera Strict Contracts     │       │  • Background Multi-Model Retrain       │  │
│  │  • Dual Ingest (JSON / CSV)     │       │  • Quality Gate (PR-AUC vs Champion)   │  │
│  │  • PT-BR/EN-US Translation      │       │  • Zero-Downtime Atomic Promotion       │  │
│  └────────────────┬────────────────┘       └────────────────────▲────────────────────┘  │
│                   │                                             │                       │
│  ┌────────────────▼────────────────┐       ┌────────────────────┴────────────────────┐  │
│  │  Explainability & Prescriptions │       │       Model Registry & Serving          │  │
│  │  • TreeSHAP Divergent Drivers   │       │  • Champion/Challenger Framework        │  │
│  │  • Prescriptive Playbooks       │       │  • Shadow Scoring (Non-blocking)        │  │
│  │  • What-If Simulator & ROI      │       │  • XGBoost, RF, HistGB, Logistic Reg.   │  │
│  └────────────────┬────────────────┘       └────────────────────▲────────────────────┘  │
│                   │                                             │                       │
│  ┌────────────────▼────────────────┐       ┌────────────────────┴────────────────────┐  │
│  │   GenAI Copilot de Retenção     │       │    Persistence & Closed-Loop Engine     │  │
│  │  • Gemini / OpenAI Engine       │       │  • Async SQLAlchemy 2.0 (SQLite/PG)     │  │
│  │  • High-Fidelity Fallback       │       │  • Outcome Logging & MRR Saved Tracking │  │
│  │  • Tone Engine (Empático/Direto)│       │  • Executive Retention Dossier Gen.     │  │
│  └─────────────────────────────────┘       └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🏆 Matriz de Marcos Implementados (M0 a M10)

| Marco | Componente / Funcionalidade | Destaque Técnico |
|:---:|---|---|
| **M0** | **Higiene & Quality Gate** | Gerenciamento ultrarrápido com `uv`, healthcheck de liveness probe e barreira de cobertura `>= 80%` no CI. |
| **M1** | **Explicabilidade TreeSHAP & Prescrição** | Cálculo exato de TreeSHAP em milissegundos, mapeamento semântico de dores e prescrição automatizada de playbooks de retenção. |
| **M2** | **Contratos Pandera & Simulador What-If** | Validação estrita de esquemas em tempo de execução, ingestão dual (JSON PT-BR ou CSV EN-US) e simulador interativo de ROI. |
| **M3** | **Observabilidade & Drift (Evidently)** | Métricas Prometheus em `/metrics`, ring buffer em memória fora do caminho crítico e relatório de Data Drift com cache inteligente. |
| **M4** | **Frontend SPA Cockpit Moderno** | Interface de alta fidelidade em **React 19 + TypeScript + Vite + Tailwind CSS + Radix UI / TanStack Table** (Zero-Streamlit). |
| **M5** | **Entrega Docker Multi-Stage & CI/CD** | Container unificado (Node 22 + Python 3.12 slim), execução não-root e pipeline de testes no GitHub Actions. |
| **M6** | **Persistência Relacional & Closed-Loop** | Banco relacional assíncrono com SQLAlchemy 2.0, registro de aplicação de playbooks, desfecho real (*Ground Truth*) e tracking de MRR salvo. |
| **M7** | **Champion/Challenger & Dynamic Registry** | Treinamento de 4 algoritmos candidatos, inferência em tempo real com Shadow Scoring e promoção atômica de modelos sem downtime. |
| **M8** | **Copilot GenAI de Retenção & Negociação** | Assistente com suporte a Gemini/OpenAI e Fallback Heurístico, gerando roteiros de call center estruturados e mensagens com variação de tom. |
| **M9** | **Continuous Training (CT) Automatizado** | Self-healing pipeline assíncrono acionado por API ou alerta de Drift, com validação de Quality Gate ($PR\text{-}AUC$) e auditoria de jobs. |
| **M10** | **Executive Retention Dossier & Relatório C-Level** | Geração e exportação instantânea de Dossiê Executivo completo em HTML/PDF print-ready com indicadores financeiros, top riscos e MLOps. |

---

## 📊 Benchmark do Catálogo de Modelos (Model Registry)

| Modelo | Algoritmo | Papel | ROC-AUC | PR-AUC | F1-Score | Latência Média |
|---|---|:---:|:---:|:---:|:---:|:---:|
| `churn-xgboost` | XGBoost Classifier | **Champion** | `0.8142` | `0.6107` | `0.5841` | `0.034 ms` |
| `churn-gradient-boosting` | HistGradientBoosting | **Challenger** | `0.8328` | `0.6392` | `0.6110` | `0.035 ms` |
| `churn-logistic-regression` | Regressão Logística | **Challenger** | `0.8414` | `0.6324` | `0.6083` | `0.023 ms` |
| `churn-random-forest` | Random Forest | **Challenger** | `0.8193` | `0.6058` | `0.5793` | `0.049 ms` |

---

## 🚀 Como Executar

### Opção 1: Via Docker (Recomendado para Produção)
```bash
# 1. Construa a imagem multi-stage
docker build -t retainiq-platform .

# 2. Execute o container na porta 8000
docker run -p 8000:8000 retainiq-platform
```
Acesse a aplicação no navegador:
- **Cockpit Frontend:** 👉 http://localhost:8000/
- **API Swagger UI:** 👉 http://localhost:8000/docs
- **Métricas Prometheus:** 👉 http://localhost:8000/metrics

---

### Opção 2: Desenvolvimento Local

```bash
# 1. Instalar dependências backend e frontend
uv sync
cd frontend && npm install && cd ..

# 2. Executar suíte completa de testes e cobertura
uv run pytest tests/ -v --cov=churn_prediction --cov-fail-under=80
cd frontend && npm test && cd ..

# 3. Iniciar Backend FastAPI (porta 8000)
uv run uvicorn churn_prediction.api.main:app --app-dir src --reload --port 8000

# 4. Em outro terminal, iniciar Frontend Vite (porta 5173 com proxy reverso)
cd frontend && npm run dev
```

---

## 🌐 Catálogo de Endpoints REST (`/api/v1`)

| Endpoint | Método | Categoria | Descrição |
|---|:---:|:---:|---|
| `/health` | GET | Infra | Liveness probe para Kubernetes / Docker (`{"status": "ok"}`) |
| `/metrics` | GET | Telemetria | Métricas padrão Prometheus de latência e contadores |
| `/api/v1/predict` | POST | Predição | Predição individual com SHAP Top 3, playbook e persistência |
| `/api/v1/predict/batch` | POST | Predição | Predição em lote via JSON PT-BR ou upload de CSV EN-US |
| `/api/v1/simulate` | POST | Prescrição | Simulador *What-If* interativo com projeção de ROI anual |
| `/api/v1/copilot/generate-script` | POST | GenAI | Assistente de negociação (WhatsApp, Call Center, E-mail) |
| `/api/v1/models` | GET | MLOps | Catálogo de modelos do Dynamic Model Registry |
| `/api/v1/models/promote` | POST | MLOps | Promoção atômica de modelo para Champion sem downtime |
| `/api/v1/models/shadow-metrics` | GET | MLOps | Telemetria de Shadow Scoring e divergência estatística |
| `/api/v1/admin/train/auto-retrain` | POST | Continuous Training | Disparo assíncrono do pipeline de retreino com Quality Gate |
| `/api/v1/admin/train/jobs` | GET | Continuous Training | Histórico e auditoria de execuções de retreinamento |
| `/api/v1/analytics/executive-report/download` | GET | Relatórios | Download do Dossiê Executivo C-Level (HTML/PDF print-ready) |
| `/api/v1/metrics/drift` | GET | Observabilidade | Relatório em cache de Data Drift com Evidently AI |

---

## 📐 Blueprint de Escala Global (Fase 2)

Para organizações com milhões de eventos por segundo e requisitos de multi-tenancy, o playbook arquitetural completo está documentado em:
👉 **[`specs/12_global_scaleup_architecture.md`](specs/12_global_scaleup_architecture.md)**

Pilares detalhados:
1. **Streaming & Ingestão:** Apache Kafka + Apache Flink para cálculo de features em tempo real.
2. **Feature Store:** Feast + Redis Online Store com consistência temporal point-in-time.
3. **Segurança & Governança:** OIDC / Keycloak, Row-Level Security (Multi-Tenancy) e conformidade LGPD/GDPR.
4. **Cloud-Native Kubernetes:** HPA / KEDA por fila e Service Mesh Istio com mTLS.
5. **AI Safety & Guardrails:** NeMo Guardrails para proteção contra alucinações e vazamento de PII no Copilot.

---

Desenvolvido por **Henrique Botelho Gomes** — Engenheiro de Software Sênior & Especialista em IA.
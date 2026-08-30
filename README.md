# 📉 RetainIQ — SaaS de Inteligência de Retenção de Clientes (Telco Churn)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-19.2+-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6?style=flat&logo=typescript&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-F37626?style=flat&logo=xgboost&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-Fast_Dependency_Manager-purple)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

> **De Modelo Preditivo a SaaS Global:** Uma solução completa de Machine Learning orientada a produto, com Engenharia de Software robusta, MLOps e interface executiva de alto nível.

Este projeto transforma o problema de retenção de clientes em Telecom em uma plataforma completa de SaaS e MLOps (**RetainIQ**), demonstrando **serviço em produção, observabilidade de drift, explicabilidade XAI (SHAP), simulador prescritivo What-If e interface moderna SPA em React + TypeScript**.

---

## 🌟 Destaques Arquiteturais & de Engenharia

1. **Frontend SPA Moderno (Zero-Streamlit):** Interface de alta fidelidade desenvolvida em **React 19 + TypeScript + Vite + Tailwind CSS + Radix UI / shadcn**, com:
   - **Dashboard Executivo:** KPIs de MRR em risco, clientes em alto risco e gráficos de distribuição.
   - **Risk Queue (TanStack Table):** Tabela virtualizada com busca, filtros semânticos por nível de risco e ordenação.
   - **Customer 360 & Simulador What-If:** Explicabilidade via TreeSHAP divergente e simulação interativa em tempo real com projeção de ROI anual.
   - **MLOps Cockpit:** Monitor de saúde do modelo, detecção de Data Drift (Evidently) e metadados de versão.
2. **Padrão Adapter na API (FastAPI):** Recebe requisições 100% em **Português** e traduz em milissegundos para o formato canônico em Inglês exigido pelo pipeline de inferência.
3. **Pipeline Anti-Leakage:** Pré-processamento matematicamente integrado no `Pipeline` do scikit-learn junto ao XGBoost.
4. **Data Contracts & Batch Dual (Pandera):** Endpoint `/api/v1/predict/batch` suportando JSON PT-BR ou upload de CSV EN-US, isolando linhas inválidas com relatório detalhado.
5. **Observabilidade Fora do Caminho Crítico:** Ring buffer de telemetria em memória; cálculo de Data Drift (Evidently AI) executado sob demanda e servido de cache; métricas Prometheus em `/metrics`.
6. **Docker Multi-Stage & Segurança:** Container unificado com build do frontend (Node 22) e runtime Python 3.12 (uv) sob usuário não-root.

---

## 📊 Performance do Modelo

Avaliação no conjunto de teste (20% dos dados invisíveis ao modelo):
- **ROC-AUC Score:** `0.82`
- **F1-Score (Churn):** `0.59`
- **Recall (Churn):** `0.67` 🎯 *(Métrica de negócio priorizada para minimizar perda de clientes)*

---

## 🚀 Como Executar

### Opção 1: Via Docker (Aplicação Completa — API + Frontend)
```bash
# 1. Construa a imagem multi-stage
docker build -t telco-churn-app .

# 2. Execute o container na porta 8000
docker run -p 8000:8000 telco-churn-app
```
Acesse a aplicação no navegador em:
- **Cockpit Frontend:** 👉 http://localhost:8000/
- **API Docs (Swagger UI):** 👉 http://localhost:8000/docs
- **Healthcheck:** 👉 http://localhost:8000/health
- **Métricas Prometheus:** 👉 http://localhost:8000/metrics

---

### Opção 2: Desenvolvimento Local

```bash
# 1. Instale dependências Python e Frontend
make install
make frontend-install

# 2. Execute todos os testes automatizados (Backend Pytest + Frontend Vitest)
make test-all

# 3. Inicie o Backend FastAPI (porta 8000)
make api

# 4. Em outro terminal, inicie o Frontend Vite (porta 5173 com proxy reverso)
make frontend-dev
```

---

## 🌐 Endpoints da API (`/api/v1`)

| Endpoint | Método | Descrição |
|---|---|---|
| `/health` | GET | Liveness probe para Docker/K8s (`{"status": "ok"}`) |
| `/metrics` | GET | Métricas padrão Prometheus (`http_*`, `churn_predictions_total`, etc.) |
| `/api/v1/predict` | POST | Predição individual com SHAP Top 3 e recomendação de playbook |
| `/api/v1/predict/batch` | POST | Predição em lote via JSON PT-BR ou upload de arquivo CSV |
| `/api/v1/simulate` | POST | Simulador *What-If* com cálculo de redução de risco e ROI anual |
| `/api/v1/metrics/drift` | GET | Leitura em cache do relatório de Data Drift (Evidently) |
| `/api/v1/admin/drift/refresh` | POST | Recálculo sob demanda do relatório de drift |
| `/api/v1/model/info` | GET | Metadados do modelo (`model_metadata.json`, métricas, git sha) |

---

## 📂 Estrutura do Projeto

```
.
├── .github/workflows/       # CI Pipeline (Backend lint/types/tests + Frontend tests/build)
├── data/
│   └── raw/                 # Dataset canônico (WA_Fn-UseC_-Telco-Customer-Churn.csv)
├── frontend/                # SPA React 19 + TypeScript + Vite + Tailwind + Radix/TanStack
│   ├── src/
│   │   ├── api/             # Client HTTP e queries TanStack
│   │   ├── components/      # UI components, Dashboard, Customer 360, Charts, MLOps
│   │   ├── pages/           # DashboardPage, CustomersPage, MlopsPage
│   │   └── types/           # Schemas e tipagens TypeScript
│   ├── package.json
│   └── vite.config.ts
├── models/
│   ├── churn_model_pipeline.joblib  # Pipeline treinado (scikit-learn + XGBoost)
│   └── model_metadata.json          # Metadados e métricas gerados no treino
├── specs/                   # Especificações técnicas e funcionais detalhadas (00 a 11)
├── src/
│   └── churn_prediction/
│       ├── api/             # FastAPI, telemetry (Prometheus), schemas Pydantic V2
│       ├── data/            # Preprocessamento anti-leakage e contratos Pandera
│       ├── models/          # Treino, avaliação, explainability (TreeSHAP), simulator e drift
│       └── config.py        # Configurações centralizadas e thresholds de risco
├── tests/                   # Suíte de testes Pytest (54 testes, cobertura >= 80%)
├── Dockerfile               # Build multi-stage (Node 22 + Python 3.12 slim)
├── Makefile                 # Automação de tarefas (testes, lint, dev, build)
├── PRD.md                   # Product Requirement Document mestre
└── pyproject.toml           # Gerenciamento uv, Ruff, Mypy e Pytest-cov
```

---

Desenvolvido por Henrique Botelho Gomes - Engenheiro de Software Sênior & Especialista em IA.
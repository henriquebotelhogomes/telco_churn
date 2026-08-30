# 📄 Product Requirement Document (PRD) — RetainIQ

> **De Modelo Preditivo a SaaS Global de Retenção de Clientes & MLOps**  
> **Versão:** 2.1.0 | **Status:** Aprovado para Execução Autônoma | **Padrão:** Startup Global / Big Tech  
> **Guia para Implementação:** Este documento contém todas as especificações técnicas, schemas de dados, assinaturas de funções e árvores de arquivos para que **qualquer LLM ou Agente de IA** execute as melhorias de ponta a ponta sem ambiguidades.

---

## 1. Diretrizes Absolutas e Restrições de Engenharia

> [!CRITICAL]
> **REGRAS MANDATÓRIAS PARA QUALQUER LLM EXECUTANDO ESTE PRD:**
> 1. **FRONTEND ZERO-STREAMLIT:** É estritamente **PROIBIDO** o uso de Streamlit, Gradio ou qualquer framework de prototipação rápida em Python. O frontend DEVE ser implementado exclusivamente em **React 18+ com TypeScript** com **Vite** (SPA — decisão fechada, sem Next.js no MVP), **Tailwind CSS**, **shadcn/ui / Radix UI**, **TanStack Query / Table** e **Recharts / Visx**.
> 2. **ANTI-DATA LEAKAGE:** Todas as transformações matemáticas de dados em inferência DEVEM utilizar exclusivamente o `Pipeline` do Scikit-Learn já treinado (`get_preprocessing_pipeline()`). Nenhuma transformação ad-hoc solta fora do pipeline é permitida.
> 3. **TIPAGEM ESTÁTICA & CONTRATOS:** Backend com **Pydantic V2** e **Mypy**; Frontend com **TypeScript Strict Mode**; Validação de DataFrames com **Pandera**.
> 4. **TOOLING PYTHON:** Todas as dependências devem ser gerenciadas via `uv` e declaradas em `pyproject.toml`.
> 5. **API VERSIONADA:** Todas as rotas de negócio vivem sob o prefixo **`/api/v1`** (breaking change em relação à `/predict` atual). `README.md`, healthcheck do Docker e Frontend são atualizados no mesmo PR. `GET /health` permanece na raiz como liveness probe.
> 6. **OBSERVABILIDADE FORA DO CAMINHO CRÍTICO:** A geração do relatório de drift (Evidently) NUNCA ocorre dentro do fluxo de inferência. Inputs de produção são acumulados em um *ring buffer* em memória; o relatório é calculado sob demanda (endpoint de refresh) e servido de cache.
> 7. **SEGURANÇA MÍNIMA:** `CORSMiddleware` com origens configuráveis via env (`CORS_ORIGINS`) desde o primeiro PR do frontend. Autenticação por `X-API-Key` implementada como dependency opcional, ativada por env (`API_KEY_ENABLED`).

---

## 2. Visão Geral da Arquitetura do Sistema

```
+---------------------------------------------------------------------------------------------------+
|                                      RETAINIQ FRONTEND (REACT + TS)                               |
|   - Executive Dashboard (MRR at Risk)               - Interactive What-If Simulator (Real-time)   |
|   - Virtualized Customer Risk Queue (TanStack)      - SHAP Waterfall Feature Importance           |
|   - Model Health & Data Drift Monitor               - Next Best Action Retention Triggers         |
+---------------------------------------------------------------------------------------------------+
                                                  │  HTTPS / JSON / Multipart
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                     FASTAPI GATEWAY & SERVING ENGINE                              |
|   - Pydantic V2 Adapter (PT-BR -> EN-US)            - Prometheus Metrics (/metrics)               |
|   - Pandera Schema Contracts (Batch Validation)     - Structured JSON Logging & Tracing           |
|   - CORS via env (CORS_ORIGINS) + X-API-Key opt.    - Ring Buffer de inputs p/ Drift              |
+---------------------------------------------------------------------------------------------------+
             │                                   │                                  │
             ▼                                   ▼                                  ▼
+-------------------------+         +-------------------------+        +----------------------------+
|   REAL-TIME INFERENCE   |         |    EXPLAINABILITY (XAI) |        |    MLOPS & DRIFT MONITOR   |
| - Scikit-Learn Pipeline |         | - TreeSHAP Calculator   |        | - Evidently AI Data Drift  |
| - XGBoost Model         |         | - Local Driver Mapping  |        | - Cache de drift (TTL)     |
+-------------------------+         +-------------------------+        +----------------------------+
```

> **Nota (v2.1) — MVP 100% stateless:** Dashboard e Risk Queue são calculados sobre a base carregada via `/api/v1/predict/batch` (7.032 clientes). Persistência (Postgres, histórico de playbooks e churn real) é o **Marco M6 (opcional)** — é ela que habilita as métricas "Evolução Temporal" e "Eficiência de Retenção" reais.

---

## 3. Mapeamento de Arquivos do Projeto (Árvore Alvo)

Qualquer LLM implementando este PRD deve criar/modificar os arquivos seguindo rigorosamente a estrutura abaixo:

```
telco_churn/
├── .github/workflows/
│   └── ci.yml                         # CI/CD: lint (Ruff), types (Mypy), tests (Pytest), front build
├── data/
│   └── raw/
│       └── WA_Fn-UseC_-Telco-Customer-Churn.csv
├── models/
│   ├── churn_model_pipeline.joblib    # [OK] caminho real já usado pelo config.py
│   └── model_metadata.json            # [NOVO] versão, data de treino, ROC-AUC/Recall, git sha
├── frontend/                          # [NOVO] Aplicação React SPA com Vite
│   ├── src/
│   │   ├── api/                       # API Client (Axios/Fetch + TanStack Query hooks)
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components (Button, Card, Badge, Dialog, etc.)
│   │   │   ├── charts/                # Recharts / Visx (SHAP Waterfall, MRR Evolution)
│   │   │   ├── dashboard/             # StatCards, Executive View
│   │   │   ├── customers/             # RiskQueueTable (TanStack Table), CustomerDetailModal
│   │   │   ├── simulator/             # WhatIfSimulator, Sliders, Delta Badge
│   │   │   └── mlobs/                 # DriftCards, ModelMetricsView
│   │   ├── types/                     # Interfaces TypeScript geradas/espelhadas da API
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
├── src/
│   └── churn_prediction/
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py                # [MODIFICAR] Rotas /api/v1/predict, batch, simulate, drift e model/info
│       │   ├── schemas.py             # [MODIFICAR] Pydantic Schemas enriquecidos com SHAP e Batch
│       │   ├── telemetry.py           # [NOVO] Métricas Prometheus e Structured JSON Logging
│       │   └── routes/                # [OPCIONAL/RECOMENDADO] Modularização de rotas
│       ├── data/
│       │   ├── __init__.py
│       │   ├── contracts.py           # [NOVO] Schemas Pandera para Data Quality e Batch
│       │   └── preprocess.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── explainability.py      # [NOVO] TreeSHAP Explainer e tradutor de features
│       │   ├── simulator.py           # [NOVO] Motor What-If e Next Best Action Heuristics
│       │   ├── drift.py               # [NOVO] Detector de Data Drift via Evidently AI
│       │   ├── train.py
│       │   └── evaluate.py
│       └── config.py                  # [MODIFICAR] Novas configurações (limiares de drift, SHAP)
├── tests/
│   ├── conftest.py                    # [NOVO] Fixtures compartilhadas (app, payload válido, base reduzida)
│   ├── test_api.py                    # [MODIFICAR] Testes das rotas /api/v1 (predict, batch, simulate, drift, model/info)
│   ├── test_explainability.py         # [NOVO] Testes de cálculo de SHAP e conversão de impacto
│   ├── test_contracts.py              # [NOVO] Testes de validação Pandera
│   ├── test_simulator.py              # [NOVO] Testes do motor What-If e ROI
│   └── test_drift.py                  # [NOVO] Testes do detector de drift e do cache
├── Dockerfile                         # [MODIFICAR] Multi-stage build suportando API e build de assets
├── Makefile                           # [MODIFICAR] Comandos de dev, test, frontend, build
├── pyproject.toml                     # [MODIFICAR] Novas dependências: shap, pandera, evidently, prometheus-fastapi-instrumentator
└── PRD.md                             # Este documento mestre
```

#### Correções obrigatórias em arquivos existentes (Marco M0)
* Renomear `src/churn_prediction/__ini__.py` e `src/churn_prediction/models/__ini__.py` → `__init__.py` (typo atual; hoje só funciona via *namespace packages*, o que fragiliza a descoberta de pacotes no build e nas ferramentas).
* Sincronizar `README.md` (rotas `/api/v1`, caminhos reais `data/raw/` e `models/churn_model_pipeline.joblib`) e o `Dockerfile` (healthcheck apontando para `/health`).
* Adicionar `pytest-cov` ao CI com gate de cobertura ≥ 80%.

---

## 4. Especificações Técnicas de Backend & MLOps

### 4.1 Dependências Python a Adicionar
```toml
# Adicionar em pyproject.toml:
dependencies = [
    "fastapi>=0.110.0",
    "joblib>=1.3.2",
    "pandas>=2.2.1",
    "pydantic-settings>=2.2.1",
    "pydantic>=2.6.3",
    "scikit-learn>=1.4.1.post1",
    "uvicorn>=0.27.1",
    "xgboost>=2.0.3",
    "shap>=0.44.1",                              # Explainable AI
    "pandera[pandas]>=0.18.3",                   # Data Contracts & Quality
    "evidently>=0.4.19",                         # Data & Concept Drift
    "prometheus-fastapi-instrumentator>=7.0.0",  # Observabilidade Prometheus
    "python-multipart>=0.0.9",                   # Upload de arquivos batch
]

# Em [dependency-groups].dev, adicionar:
#   "pytest-cov>=5.0.0"  # Cobertura com gate >= 80% no CI
#   "httpx>=0.27.0"      # Requisito do TestClient do Starlette/FastAPI
```

---

### 4.2 Módulo de Explicabilidade (`src/churn_prediction/models/explainability.py`)

#### Responsabilidade:
Calcular os SHAP values locais em milissegundos para qualquer inferência e traduzir as features técnicas para termos amigáveis de negócio.

#### Assinatura e Lógica:
```python
import shap
import pandas as pd
from typing import List, Dict, Any

class ChurnExplainer:
    def __init__(self, pipeline):
        """
        Extrai o pré-processador do scikit-learn e o modelo XGBoost.
        Instancia o shap.TreeExplainer sobre o modelo já ajustado.
        """
        self.preprocessor = pipeline.named_steps["preprocessing"]
        self.model = pipeline.named_steps["classifier"]
        self.explainer = shap.TreeExplainer(self.model)
        
    def explain_instance(self, raw_input_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        1. Transforma raw_input_df usando self.preprocessor.transform(raw_input_df).
        2. Executa self.explainer.shap_values(transformed_features).
        3. Obtém os feature_names transformados (OneHot + Numerical).
        4. Ordena por magnitude de impacto absoluto (|SHAP value|).
        5. Retorna Top 3 a 5 fatores com: feature, impact, direction ("increases_risk" | "reduces_risk")
           e human_explanation traduzida.
        """
        pass
```

#### Algoritmo de conversão SHAP → impacto (%) (definição fechada, v2.1)
O `TreeExplainer` roda em `model_output="raw"` (log-odds). Para o `impacto` em % exibido no front:
1. Ordene os SHAP values por |φ| decrescente.
2. Compute probabilidades acumuladas: `p_k = σ(f0 + Σ_{j≤k} φ_j)`, com `p_0 = σ(f0)` (base value).
3. `impacto_i = (p_i − p_{i−1}) / p_final` — fração da probabilidade final explicada pela feature i, expressa em % com sinal.
4. `direcao`: `aumenta_risco` se φ_i > 0, senão `reduz_risco`.
5. A resposta também inclui `shap_value` (log-odds bruto) para auditoria/debug.

#### Dicionário de Tradução de Features:
* `Contract_Month-to-month` -> `"Contrato mês a mês sem fidelidade"` (+Risco)
* `InternetService_Fiber optic` -> `"Uso de fibra ótica sem serviços de suporte"` (+Risco)
* `PaymentMethod_Electronic check` -> `"Pagamento via cheque eletrônico manual"` (+Risco)
* `tenure` -> `"Tempo de permanência na empresa"` (-Risco se alto)
* `OnlineSecurity_No` -> `"Ausência de segurança online ativa"` (+Risco)
* `TechSupport_No` -> `"Ausência de suporte técnico contratado"` (+Risco)

#### Níveis de Risco Semânticos (thresholds fechados, v2.1)
Centralizados em `config.py` (`RISK_THRESHOLDS`), nunca hard-coded na API:
* `Baixo`: p < 0.30
* `Médio`: 0.30 ≤ p < 0.60
* `Alto`: 0.60 ≤ p < 0.80
* `Crítico`: p ≥ 0.80

#### Regra de `acao_recomendada` (determinística, v2.1)
No `POST /api/v1/predict`, o servidor simula internamente as 4 ações do simulador (4.4) e recomenda a de **maior redução absoluta de probabilidade** (`delta_risk` mais negativo). Tie-break pela ordem: Fidelização > Cross-sell de Proteção > Automatização de Pagamento > Desconto. Custo: 4 inferências extras por request (~ms no XGBoost) — aceitável.

---

### 4.3 Módulo de Contratos de Dados & Validação Batch (`src/churn_prediction/data/contracts.py`)

#### Schema Pandera para Ingestão:
```python
import pandera as pa
from pandera.typing import Series

class CustomerDataContract(pa.DataFrameModel):
    gender: Series[str] = pa.Field(isin=["Male", "Female"])
    SeniorCitizen: Series[int] = pa.Field(isin=[0, 1])
    Partner: Series[str] = pa.Field(isin=["Yes", "No"])
    Dependents: Series[str] = pa.Field(isin=["Yes", "No"])
    tenure: Series[int] = pa.Field(ge=0, le=120)
    PhoneService: Series[str] = pa.Field(isin=["Yes", "No"])
    MultipleLines: Series[str] = pa.Field(isin=["Yes", "No", "No phone service"])
    InternetService: Series[str] = pa.Field(isin=["DSL", "Fiber optic", "No"])
    OnlineSecurity: Series[str] = pa.Field(isin=["Yes", "No", "No internet service"])
    OnlineBackup: Series[str] = pa.Field(isin=["Yes", "No", "No internet service"])
    DeviceProtection: Series[str] = pa.Field(isin=["Yes", "No", "No internet service"])
    TechSupport: Series[str] = pa.Field(isin=["Yes", "No", "No internet service"])
    StreamingTV: Series[str] = pa.Field(isin=["Yes", "No", "No internet service"])
    StreamingMovies: Series[str] = pa.Field(isin=["Yes", "No", "No internet service"])
    Contract: Series[str] = pa.Field(isin=["Month-to-month", "One year", "Two year"])
    PaperlessBilling: Series[str] = pa.Field(isin=["Yes", "No"])
    PaymentMethod: Series[str] = pa.Field(isin=[
        "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
    ])
    MonthlyCharges: Series[float] = pa.Field(ge=0.0)
    TotalCharges: Series[str] = pa.Field(nullable=True)

    class Config:
        strict = False
        coerce = True
```

> **Contrato de ingestão (v2.1):**
> * **JSON em lote** (`POST /api/v1/predict/batch` com `Content-Type: application/json`): payload em **PT-BR**, reutilizando o `PrevisaoChurnRequest` + o Adapter existente; Pandera valida o DataFrame **após** a conversão para EN-US.
> * **CSV em lote** (multipart upload): arquivo no **formato cru EN-US do dataset original** (mesmas colunas do CSV de treino, incluindo `TotalCharges` como string); Pandera valida **antes** da inferência. Linhas inválidas são rejeitadas com relatório de erro por linha (índice + motivo), sem derrubar o lote inteiro.

---

### 4.4 Módulo de Prescrição & Simulador What-If (`src/churn_prediction/models/simulator.py`)

#### Lógica:
Permite avaliar o impacto de ações comerciais no score do cliente.
* **Ação 1: Fidelização:** Altera `Contract` para `"One year"` ou `"Two year"`.
* **Ação 2: Desconto:** Reduz `MonthlyCharges` em $X\%$.
* **Ação 3: Cross-sell de Proteção:** Ativa `TechSupport = "Yes"` e `OnlineSecurity = "Yes"`.
* **Ação 4: Automatização de Pagamento:** Altera `PaymentMethod` para `"Credit card (automatic)"`.

O endpoint `/api/v1/simulate` recalcula o score com as alterações propostas e retorna:
* `original_probability`: float
* `simulated_probability`: float
* `delta_risk`: float (ex: `-0.35` indicando redução de 35% no risco)
* `roi_expected_annual_savings`: float (`MonthlyCharges * 12 * delta_risk`)

---

### 4.5 Módulo de Observabilidade & Data Drift (`src/churn_prediction/models/drift.py`)

#### Implementação com Evidently AI:
```python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
import pandas as pd

def generate_drift_report(reference_data: pd.DataFrame, current_data: pd.DataFrame) -> dict:
    """
    Compara o dataset de treino (reference) com os dados recebidos em produção (current).
    Retorna o status geral de drift, número de features com drift e o PSI por feature.
    """
    report = Report(metrics=[DataDriftPreset(), DataQualityPreset()])
    report.run(reference_data=reference_data, current_data=current_data)
    return report.as_dict()
```

> **Execução fora do caminho crítico (v2.1):**
> * `telemetry.py` mantém um **ring buffer** (`deque`, `maxlen` configurável, default 5.000) com os inputs EN-US já validados de cada inferência.
> * `POST /api/v1/admin/drift/refresh` roda o relatório Evidently (buffer vs. baseline de treino) e publica o resultado em cache com TTL configurável. `GET /api/v1/metrics/drift` apenas lê o cache.
> * Em deployments multi-worker o buffer é por processo — aceitável no MVP (1 worker no Render); no M6, substituir por armazenamento compartilhado.

---

### 4.6 Especificação Completa dos Endpoints FastAPI

> [!IMPORTANT]
> **v2.1 — Breaking change controlado:** as rotas de negócio passam a viver sob `/api/v1` (por exemplo, `/api/v1/predict`). A rota antiga `/predict` é removida; `README.md`, healthcheck do Docker e frontend são atualizados no mesmo PR. `GET /health` permanece na raiz como liveness probe.

#### 1. `POST /api/v1/predict`
* **Descrição:** Inferência individual em tempo real com probabilidade, nível de risco semântico e Top 3 SHAP Drivers.
* **Request:** Schema `PrevisaoChurnRequest` (compatível com os campos em português atuais).
* **Response:**
```json
{
  "previsao_cancelamento": 1,
  "probabilidade_cancelamento": 0.84,
  "nivel_risco": "Crítico",
  "mrr_em_risco": 89.50,
  "top_fatores_risco": [
    {
      "fator": "Tipo de Contrato",
      "impacto": "+28%",
      "shap_value": 0.83,
      "direcao": "aumenta_risco",
      "descricao": "Contrato mês a mês sem fidelidade"
    },
    {
      "fator": "Serviço de Internet",
      "impacto": "+21%",
      "direcao": "aumenta_risco",
      "descricao": "Fibra óptica sem suporte técnico contratado"
    }
  ],
  "acao_recomendada": {
    "playbook": "MIGRAÇÃO_CONTRATO_ANUAL",
    "descricao": "Oferecer 15% de desconto no plano anual com inclusão de Suporte Técnico.",
    "reducao_estimada_risco": 0.35
  }
}
```

#### 2. `POST /api/v1/predict/batch`
* **Descrição:** Inferência em lote para múltiplos clientes, com **dupla ingestão**: payload JSON PT-BR (Adapter) ou upload de `.csv` EN-US cru (Pandera).
* **Processamento:** Validação com Pandera -> Processamento Vetorizado -> Retorno com lista de previsões e resumo executivo.
* **Response (resumo):** `{ "results": [...], "resumo": { "total_analisado", "total_em_risco", "mrr_total_em_risco", "distribuicao_risco": {"baixo", "medio", "alto", "critico"} }, "linhas_invalidas": [ {"indice", "motivo"} ] }`. O resumo alimenta os KPIs do Dashboard.

#### 3. `POST /api/v1/simulate`
* **Descrição:** Simulação *What-If* interativa. Recebe o estado atual do cliente + alterações desejadas e retorna o delta de probabilidade e economia financeira estimada.

#### 4. `GET /api/v1/metrics/drift`
* **Descrição:** Retorna o status de drift das variáveis em produção contra o dataset baseline (resultado servido de cache; recálculo apenas via `/api/v1/admin/drift/refresh`).

#### 5. `GET /metrics`
* **Descrição:** Endpoint padrão do Prometheus com métricas `http_request_duration_seconds`, `http_requests_total` e `churn_predictions_total`.

#### 6. `GET /api/v1/model/info`
* **Descrição:** Lê `models/model_metadata.json` (gerado no treino) e retorna versão, data de treino, ROC-AUC/Recall e hash do artefato. Alimenta a tela `/mlobs`.

#### 7. `POST /api/v1/admin/drift/refresh`
* **Descrição:** Executa o relatório Evidently (ring buffer vs. baseline de treino) e atualiza o cache servido por `GET /api/v1/metrics/drift`. Protegido por `X-API-Key` quando ativado.

---

## 5. Especificação Técnica do Frontend (React + TypeScript)

> [!IMPORTANT]
> A LLM deve criar a pasta `frontend/` na raiz do projeto com um setup moderno usando **Vite + React 18/19 + TypeScript + Tailwind CSS**.
> **v2.1:** A base da API vem de `VITE_API_BASE_URL` (env), consumindo as rotas `/api/v1/*` (CORS já configurado no backend). Testes de componentes com **Vitest + Testing Library** (smoke E2E com Playwright é opcional); hooks testados com `msw` ou mock do client.

### 5.1 Telas e Componentes Mandatórios

#### 1. Dashboard Executivo (`/`)
* **Hero Metrics (StatCards):**
  * *Receita em Risco (MRR):* Ex: `R$ 48.520,00` (indicador de tendência entra no **M6**, quando houver histórico).
  * *Clientes em Alto Risco:* Ex: `312 clientes` (taxa de churn projetada de `26.4%`).
  * *Eficiência de Retenção:* Taxa de sucesso de playbooks aplicados. **[M6 — oculto no MVP: requer histórico persistido]**
* **Gráfico Principal:** **[MVP]** Distribuição de MRR e contagem de clientes por nível de risco (Recharts `BarChart`), derivados do resumo executivo do `/api/v1/predict/batch`. A "Evolução Temporal de Churn vs. Retenção" (Recharts `AreaChart`) entra somente no **M6**.

> **Definições de KPI (MVP):** `MRR em Risco = Σ (MonthlyCharges × p(churn))` dos clientes com nível Alto/Crítico; `Clientes em Alto Risco` = contagem com p ≥ 0.60. KPIs são calculados no backend (resumo do batch) e apenas renderizados no front.
* **Distribuição de Risco:** Gráfico de Rosca / Donut (Baixo, Médio, Alto, Crítico).

#### 2. Fila Priorizada de Clientes / Risk Queue (`/customers`)
* **Tabela Virtualizada (TanStack Table):**
  * Colunas: `Cliente ID`, `Gênero`, `Tempo de Casa (meses)`, `Contrato`, `Cobrança Mensal (MRR)`, `Score de Churn (Badge com cores semânticas)`, `Principal Driver SHAP`, `Ações`.
  * Filtros por nível de risco, tipo de contrato e busca por ID.
  * Botão de clique para abrir o **Customer 360 Drawer/Modal**.

#### 3. Customer 360 & Simulador What-If (Modal ou Tela `/customers/:id`)
* **Visualizador de Score (RiskGauge):** Gráfico semicircular animado com a probabilidade atual.
* **SHAP Waterfall Divergente:** Gráfico de barras horizontais mostrando fatores que aumentam o risco em vermelho e fatores que reduzem o risco em verde.
* **Painel Interativo de Simulação What-If:**
  * Select interativo para mudar Contrato (Mensal -> Anual).
  * Slider de Desconto de Mensalidade (0% a 30%).
  * Toggles para Ativar Suporte Técnico e Segurança Online.
  * **Badge Dinâmico de Impacto:** Recálculo em tempo real (ex: *"Novo Risco: 42% (Redução de 42%) — Economia Anual Projetada: R$ 1.074,00"*).
  * Botão de ação: *"Aplicar Playbook de Retenção"*.

#### 4. Monitor de Saúde do Modelo / MLOps (`/mlobs`)
* Cards de Data Drift por variável (PSI score com alerta verde/vermelho).
* Histórico de versão do modelo em produção (`XGBoost v1.0.0 - Recall: 0.67 | ROC-AUC: 0.82`).
* Latência média da API (p95).

---

## 6. Roteiro Passo a Passo para Implementação por outra LLM

Qualquer LLM executando a implementação deve seguir estritamente esta ordem (marcos entre parênteses — ver Seção 8):

0. **Passo 0 — Higiene (M0):**
   Renomear os arquivos `__ini__.py` (typo) para `__init__.py`, adicionar `pytest-cov` ao CI e sincronizar README com os caminhos reais (`data/raw/`, `models/churn_model_pipeline.joblib`).

1. **Passo 1 — Dependências Backend:**  
   Atualizar `pyproject.toml` adicionando `shap`, `pandera`, `evidently`, `prometheus-fastapi-instrumentator`, `python-multipart`. Executar `uv sync` ou `pip install .`.
2. **Passo 2 — Motor de Explicabilidade:**  
   Criar `src/churn_prediction/models/explainability.py` implementando o cálculo de TreeSHAP e o dicionário de tradução semântica.
3. **Passo 3 — Contratos de Dados:**  
   Criar `src/churn_prediction/data/contracts.py` com o schema Pandera.
4. **Passo 4 — Simulador What-If:**  
   Criar `src/churn_prediction/models/simulator.py` com as regras de simulação e cálculo de ROI.
5. **Passo 5 — Observabilidade & Drift:**  
   Criar `src/churn_prediction/models/drift.py` e `src/churn_prediction/api/telemetry.py`.
6. **Passo 6 — Atualizar API FastAPI:**  
   Atualizar `src/churn_prediction/api/schemas.py` e `src/churn_prediction/api/main.py` com as rotas completas sob `/api/v1` (`/api/v1/predict`, `/api/v1/predict/batch`, `/api/v1/simulate`, `/api/v1/metrics/drift`, `/api/v1/model/info`, `/api/v1/admin/drift/refresh`), mantendo `GET /health` na raiz; adicionar `CORSMiddleware` (env `CORS_ORIGINS`) e `X-API-Key` opcional (env `API_KEY_ENABLED`). Atualizar `README.md` e healthcheck do Docker no mesmo PR.
7. **Passo 7 — Testes Unitários:**  
   Expandir `tests/` cobrindo SHAP, Pandera e todos os novos endpoints via Pytest.
8. **Passo 8 — Frontend React:**  
   Inicializar a aplicação na pasta `frontend/` com Vite + React + TypeScript + Tailwind + shadcn, conectando ao backend via env `VITE_API_BASE_URL` (rotas `/api/v1`). Incluir testes de componentes com Vitest + Testing Library.
9. **Passo 9 — Docker & CI/CD:**  
   Ajustar o `Dockerfile` (multi-stage: build do front + API servindo os assets) e `.github/workflows/ci.yml` (lint, mypy, pytest com cobertura ≥ 80%, build e testes do front). Publicar no Render com healthcheck em `/health`.

---

## 7. Critérios de Aceite (Definition of Done)

* [ ] `pytest tests/` executa com 100% de aprovação e cobertura >= 80% (medida com `pytest-cov`, gate no CI).
* [ ] Nenhum arquivo `__ini__.py` no repositório (typo corrigido para `__init__.py`).
* [ ] Rotas de negócio sob `/api/v1`; rota antiga `/predict` removida; README e healthcheck do Docker atualizados.
* [ ] `CORSMiddleware` configurado via env; `X-API-Key` opcional funcionando (401 quando ativado e header ausente).
* [ ] Rota `/api/v1/predict` retorna score + Top Drivers SHAP (impacto em % de probabilidade + `shap_value` bruto) em < 50ms.
* [ ] `nivel_risco` e `acao_recomendada` seguem as regras de 4.2 (thresholds centralizados em `config.py`; playbook = argmax determinístico das 4 ações).
* [ ] Rota `/api/v1/simulate` permite alterar parâmetros do cliente e ver o score atualizado instantaneamente.
* [ ] Rota `/api/v1/predict/batch` aceita JSON PT-BR (Adapter) e CSV EN-US cru (Pandera), retorna resumo executivo e relatório de linhas inválidas.
* [ ] `GET /api/v1/metrics/drift` serve resultado de cache; o relatório Evidently só roda via `/api/v1/admin/drift/refresh`.
* [ ] `models/model_metadata.json` gerado no treino e exposto em `GET /api/v1/model/info`.
* [ ] Frontend React (Vite) renderiza Dashboard, Tabela de Clientes, Gráficos SHAP e Simulador What-If com design premium e responsivo; testes de componentes (Vitest + Testing Library) verdes.
* [ ] Zero ocorrências de Streamlit no repositório.

---

## 8. Marcos de Entrega (Milestones) & Decisões de Arquitetura (v2.1)

### 8.1 Milestones — um PR por marco, nesta ordem
| Marco | Escopo | DoD resumido |
|---|---|---|
| **M0 — Higiene** | Fix `__ini__.py` → `__init__.py`; sync README/caminhos; `pytest-cov` no CI | CI verde reportando cobertura |
| **M1 — XAI & Prescrição** | `explainability.py`, thresholds de risco, `acao_recomendada`, rota `/api/v1/predict` | Testes de SHAP verdes; p95 < 50ms |
| **M2 — Batch & Simulador** | `contracts.py`, `/api/v1/predict/batch` (JSON+CSV), `simulator.py` + `/api/v1/simulate` | Testes de contratos e simulador verdes |
| **M3 — Observabilidade** | `telemetry.py` (Prometheus + ring buffer), `drift.py`, `/api/v1/metrics/drift` + refresh, `/api/v1/model/info` | Drift fora do request path; `/metrics` exposto |
| **M4 — Frontend** | SPA Vite (Dashboard, Risk Queue, Customer 360 + Simulador, MLObs), CORS, Vitest | Build + testes de front verdes |
| **M5 — Entrega** | Dockerfile multi-stage (front + API), CI completo, README v2 | Imagem publicada no Render com `/health` |
| **M6 — Persistência (opcional)** | Postgres/SQLite + repositório; histórico de playbooks e churn real | Métricas temporais e eficiência de retenção reais |

### 8.2 Decisões de Arquitetura (ADR resumido)
* **ADR-001 — MVP stateless:** KPIs do dashboard derivam da base carregada via batch (7.032 clientes); sem banco no MVP. O M6 reverte a decisão se histórico real for necessário. *(Motivo: escopo, custo, deploy single-container no Render.)*
* **ADR-002 — Impacto SHAP em % de probabilidade:** SHAP raw (log-odds) convertido incrementalmente (σ de soma parcial ordenada por |φ|); log-odds bruto também retornado. *(Motivo: interpretação de negócio sem "inventar" percentuais.)*
* **ADR-003 — Vite, não Next.js:** SPA pura consumindo API; sem necessidade de SSR/SEO no MVP. *(Motivo: simplicidade e build mais rápido.)*
* **ADR-004 — `/api/v1` como breaking change:** adotado de uma vez, com README/Docker/front atualizados no mesmo PR. *(Motivo: projeto pré-prod, sem consumidores externos.)*
* **ADR-005 — Drift sob demanda com cache:** relatório Evidently nunca no caminho de inferência. *(Motivo: latência e custo de CPU.)*

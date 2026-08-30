# 03 — Especificação Técnica de Alto Nível

> Define **como** o RetainIQ é construído em alto nível: stack, domínios,
> contratos e fluxo de dados. Detalhamento de topologia está em `04_architecture.md`.

---

## 1. Princípios de Engenharia

1. **Contracts-first** — APIs definidas por OpenAPI/JSON Schema antes do código.
2. **Domain-driven** — fronteiras claras entre domínios (Scoring, MLOps, Tenancy).
3. **Stateless services** — escalabilidade horizontal; estado em data stores.
4. **Immutable artifacts** — modelos e imagens versionados e imutáveis.
5. **Everything as code** — infra, pipelines, qualidade e observabilidade.
6. **Secure & observable by default** — não são "add-ons" pós-MVP.
7. **Evoluir o que já existe** — o pipeline scikit-learn + XGBoost + FastAPI
   atual é o núcleo do *Inference Service*, não é descartado.

---

## 2. Visão de Stack

### 2.1 Backend / ML
| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Linguagem | Python 3.12 | Já adotado; ecossistema ML maduro |
| API | FastAPI + Pydantic V2 | Já adotado; performance e tipagem |
| Servidor | Uvicorn/Gunicorn | ASGI, workers |
| ML | scikit-learn Pipeline + XGBoost | Reuso do modelo já treinado |
| Explicabilidade | SHAP | Padrão de mercado para drivers |
| Tarefas async | Celery / RQ + Redis (ou Arq) | Scoring em lote, re-treino |
| Tracking ML | MLflow | Registro de modelos e métricas |
| Validação de dados | Pandera / Great Expectations | Qualidade de entrada e drift |

### 2.2 Dados
| Uso | Tecnologia |
|-----|-----------|
| Operacional (tenants, ações, usuários) | PostgreSQL |
| Cache / fila | Redis |
| Object storage (datasets, artefatos) | S3 / MinIO |
| Analytics (opcional V1+) | DuckDB / warehouse do cliente |
| Feature store (V1+) | Feast (sobre Postgres/Redis) |

### 2.3 Frontend
| Camada | Tecnologia |
|--------|-----------|
| Framework | React 18 + TypeScript |
| Build/SSR | Next.js (App Router) |
| Estado servidor | TanStack Query |
| UI / Design System | Tailwind CSS + Radix UI + shadcn/ui |
| Dataviz | Visx / Recharts / D3 (casos complexos) |
| Testes | Vitest + Testing Library + Playwright |

> Detalhes em `09_frontend_ux.md`.

### 2.4 Plataforma
| Área | Tecnologia |
|------|-----------|
| Container | Docker (multi-stage, non-root — já existente) |
| Orquestração | Kubernetes (k3d/kind local) |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Gateway/Ingress | NGINX / Traefik |
| Observabilidade | OpenTelemetry, Prometheus, Grafana, Loki, Tempo |

---

## 3. Domínios e Serviços (bounded contexts)

| Serviço | Responsabilidade | Notas |
|---------|------------------|-------|
| **API Gateway / BFF** | Autenticação, roteamento, agregação para o front | Backend-for-Frontend |
| **Inference Service** | Scoring individual e explicabilidade | Evolução do `api/main.py` atual |
| **Batch Scoring Worker** | Scoring em lote assíncrono | Consome filas |
| **MLOps Service** | Registro, drift, re-treino, promoção de modelos | MLflow + scheduler |
| **Tenant & Identity** | Tenants, usuários, RBAC, auditoria | Postgres |
| **Action/Playbook Service** | Recomendação e registro de ações | Fecha o loop |
| **Ingestion Service** | Conectores e validação de dados | Pandera/GE |

> No MVP, vários domínios podem coabitar um **monólito modular** bem fronteirado,
> extraível em serviços conforme a escala (ver `ADR-03`).

---

## 4. Contratos de API (alto nível)

> Versionamento via path (`/api/v1`). Todos os endpoints retornam erros no
> formato **RFC 7807 (Problem Details)** e exigem `tenant` no token.

| Método | Rota | Descrição | RF |
|--------|------|-----------|-----|
| `POST` | `/api/v1/predictions` | Scoring individual + drivers | RF-10, RF-20 |
| `POST` | `/api/v1/predictions/batch` | Cria job de scoring em lote | RF-11 |
| `GET` | `/api/v1/predictions/batch/{jobId}` | Status/resultado do job | RF-11 |
| `GET` | `/api/v1/customers?sort=risk_value` | Fila priorizada | RF-30 |
| `GET` | `/api/v1/customers/{id}` | Detalhe + score + drivers | RF-20 |
| `POST` | `/api/v1/customers/{id}/simulate` | What-if | RF-50 |
| `POST` | `/api/v1/actions` | Registrar ação/resultado | RF-41 |
| `GET` | `/api/v1/models` | Registro de modelos e métricas | RF-72 |
| `GET` | `/api/v1/models/drift` | Status de drift | RF-70 |
| `GET` | `/health` `/ready` | Liveness/Readiness probes | — |
| `GET` | `/metrics` | Métricas Prometheus | — |

**Exemplo de resposta de predição (ilustrativo):**

```jsonc
{
  "customer_id": "c_123",
  "churn_probability": 0.78,
  "risk_class": "Alto",
  "model_version": "xgb-2024.11.0",
  "scored_at": "2026-06-22T12:00:00Z",
  "drivers": [
    { "feature": "Contrato mensal", "impact": 0.21, "direction": "increases" },
    { "feature": "Tempo de permanência baixo", "impact": 0.14, "direction": "increases" }
  ],
  "trace_id": "f1a2b3c4..."
}
```

> Mantém-se o **padrão Adapter PT↔EN** já existente, agora generalizado por
> *locale* e desacoplado do schema do modelo.

---

## 5. Fluxo de Dados (end-to-end)

```
Fonte de dados (CSV / DB do cliente)
   │  (Ingestion + validação de schema/qualidade)
   ▼
Feature pipeline (scikit-learn) ── Feature Store (V1+)
   │
   ▼
Inference Service ──(MLflow model registry: versão N)──► Score + SHAP
   │
   ├─► Persistência (Postgres): predição + versão + trace_id
   ├─► Métricas (Prometheus) + logs estruturados + span (OTel)
   └─► Frontend (BFF / TanStack Query)
                       │
                       ▼
              Ação registrada ──► Feedback loop ──► Monitor de drift ──► Re-treino
```

---

## 6. Versionamento e Reprodutibilidade

- **Modelos:** versionados no MLflow; cada predição grava `model_version`.
- **Dados de treino:** versionados (DVC ou snapshot em object storage).
- **Código:** SemVer + tags; imagens Docker com digest imutável.
- **Schema de API:** OpenAPI versionado; *contract tests* no CI.

---

## 7. Estratégia de Testes

| Nível | Ferramenta | Foco |
|-------|-----------|------|
| Unidade | Pytest | Lógica de domínio, adapters, transforms |
| Contrato | Schemathesis / OpenAPI | Conformidade da API |
| Integração | Pytest + Testcontainers | Postgres/Redis reais |
| ML | Pytest + métricas mínimas | Recall/AUC não regridem (gate) |
| E2E Front | Playwright | Jornadas críticas |
| Carga | k6 / Locust | SLOs de latência e throughput |

> **Quality gate** no CI: lint (Ruff), tipos (Mypy), testes, cobertura mínima e
> *model performance gate* (bloqueia merge se AUC/recall caírem além do limiar).


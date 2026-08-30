# 11 — Riscos, Premissas e Decisões Arquiteturais (ADRs)

> Registro consolidado de **riscos**, **premissas** e **Architecture Decision
> Records**. ADRs são imutáveis: uma decisão revogada é *substituída* por outra,
> nunca apagada.

---

## Parte 1 — Premissas

| ID | Premissa | Impacto se falsa |
|----|----------|------------------|
| PR-01 | O dataset Telco público é suficiente como tenant de demonstração | Necessário gerar dados sintéticos adicionais |
| PR-02 | Latência de inferência XGBoost permite p95 < 200 ms sem GPU | Necessário otimização/serving dedicado |
| PR-03 | SHAP (`TreeExplainer`) é rápido o bastante para uso sob demanda | Pré-computar/aproximar explicações |
| PR-04 | Postgres + RLS atende isolamento multi-tenant no MVP | Antecipar isolamento físico |
| PR-05 | Um time pequeno (ou solo) implementa o roadmap incrementalmente | Repriorizar escopo por fase |
| PR-06 | Clientes fornecem dados em schema mapeável ao modelo | Camada de mapeamento por tenant mais robusta |
| PR-07 | Kubernetes é aceitável como alvo de deploy | Alternativa: serverless/PaaS |

---

## Parte 2 — Riscos

Escala: Probabilidade (B/M/A) × Impacto (B/M/A).

| ID | Risco | P | I | Mitigação |
|----|-------|---|---|-----------|
| RI-01 | **Over-engineering** para um projeto de portfólio | A | M | Roadmap em fases; cada fase é demonstrável e útil isolada |
| RI-02 | **Drift de modelo** degrada predições silenciosamente | M | A | Monitoramento de drift + alertas + re-treino (Fase 3) |
| RI-03 | **Vazamento entre tenants** | B | A | RLS + testes de isolamento automatizados no CI |
| RI-04 | **Custo de infra** cresce além do esperado | M | M | Scale-to-zero, cache, FinOps, ambientes efêmeros sob demanda |
| RI-05 | **Latência de SHAP** estoura SLO | M | M | SHAP sob demanda + cache + TreeExplainer |
| RI-06 | **Escopo grande** atrasa entrega visível | A | M | Priorizar telas "uau" e MLOps (alto sinal) primeiro |
| RI-07 | **Qualidade de dados** do cliente quebra scoring | M | A | Validação (Pandera/GE) + degradação graciosa + relatórios |
| RI-08 | **Conformidade LGPD/GDPR** mal endereçada | B | A | Privacidade por design; auditoria; data subject requests |
| RI-09 | **Lock-in** de fornecedor cloud | B | M | OTel neutro, Terraform, abstrações de storage |
| RI-10 | **Desbalanceamento de classes** prejudica recall | M | M | `scale_pos_weight` (já aplicado) + threshold tuning + monitoramento |
| RI-11 | **Complexidade operacional** do K8s para um dev | M | M | Monólito modular + compose local; K8s só em staging/prod |

---

## Parte 3 — Architecture Decision Records (ADRs)

> Formato: Contexto → Decisão → Consequências → Status.

### ADR-01 — Núcleo em Python/FastAPI (reuso do existente)
- **Status:** Aceito.
- **Contexto:** já existe API FastAPI + pipeline scikit-learn/XGBoost maduros.
- **Decisão:** manter Python/FastAPI como núcleo de inferência; evoluir, não reescrever.
- **Consequências:** ✅ reaproveitamento, time-to-value baixo. ⚠️ Python não é o
  mais rápido para alto throughput — mitigado por workers, cache e autoscaling.

### ADR-02 — Multi-tenancy por Row-Level Security (RLS) no MVP
- **Status:** Aceito.
- **Contexto:** precisamos isolar tenants sem custo operacional de múltiplos bancos.
- **Decisão:** isolamento lógico via `tenant_id` + RLS no PostgreSQL.
- **Consequências:** ✅ simples e seguro com testes. ⚠️ tenants enterprise muito
  grandes podem exigir isolamento físico (evolução prevista).

### ADR-03 — Monólito modular antes de microsserviços
- **Status:** Aceito.
- **Contexto:** evitar complexidade distribuída prematura num projeto enxuto.
- **Decisão:** começar como monólito modular com fronteiras de domínio claras;
  extrair serviços (ex.: workers, MLOps) só quando escala/deploy justificarem.
- **Consequências:** ✅ operável e rápido de evoluir. ⚠️ exige disciplina de
  fronteiras para permitir extração futura.

### ADR-04 — MLflow para registro e versionamento de modelos
- **Status:** Aceito.
- **Contexto:** rastreabilidade modelo→dados→métricas é diferencial de maturidade.
- **Decisão:** usar MLflow como model registry + tracking; cada predição grava `model_version`.
- **Consequências:** ✅ reprodutibilidade, rollback, gates. ⚠️ um componente a
  operar (mitigado com versão gerenciada/leve).

### ADR-05 — OpenTelemetry como padrão único de instrumentação
- **Status:** Aceito.
- **Contexto:** evitar lock-in e padronizar logs/métricas/traces.
- **Decisão:** instrumentar tudo com OTel; backends (Prometheus/Loki/Tempo)
  intercambiáveis via Collector.
- **Consequências:** ✅ neutralidade de fornecedor, correlação total. ⚠️ curva de
  configuração inicial.

### ADR-06 — Frontend em React/Next.js + design system próprio
- **Status:** Aceito.
- **Contexto:** o produto precisa de UX de classe mundial e forte sinal de portfólio.
- **Decisão:** Next.js (App Router) + TypeScript + Tailwind + Radix/shadcn +
  TanStack Query; tipos gerados do OpenAPI.
- **Consequências:** ✅ DX excelente, A11y, contratos tipados. ⚠️ exige disciplina
  de design system para consistência.

### ADR-07 — Contracts-first (OpenAPI) e erros RFC 7807
- **Status:** Aceito.
- **Contexto:** alinhar front/back e permitir contract tests.
- **Decisão:** API definida por OpenAPI versionado; erros em Problem Details.
- **Consequências:** ✅ menos drift, melhor DX. ⚠️ disciplina de manter o spec.

### ADR-08 — Adapter PT↔EN generalizado por locale
- **Status:** Aceito (evolui o padrão atual).
- **Contexto:** já existe Adapter PT→schema do modelo; precisamos de i18n real.
- **Decisão:** generalizar o mapeamento para tabela por *locale*, desacoplando o
  domínio de negócio do schema do modelo.
- **Consequências:** ✅ i18n e manutenção mais simples. ⚠️ exige cobertura de testes
  do mapeamento.

### ADR-09 — Processamento assíncrono para batch e re-treino
- **Status:** Aceito.
- **Contexto:** scoring em lote e re-treino são pesados e não devem bloquear a API.
- **Decisão:** filas (Redis) + workers (Celery/Arq), com idempotência e backpressure.
- **Consequências:** ✅ resiliência e escala (KEDA scale-to-zero). ⚠️ complexidade
  de orquestração de jobs.

### ADR-10 — Container non-root e supply chain security no CI
- **Status:** Aceito (formaliza o que já existe + amplia).
- **Contexto:** o Dockerfile já roda non-root; falta cobrir a cadeia de suprimentos.
- **Decisão:** manter non-root + adicionar SAST/SCA/secret scan, SBOM e assinatura
  de artefatos no pipeline.
- **Consequências:** ✅ postura de segurança forte e auditável. ⚠️ pipeline mais longo.

---

## Parte 4 — Decisões em Aberto (a revisitar)

| ID | Questão | Quando decidir |
|----|---------|----------------|
| OD-01 | Celery vs. Arq vs. RQ para workers | Início da Fase 1 |
| OD-02 | Loki/ELK e Tempo/Jaeger como backends | Fase 0 |
| OD-03 | Feature Store agora (Feast) vs. adiar | Fase 3 |
| OD-04 | Warehouse (DuckDB local vs. gerenciado) para analytics | Fase 2/3 |
| OD-05 | Estratégia de threshold por tenant (auto vs. manual) | Fase 1 |

---

## Parte 5 — Rastreabilidade entre Documentos

| Decisão | Relaciona-se a |
|---------|----------------|
| ADR-02 (RLS) | `04_architecture.md` §5, `08_security.md` §3, RI-03 |
| ADR-04 (MLflow) | `06_observability_traceability.md` §6–7, RF-72 |
| ADR-05 (OTel) | `06_observability_traceability.md` inteiro, RNF-40 |
| ADR-06 (Frontend) | `09_frontend_ux.md` inteiro |
| ADR-09 (Async) | `07_performance_scalability.md` §4, RNF-13 |


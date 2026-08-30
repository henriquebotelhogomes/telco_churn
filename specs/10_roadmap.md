# 10 — Roadmap de Evolução

> Caminho incremental do repositório técnico atual até um SaaS sólido. Cada fase
> é **demonstrável** e adiciona um sinal de maturidade de engenharia. Estimativas
> são relativas (esforço), não datas rígidas.

---

## 1. Estado Atual (baseline)

✅ Já existe e funciona:
- Modelo XGBoost + pipeline scikit-learn (anti-leakage).
- API FastAPI com `/predict`, `/health`, schema PT↔EN (Adapter).
- Docker multi-stage non-root, Makefile, uv, Ruff, Mypy, Pytest, CI/CD.

**Gap para SaaS:** sem persistência, multi-tenancy, frontend, explicabilidade,
observabilidade completa e MLOps de produção.

---

## 2. Visão em Fases

```
Fase 0  Fundação & Higiene  ──▶  Fase 1  Núcleo do Produto (MVP)
   │                                   │
   ▼                                   ▼
Fase 4  Enterprise & Escala  ◀── Fase 3  MLOps & Confiabilidade ◀── Fase 2  Plataforma SaaS
```

---

## 3. Fase 0 — Fundação e Higiene Técnica

**Objetivo:** preparar o terreno e maximizar sinais de qualidade no repositório.

- [ ] Adotar esta pasta `specs/` como fonte de verdade (feito).
- [ ] OpenAPI versionado + erros RFC 7807.
- [ ] Observabilidade base: logs estruturados + `/metrics` + tracing OTel local.
- [ ] `docker-compose` para stack local (API + Postgres + Redis + Grafana).
- [ ] Reforçar CI: cobertura, *model performance gate*, SCA/SAST/secret scan.
- [ ] ADRs iniciais publicados (`11_*`).

**Entregável demonstrável:** repo com observabilidade e qualidade visíveis no README.

---

## 4. Fase 1 — Núcleo do Produto (MVP)

**Objetivo:** transformar a predição isolada em fluxo de produto end-to-end.

- [ ] **Persistência** de predições (Postgres) com `model_version` + `trace_id` (RF-13).
- [ ] **Explicabilidade SHAP** nos detalhes do cliente (RF-20).
- [ ] **Priorização** risco × valor (RF-30).
- [ ] **Scoring em lote** assíncrono (RF-11).
- [ ] **AuthN + multi-tenant** com RLS (RF-80).
- [ ] **Frontend MVP** (Next.js): dashboard, fila priorizada, detalhe do cliente
  com drivers e what-if (RF-50).
- [ ] **Demo tenant** pré-carregado com dataset Telco (para recrutadores testarem).

**Entregável demonstrável:** SaaS navegável com login, scoring, explicação e ação.

---

## 5. Fase 2 — Plataforma SaaS

**Objetivo:** maturidade de plataforma e colaboração.

- [ ] **RBAC** (Admin/Analista/Leitor) + **trilha de auditoria** (RF-81, RF-82).
- [ ] **Conectores de dados** (Postgres/BigQuery/S3) + validação de schema (RF-02/03).
- [ ] **Playbooks de retenção** + registro de resultado, fechando o loop (RF-40/41).
- [ ] **Cohorts & analytics** (RF-60).
- [ ] **i18n** pt-BR/en-US ponta a ponta (RF-90).
- [ ] **IaC (Terraform)** + deploy em Kubernetes + ambientes efêmeros por PR.

**Entregável demonstrável:** múltiplos usuários/papéis, integrações e analytics.

---

## 6. Fase 3 — MLOps e Confiabilidade

**Objetivo:** modelos que se mantêm saudáveis em produção (grande diferencial).

- [ ] **MLflow** model registry + versionamento de dados (DVC/snapshot) (RF-72).
- [ ] **Monitoramento de drift** (data/prediction/concept) + alertas (RF-70).
- [ ] **Re-treino orquestrado** + promoção com *gate* + **rollback** (RF-71).
- [ ] **Canary/Shadow deployment** de modelos.
- [ ] **SLOs + error budget** com dashboards Grafana e alertas.
- [ ] **Feature Store (Feast)** para consistência online/offline.

**Entregável demonstrável:** painel de saúde do modelo + ciclo de re-treino automatizado.

---

## 7. Fase 4 — Enterprise e Escala

**Objetivo:** prontidão comercial e escala.

- [ ] **SSO (OIDC/SAML) + SCIM** (RF-83).
- [ ] **Billing/usage metering** por tenant.
- [ ] **Sharding por tenant** + warehouse para analytics em escala.
- [ ] **SBOM + assinatura de artefatos** + pentest externo.
- [ ] **Data residency** regional.
- [ ] **Integrações outbound** (CRM/e-mail) para acionar retenção (RF-42).

**Entregável demonstrável:** prontidão para clientes enterprise.

---

## 8. Marcos de Portfólio (o que mostrar e quando)

| Marco | Demonstra | Fase |
|-------|-----------|------|
| API observável + CI robusto | Engenharia de software | 0 |
| SaaS navegável com explicabilidade | Produto + ML aplicado | 1 |
| Multi-tenant + RBAC + IaC | Engenharia de plataforma | 2 |
| Drift + re-treino + SLOs | **MLOps sênior** (raro) | 3 |
| Enterprise-ready | Visão de negócio | 4 |

---

## 9. Critérios de "Pronto" (Definition of Done) por fase

- Testes (unidade/integração/E2E) verdes + cobertura ≥ alvo.
- Observabilidade: dashboards e alertas da feature existem.
- Segurança: scans no CI passam; sem segredos no código.
- Documentação: ADRs e OpenAPI atualizados; README com GIF/demo.
- Performance: SLOs validados em staging.

---

## 10. Priorização (impacto × esforço para portfólio)

| Iniciativa | Impacto | Esforço | Prioridade |
|------------|---------|---------|-----------|
| Explicabilidade SHAP no front | 🔴 Alto | 🟡 Médio | 1 |
| Observabilidade + SLOs | 🔴 Alto | 🟡 Médio | 1 |
| Frontend impecável (detalhe do cliente) | 🔴 Alto | 🔴 Alto | 1 |
| Drift + re-treino (MLOps) | 🔴 Alto | 🔴 Alto | 2 |
| Multi-tenancy + RBAC | 🟡 Médio | 🟡 Médio | 2 |
| SSO/billing enterprise | 🟢 Baixo (portfólio) | 🔴 Alto | 4 |


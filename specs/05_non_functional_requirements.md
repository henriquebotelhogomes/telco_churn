# 05 — Requisitos Não Funcionais (RNF)

> Requisitos de qualidade rastreáveis (`RNF-XX`), com metas mensuráveis (SLOs).
> Estes requisitos são tão importantes quanto os funcionais para a percepção de
> maturidade de engenharia.

---

## 1. Disponibilidade e Confiabilidade

| ID | Requisito | Meta |
|----|-----------|------|
| RNF-01 | Disponibilidade da API de scoring | **99.9%** mensal (SLO) |
| RNF-02 | Tolerância a falha de instância | Sem perda de requisições (múltiplas réplicas) |
| RNF-03 | RTO (Recovery Time Objective) | ≤ 30 min |
| RNF-04 | RPO (Recovery Point Objective) | ≤ 15 min (backups Postgres) |
| RNF-05 | Degradação graciosa | Se SHAP falhar, retornar score sem drivers, não erro 500 |

---

## 2. Performance (SLOs)

| ID | Requisito | Meta |
|----|-----------|------|
| RNF-10 | Latência scoring individual (p95) | **< 200 ms** (sem explicabilidade) |
| RNF-11 | Latência scoring + drivers SHAP (p95) | < 600 ms |
| RNF-12 | Throughput por réplica | ≥ 150 req/s (scoring simples) |
| RNF-13 | Batch de 100k clientes | < 10 min |
| RNF-14 | Carregamento do modelo (cold start) | < 5 s |

> Detalhes e estratégias em `07_performance_scalability.md`.

---

## 3. Escalabilidade

| ID | Requisito |
|----|-----------|
| RNF-20 | Serviços de aplicação **DEVEM** ser stateless e escaláveis horizontalmente |
| RNF-21 | Workers de batch **DEVEM** escalar por profundidade de fila (KEDA) |
| RNF-22 | O sistema **DEVE** suportar crescimento de tenants sem refatoração estrutural |

---

## 4. Segurança e Privacidade

| ID | Requisito |
|----|-----------|
| RNF-30 | Todo tráfego **DEVE** usar TLS 1.2+ |
| RNF-31 | Dados em repouso **DEVEM** ser criptografados |
| RNF-32 | Isolamento de tenant **DEVE** ser garantido por RLS + testes automatizados |
| RNF-33 | Segredos **NÃO DEVEM** estar no código (secret manager) |
| RNF-34 | Container **DEVE** rodar como usuário non-root (já implementado) |

> Detalhes em `08_security.md`.

---

## 5. Observabilidade

| ID | Requisito |
|----|-----------|
| RNF-40 | Toda requisição **DEVE** ter `trace_id` propagado (OTel) |
| RNF-41 | Logs **DEVEM** ser estruturados (JSON) e correlacionáveis por trace |
| RNF-42 | Métricas RED/USE **DEVEM** ser expostas em `/metrics` |
| RNF-43 | Drift de modelo **DEVE** ser monitorado e alertado |

> Detalhes em `06_observability_traceability.md`.

---

## 6. Manutenibilidade

| ID | Requisito | Meta |
|----|-----------|------|
| RNF-50 | Cobertura de testes (linhas) | ≥ **85%** no core de domínio |
| RNF-51 | Tipagem estática | Mypy `strict` sem erros (já adotado) |
| RNF-52 | Lint/format | Ruff sem violações (já adotado) |
| RNF-53 | Complexidade ciclomática por função | ≤ 10 |
| RNF-54 | Documentação | ADRs atualizados + OpenAPI publicado |
| RNF-55 | Dívida técnica | Rastreada e priorizada no backlog |

---

## 7. Portabilidade e Operação

| ID | Requisito |
|----|-----------|
| RNF-60 | A aplicação **DEVE** rodar via Docker em qualquer ambiente (já implementado) |
| RNF-61 | Infra **DEVE** ser provisionável via IaC (Terraform) |
| RNF-62 | Deploys **DEVEM** ser reproduzíveis e auditáveis (CI/CD) |
| RNF-63 | Configuração **DEVE** vir de ambiente, nunca hardcoded (12-Factor; já via Pydantic Settings) |

---

## 8. Usabilidade e Acessibilidade

| ID | Requisito | Meta |
|----|-----------|------|
| RNF-70 | Acessibilidade | **WCAG 2.1 AA** |
| RNF-71 | Performance web (Core Web Vitals) | LCP < 2.5s, INP < 200ms, CLS < 0.1 |
| RNF-72 | Internacionalização | pt-BR e en-US |
| RNF-73 | Responsividade | Desktop-first, funcional em tablet |

---

## 9. Conformidade

| ID | Requisito |
|----|-----------|
| RNF-80 | Aderência a **LGPD/GDPR** (dados de clientes finais) |
| RNF-81 | Direito ao esquecimento e exportação de dados (data subject requests) |
| RNF-82 | Trilha de auditoria retida por período configurável |
| RNF-83 | Explicabilidade do modelo para suporte a decisões (transparência algorítmica) |

---

## 10. Matriz de Priorização (resumo)

| Atributo de Qualidade | Prioridade | Fase |
|-----------------------|-----------|------|
| Segurança & multi-tenancy | 🔴 Alta | MVP |
| Observabilidade | 🔴 Alta | MVP |
| Performance de scoring | 🔴 Alta | MVP |
| Escalabilidade horizontal | 🟡 Média | V1 |
| Conformidade LGPD/GDPR | 🟡 Média | V1 |
| Acessibilidade AA | 🟡 Média | V1 |


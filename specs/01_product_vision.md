# 01 — Visão de Produto

> **Produto:** RetainIQ — *Customer Retention Intelligence Platform*
> **Tagline:** "Pare de perder clientes que você poderia ter salvo."

---

## 1. Contexto e Problema

Empresas de receita recorrente (telecom, SaaS, streaming, fintech, seguros)
vivem ou morrem pela sua **taxa de retenção**. Adquirir um novo cliente custa de
**5 a 25× mais** do que reter um existente, e uma redução de 5% no churn pode
aumentar o lucro em 25%–95% (Bain & Company).

Apesar disso, a maioria das equipes de retenção opera de forma **reativa**:
descobrem o cancelamento *depois* que ele acontece, agem por intuição e não
conseguem priorizar onde investir esforço de retenção (que também tem custo).

O projeto original já resolve o "coração" técnico: um modelo de ML que prevê a
probabilidade de churn. O salto de produto é transformar essa **predição isolada**
em um **sistema de decisão acionável**.

---

## 2. Visão

> Tornar a retenção de clientes uma disciplina **preditiva, explicável e
> acionável** para qualquer empresa de receita recorrente, sem exigir um time de
> Data Science interno.

O RetainIQ entrega, em uma única plataforma:

1. **Previsão** — *quem* vai cancelar e *quando* (score de risco).
2. **Explicação** — *por quê* aquele cliente está em risco (drivers do churn).
3. **Priorização** — *onde* agir primeiro (risco × valor do cliente).
4. **Ação** — *o que* fazer (playbooks de retenção recomendados).
5. **Aprendizado** — *funcionou?* (medição do impacto das ações).

---

## 3. Proposta de Valor

| Para... | Que... | O RetainIQ... | Diferente de... |
|---------|--------|---------------|-----------------|
| Times de CS/Retenção | precisam reduzir churn proativamente | entrega scores de risco explicáveis e playbooks acionáveis | dashboards de BI estáticos |
| Líderes de Receita | precisam proteger MRR/ARR | quantifica a *receita em risco* e o ROI das ações de retenção | planilhas e intuição |
| Times de Dados | não querem reinventar a roda de MLOps | oferece modelos versionados, monitorados e prontos para produção | construir tudo do zero |

**Proposta de valor central (one-liner):**
> "Transformamos seus dados de clientes em uma fila priorizada de ações de
> retenção, com explicação do risco e medição de resultado — em dias, não meses."

---

## 4. Público-Alvo

### Segmento primário
- **Empresas B2C de assinatura** de médio porte (telecom, streaming, fitness,
  edtech, fintech) com **10k–5M clientes** e churn mensal relevante.

### Segmento secundário
- **SaaS B2B** com churn por conta/seat.
- **Seguradoras e bancos digitais** (retenção de produto).

### Compradores e usuários
- **Comprador econômico:** VP de Receita / Head de Growth / CFO.
- **Usuário campeão:** Líder de Customer Success / Retenção.
- **Usuário técnico:** Engenheiro de Dados que conecta as fontes.

---

## 5. Posicionamento e Diferenciação

**Categoria:** Customer Retention Intelligence (entre *Customer Data Platform* e
*BI*, com um núcleo de *Decision Intelligence*).

**Eixos de diferenciação:**

1. **Explicabilidade-first** — cada score vem com seus *drivers* (SHAP),
   gerando confiança e adoção (vs. caixas-pretas).
2. **Acionável, não só analítico** — fecha o loop predição → ação → resultado.
3. **MLOps embarcado** — modelos que se mantêm saudáveis (monitoramento de drift
   e re-treino), sem time de DS no cliente.
4. **Time-to-value baixo** — conectores e *templates* por vertical.

---

## 6. Modelo de Negócio (ilustrativo)

- **SaaS por assinatura**, com *tiers* por volume de clientes monitorados e
  features (explicabilidade avançada, integrações, SSO/RBAC, SLA).
- **Free / Demo tier** para o portfólio: dataset Telco público pré-carregado,
  permitindo que recrutadores testem o produto sem onboarding.
- Métricas-chave do negócio (North Star): **Receita Retida Influenciada** —
  MRR de clientes em risco que permaneceram após ação recomendada.

---

## 7. Métricas de Sucesso do Produto

| Categoria | Métrica | Alvo (referência) |
|-----------|---------|-------------------|
| Adoção | % de clientes em risco com ação registrada | > 60% |
| Modelo | ROC-AUC em produção | ≥ 0.82, sem degradação > 3% |
| Negócio | Redução relativa de churn vs. baseline | 10–20% |
| Produto | Time-to-first-insight (onboarding) | < 30 min |
| Confiança | NPS do time de retenção | > 40 |

---

## 8. Escopo da Demonstração de Portfólio

Para fins de portfólio, o RetainIQ é entregue como um **SaaS funcional de
demonstração**, com o dataset público *Telco Customer Churn* como tenant de
exemplo. O foco é evidenciar **excelência de engenharia e produto**, não cobertura
de mercado. O `10_roadmap.md` detalha o caminho do MVP demonstrável até a versão
comercial.


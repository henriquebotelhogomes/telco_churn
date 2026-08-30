# 09 — Frontend e Experiência do Usuário

> Proposta de um frontend **impecável, moderno e impactante** que traduz a
> inteligência do RetainIQ em decisões claras. Atende `RNF-70`–`RNF-73`.
> Objetivo de portfólio: um produto que **parece** e **funciona** como SaaS real.

---

## 1. Princípios de Design

1. **Clareza acima de tudo** — o usuário entende risco e ação em segundos.
2. **Da predição à ação** — cada tela termina numa decisão possível.
3. **Confiança via explicabilidade** — nunca um número sem o "porquê".
4. **Performance é UX** — Core Web Vitals como requisito (`RNF-71`).
5. **Acessível por padrão** — WCAG 2.1 AA (`RNF-70`).
6. **Consistência** — design system próprio, tokens e componentes reutilizáveis.

---

## 2. Stack de Frontend

| Camada | Escolha | Justificativa |
|--------|---------|---------------|
| Framework | **React 18 + TypeScript** | Tipagem forte, ecossistema |
| Meta-framework | **Next.js (App Router)** | SSR/streaming, rotas, DX |
| Estilo | **Tailwind CSS** | Velocidade + consistência via tokens |
| Componentes | **Radix UI + shadcn/ui** | Acessíveis, headless, customizáveis |
| Estado servidor | **TanStack Query** | Cache, revalidação, sincronização |
| Estado cliente | **Zustand** | Leve para UI state |
| Formulários | **React Hook Form + Zod** | Validação tipada espelhando a API |
| Dataviz | **Visx / Recharts** (+ D3 quando necessário) | Gráficos performáticos e custom |
| Tabelas | **TanStack Table** | Virtualização, ordenação, filtros |
| Animação | **Framer Motion** | Microinterações sutis |
| i18n | **next-intl** | pt-BR / en-US (`RNF-72`) |
| Testes | **Vitest + Testing Library + Playwright** | Unidade, componente e E2E |
| Qualidade | **ESLint + Prettier + Storybook** | DX e documentação viva de UI |

---

## 3. Design System

- **Tokens de design:** cores, tipografia, espaçamento, raios, sombras e
  *z-index* centralizados (compatível com Tailwind + CSS variables).
- **Tema claro/escuro** com persistência e respeito a `prefers-color-scheme`.
- **Paleta semântica de risco:** verde (baixo), âmbar (médio), vermelho (alto) —
  sempre acompanhada de rótulo textual e ícone (não depender só de cor — A11y).
- **Tipografia:** *Inter* (UI) + um display sutil para títulos; números tabulares
  para métricas.
- **Componentes-base:** Button, Card, Badge, Table, Dialog, Drawer, Toast,
  Tooltip, Tabs, EmptyState, Skeleton, RiskGauge, DriverBar (SHAP), StatCard.
- **Storybook** documenta cada componente com estados e variações.

---

## 4. Arquitetura de Informação (telas)

```
/login
/onboarding            (conectar/upload de dados)
/dashboard             (visão executiva: receita em risco, KPIs)
/customers             (fila priorizada: tabela com risco × valor)
/customers/:id         (detalhe: score, drivers SHAP, what-if, ação)
/cohorts               (analytics por coorte e período)
/models                (saúde do modelo, drift, versões)
/settings              (usuários, RBAC, integrações, billing)
```

---

## 5. Telas-Chave (especificação de UX)

### 5.1 Dashboard Executivo
- **Hero metrics:** Receita em Risco (R$), Clientes em Alto Risco, Churn projetado,
  Ações em aberto — em `StatCard` com tendência (sparkline).
- **Gráfico principal:** evolução de receita em risco × retida (área empilhada).
- **Top movers:** clientes que mudaram de classe de risco recentemente.
- **Estado vazio** elegante guia o onboarding (upload de dados).

### 5.2 Fila Priorizada de Clientes
- **Tabela virtualizada** (TanStack Table) ordenada por `risco × valor`.
- Colunas: cliente, MRR, score (RiskGauge mini), classe, principal driver, ação.
- **Filtros salvos** e busca; **bulk actions** (ex.: marcar para campanha).
- Densidade ajustável; export CSV.

### 5.3 Detalhe do Cliente (a tela "uau")
- **RiskGauge** grande com probabilidade e classe.
- **Drivers (SHAP)** em barras divergentes: o que aumenta vs. reduz o risco,
  em **linguagem de negócio** (RF-22).
- **Simulador What-if** (RF-50): controles para alterar contrato, serviços, etc.,
  com **recálculo em tempo real** e *delta* animado do score.
- **Playbooks recomendados** (RF-40) com botão para **registrar ação** (RF-41).
- **Timeline** de eventos e ações do cliente.

### 5.4 Saúde do Modelo (MLOps para humanos)
- Cards de **drift** por feature (PSI), **AUC/recall rolling**, **frescor**.
- Linha do tempo de versões com diff de métricas e botão de **rollback** (visual).
- Transparência que **impressiona recrutadores técnicos**.

---

## 6. Microinterações e Estados

- **Skeletons** durante carregamento (nunca telas em branco).
- **Optimistic UI** ao registrar ações (TanStack Query mutations).
- **Toasts** para feedback; **empty states** ilustrados e acionáveis.
- **Transições sutis** (Framer Motion) — funcionais, nunca gratuitas.
- **Estados de erro** claros, com retry e correlação ao suporte (trace id).

---

## 7. Acessibilidade (WCAG 2.1 AA)

- Navegação completa por teclado; *focus rings* visíveis.
- Contraste mínimo AA; cor nunca como único portador de significado.
- Componentes Radix garantem semântica ARIA correta.
- `prefers-reduced-motion` respeitado.
- Testes automatizados de a11y (axe) no CI.

---

## 8. Performance Web

- **SSR/streaming** (Next.js) para *first paint* rápido.
- **Code splitting** por rota e **lazy loading** de gráficos pesados.
- **Imagens otimizadas** (next/image) e fontes com `display: swap`.
- **TanStack Query** evita refetch desnecessário; *prefetch* em hover.
- Orçamento de performance no CI (Lighthouse CI): LCP < 2.5s, INP < 200ms,
  CLS < 0.1 (`RNF-71`).

---

## 9. Integração com Backend

- **Tipos gerados** a partir do OpenAPI (ex.: `openapi-typescript`) — contrato
  único entre front e back, sem *drift* de tipos.
- **Validação Zod** no cliente espelha o schema do servidor.
- **BFF** (Next.js Route Handlers) agrega chamadas e protege segredos.
- **Autenticação** via sessão segura (cookies httpOnly) + tokens curtos.

---

## 10. Qualidade e DX

- **Storybook** publicado (Chromatic) como vitrine de UI — ótimo para portfólio.
- **Visual regression** + testes E2E (Playwright) das jornadas críticas.
- **Conventional Commits** + preview deploys por PR (ambiente efêmero).

---

## 11. Por que isso impressiona recrutadores

- Demonstra domínio de **React/Next moderno + TypeScript + design system**.
- Mostra **dataviz com propósito** (SHAP, drift) — raro e técnico.
- Evidencia preocupação com **A11y, performance e contratos tipados**.
- Entrega uma **experiência coesa de produto**, não um CRUD genérico.


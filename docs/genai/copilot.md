# Copilot GenAI de Retenção & Negociação

O **Copilot de Retenção** do RetainIQ auxilia a equipe de atendimento com geração automatizada de roteiros comerciais personalizados.

---

## 🤖 Arquitetura Multi-Provedor com Fallback

```mermaid
graph TD
    A[Requisição com Dados do Cliente + SHAP] --> B{Chave Gemini ou OpenAI configurada?}
    B -- Sim --> C[Chamada LLM: Gemini 1.5 Flash / GPT-4o-mini]
    B -- Não ou Erro --> D[Motor Heurístico Determinístico de Fallback]
    C --> E[Roteiro de Negociação Estruturado]
    D --> E
```

---

## 🎭 Motor de Variação de Tom

O usuário pode alternar dinamicamente o estilo de comunicação:
- **Empático:** Focado em acolhimento, escuta ativa e compreensão das insatisfações.
- **Firme:** Focado na exclusividade da oferta, valor dos benefícios e senso de urgência.
- **Consultivo:** Abordagem analítica comparando custo-benefício e otimização de planos.
- **Direto:** Comunicação objetiva e simplificada para WhatsApp e mensagens rápidas.

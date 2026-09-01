# Processamento em Tempo Real com Apache Flink (Fase 2 - Marco M12)

O **Marco M12** implementa o motor de processamento de fluxo contínuo (*Stream Processing*) com estado (*Stateful Processing*), janelas deslizantes (*Sliding Windows*) e disparo de alertas reativos com latência inferior a $100\text{ ms}$.

---

## 🏗️ Arquitetura de Janelas Deslizantes (*Sliding Windows*)

Enquanto o treinamento tradicional de Machine Learning opera em lotes (*batch* diários ou semanais), clientes com problemas agudos de conectividade ou insatisfação financeira demandam **intervenção proativa imediata**.

```mermaid
graph TD
    subgraph StreamSources["Eventos Redpanda / Kafka (M11)"]
        T1["telemetry.network.events"]
        T2["billing.payment.events"]
        T3["crm.interaction.events"]
    end

    subgraph WindowProcessor["Stream Window Engine (Apache Flink / PyWorker)"]
        W15["Janela 15 Minutos:<br/>• Latência média (ms)<br/>• Perda de pacotes (%)"]
        W1H["Janela 1 Hora:<br/>• Quedas de fibra/rede acumuladas"]
        W24H["Janela 24 Horas:<br/>• Falhas consecutivas de pagamento"]
        W7D["Janela 7 Dias:<br/>• Sentimento de suporte e chamados SAC"]
        
        SCORE["Cálculo do Realtime Instability Score [0.0 - 1.0]"]
        TRIGGER["Motor de Alertas Reativos (SLA < 100ms)"]
        
        T1 --> W15
        T1 --> W1H
        T2 --> W24H
        T3 --> W7D
        
        W15 --> SCORE
        W1H --> SCORE
        W24H --> SCORE
        W7D --> SCORE
        
        SCORE --> TRIGGER
    end

    subgraph Outputs["Consumidores em Tempo Real"]
        FS["Feature Store / Redis (Marco M13)"]
        UI["Cockpit Visual RetainIQ"]
        COPILOT["Copilot GenAI / Ações Proativas"]
    end

    SCORE --> FS
    SCORE --> UI
    TRIGGER --> COPILOT
```

---

## ⏱️ Janelas Deslizantes Suportadas

| Janela | Escopo | Métricas Computadas | Limiar de Alerta Crítico |
| :--- | :--- | :--- | :--- |
| **15 Minutos** | Qualidade de Rede | `avg_latency_15min`, `avg_packet_loss_15min` | Latência $> 150\text{ ms}$ e Perda $> 10\%$ |
| **1 Hora** | Estabilidade de Fibra | `disconnect_count_1h` | $\ge 3$ quedas de sinal na hora |
| **24 Horas** | Saúde Financeira | `failed_payment_count_24h` | $\ge 2$ tentativas de cobrança recusadas |
| **7 Dias** | Sentimento de CRM | `negative_crm_count_7d`, `avg_sentiment_7d` | Sentimento $\le -0.40$ em chamados de suporte |

---

## ⚡ Fórmula do Score de Instabilidade em Tempo Real

A cada novo evento ingerido pelo motor de streaming, o cliente tem seu score de volatilidade recalculado dinamicamente:

$$\text{Instability Score} = \min\left(1.0, 0.40 \times \frac{\text{Quedas}_{1h}}{3} + 0.20 \times \frac{\text{Latência}_{15m}}{200} + 0.25 \times \frac{\text{Falhas}_{24h}}{2} + 0.15 \times \mathbb{I}(\text{Sentimento} < -0.3)\right)$$

---

## 🚨 Fila de Alertas Reativos de Churn

Quando as regras de risco são violadas, um `RealtimeRiskAlert` é gerado e disponibilizado via API REST:

- **`GET /api/v1/streaming/windows`**: Lista todas as janelas dos clientes em monitoramento ativo.
- **`GET /api/v1/streaming/windows/{customer_id}`**: Detalhes em tempo real de um cliente específico.
- **`GET /api/v1/streaming/alerts`**: Fila de alertas para atendimento proativo.
- **`POST /api/v1/streaming/alerts/{alert_id}/acknowledge`**: Confirmação de atendimento por um operador ou sistema automatizado.

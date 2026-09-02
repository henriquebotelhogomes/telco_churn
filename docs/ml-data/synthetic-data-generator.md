# ⚡ Synthetic Data Engineering & Data Augmentation (Telco 360 Enterprise)

A plataforma **RetainIQ** incorpora um módulo nativo de **Engenharia de Dados Sintéticos e Simulação Causal** para resolver um dos maiores desafios de IA no setor de telecomunicações: **Treinamento e Homologação Contínua em conformidade com a LGPD/GDPR sem expor dados confidenciais de clientes reais.**

---

## 🏛️ Por que Geração de Dados Sintéticos em Telecomunicações?

1. **Conformidade Regulatória (LGPD / ANPD / Anatel):**  
   Dados de assinantes (CPFs, históricos de chamadas, registros de cartões de crédito e localização) são protegidos por sigilo e leis de privacidade. O compartilhamento ou uso inseguro em ambientes de teste gera riscos de multas severas.
2. **Causalidade de Rede (Physics of Telecom QoE):**  
   Bases públicas tradicionais (como o dataset estático do Kaggle de 2018) carecem de variáveis técnicas que realmente explicam o churn em operadoras Tier-1 (latência, jitter, perda de pacotes, quedas de fibra ótica FTTH, instabilidade 5G).
3. **Omnichannel & Sentimento de Atendimento:**  
   Simulação probabilística de notas de CSAT, NPS e análise de sentimento de mensagens recebidas via WhatsApp e Call Center.

---

## 🔬 Atributos Gerados no Schema Telco 360 Enterprise

A base sintetizada expande o schema canônico para **40 atributos de alta fidelidade**:

| Categoria | Features Sintetizadas | Regra Causal de Domínio |
| :--- | :--- | :--- |
| **Identificação & Operadora** | `customerID`, `operator` (Vivo, Claro, TIM), `region_uf` (SP, RJ, MG, RS, etc.), `b2b_cnpj_flag` | Prefixo determinístico por tenant e distribuição geográfica ponderada por densidade populacional. |
| **Telemetria FTTH / 5G (QoE)** | `plan_speed_mbps`, `avg_download_speed_mbps`, `avg_latency_ms`, `packet_loss_pct_30d`, `fiber_outages_count_90d`, `modem_reboots_count_30d`, `technical_visit_count_12m` | Se `fiber_outages >= 3` e `packet_loss > 8%` $\to$ a probabilidade de cancelamento aumenta em $+35\%$. |
| **CRM & Sentimento Omnichannel** | `nps_score` (0-10), `csat_score` (1.0-5.0), `whatsapp_sentiment_score` (-1.0 a +1.0), `crm_tickets_opened_60d`, `anatel_complaint_flag` | Clientes com queda de rede frequente apresentam notas de NPS $< 5$ e sentimento no WhatsApp negativo ($-0.85$). |
| **Faturamento BRL & Financeiro** | `billing_disputes_count_12m`, `price_increase_pct_last_cycle`, `pix_payment_enabled`, `auto_debit_failures_count` | Falhas de débito automático e disputas de fatura aumentam o risco de churn imediato. |
| **Contrato Canônico (19 colunas)** | `gender`, `tenure`, `Contract`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges`, `Churn` | 100% compatível com o contrato de dados Pandera (`CustomerDataContract`). |

---

## 💻 Como Gerar Novas Bases

### 1. Pela Interface Gráfica (Cockpit UI):
- Clique no botão **`⚡ Sintetizar Base Telco 360`** na barra superior de dados.
- Escolha o volume desejado (**5.000**, **7.043**, **15.000** ou **25.000** clientes) e o nível de caos.

### 2. Via Endpoint REST da API:
```bash
curl -X POST http://localhost:8000/api/v1/admin/data/synthesize-enterprise-dataset \
  -H "Content-Type: application/json" \
  -d '{"num_samples": 10000, "chaos_ratio": 0.15, "save_as_default": true}'
```

### 3. Via Linha de Comando (CLI):
```bash
uv run python -m churn_prediction.data.generate_enterprise_dataset --num-samples 10000 --output data/raw/telco_enterprise_customers.csv
```

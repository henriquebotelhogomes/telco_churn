# Champion/Challenger & Shadow Scoring

A governança multi-modelo do RetainIQ permite avaliar algoritmos concorrentes em condições reais de tráfego de produção.

---

## 👥 Champion vs. Challengers

- **Champion:** O modelo ativo oficial que responde às requisições do produto na borda com SLA $< 10\text{ ms}$.
- **Challengers:** Modelos concorrentes treinados em paralelo, mantidos no `ModelManager`.

---

## ⚡ Telemetria de Shadow Scoring em Tempo Real

A cada inferência no Champion, uma tarefa assíncrona (`asyncio.create_task`) executa a predição nos Challengers sem onerar o tempo de resposta do cliente:

- **Taxa de Concordância:** Proporção de predições onde o Challenger classificou o risco na mesma categoria do Champion.
- **Δ Probabilidade Média:** Diferença absoluta média $|p_{\text{challenger}} - p_{\text{champion}}|$.
- **Latência de Inferência:** Tempo médio de cálculo de cada algoritmo.

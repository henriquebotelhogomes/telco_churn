# 📉 Telco Customer Churn Prediction - ML in Production

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![XGBoost](https://img.shields.io/badge/XGBoost-F37626?style=flat&logo=xgboost&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![uv](https://img.shields.io/badge/uv-Fast_Dependency_Manager-purple)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=github-actions&logoColor=white)

> **Mais do que um Jupyter Notebook:** Uma solução completa de Machine Learning orientada a produção, focada em Engenharia de Software, MLOps e impacto de negócio.

Este projeto resolve o problema de predição de cancelamento de clientes (Churn) utilizando dados de Telecom. O foco principal não é apenas treinar um modelo, mas demonstrar **como servir este modelo em um ambiente real**, com segurança, tipagem estrita, testes automatizados e containerização.

---

## 🌟 Por que este projeto se destaca? (Destaques Arquiteturais)

Para garantir que a aplicação seja escalável e de fácil manutenção, as seguintes decisões de Engenharia Sênior foram aplicadas:

1. **Padrão Adapter na API:** A API recebe requisições 100% em **Português** (facilitando a integração com o Front-end/Negócio local), mas utiliza o padrão *Adapter* no Pydantic para traduzir o payload em milissegundos para o formato original em Inglês esperado pelo modelo treinado.
2. **Pipeline Anti-Leakage:** O pré-processamento (imputação, encoding) não é feito solto em scripts. Ele está encapsulado em um `Pipeline` do *scikit-learn* junto com o modelo. A API aplica exatamente as mesmas transformações matemáticas dos dados de treino em tempo de inferência.
3. **Segurança no Docker (Non-Root):** O `Dockerfile` utiliza *multi-stage build* com cache de dependências e executa a aplicação sob um usuário sem privilégios de root (Princípio do Menor Privilégio).
4. **Tooling Moderno (State of the Art):** 
   - **`uv`**: Resolução e instalação de dependências em milissegundos.
   - **`Ruff` & `Mypy`**: Linting ultrarrápido e checagem de tipagem estática.
   - **`Pydantic V2`**: Validação de dados de entrada de alta performance.
5. **Foco em Métricas de Negócio:** O modelo XGBoost foi calibrado com `scale_pos_weight` para lidar com o desbalanceamento. A métrica otimizada foi o **Recall (0.67)**, pois em regras de negócio de Churn, o custo de um Falso Negativo (perder o cliente sem prever) é muito maior que um Falso Positivo.

---

## 📊 Performance do Modelo

Avaliação no conjunto de teste (20% dos dados invisíveis ao modelo):
- **ROC-AUC Score:** `0.82`
- **F1-Score (Churn):** `0.59`
- **Recall (Churn):** `0.67` 🎯 *(Métrica de negócio priorizada)*

---

## 🚀 Como Executar

### Opção 1: Via Docker (Recomendado para Produção)
```bash
# 1. Construa a imagem otimizada
docker build -t telco-churn-api .

# 2. Rode o container mapeando a porta 8000
docker run -p 8000:8000 telco-churn-api
```
### Opção 2: Ambiente Local (Desenvolvimento)
```
# 1. Instale o gerenciador uv (se não possuir)
pip install uv

# 2. Instale todas as dependências via Makefile
make install

# 3. Rode os testes automatizados (Pytest)
make test

# 4. Inicie a API localmente
make api
```

## 🌐 Consumindo a API
Com a API rodando, acesse a documentação interativa (Swagger UI) gerada automaticamente:
👉 http://localhost:8000/docs 

Ou faça uma requisição de teste via cURL (Payload validado estritamente em Português):
````
curl -X 'POST' \
  'http://localhost:8000/predict' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "genero": "Feminino",
  "idoso": 0,
  "tem_parceiro": "Sim",
  "tem_dependentes": "Não",
  "meses_permanencia": 1,
  "servico_telefone": "Não",
  "multiplas_linhas": "Sem serviço de telefone",
  "servico_internet": "DSL",
  "seguranca_online": "Não",
  "backup_online": "Sim",
  "protecao_dispositivo": "Não",
  "suporte_tecnico": "Não",
  "streaming_tv": "Não",
  "streaming_filmes": "Não",
  "contrato": "Mensal",
  "faturamento_sem_papel": "Sim",
  "metodo_pagamento": "Cheque eletrônico",
  "cobranca_mensal": 29.85,
  "cobranca_total": "29.85"
}'
````

## 📂 Estrutura do Projeto
````
.
├── .github/workflows/   # Pipeline de CI/CD (Lint, Types, Tests)
├── data/                # Dados brutos e processados (ignorados no git)
├── models/              # Artefatos do modelo treinado (.joblib)
├── src/
│   └── churn_prediction/
│       ├── api/         # FastAPI, Schemas (Pydantic V2) e rotas
│       ├── data/        # Scripts de pré-processamento (scikit-learn)
│       ├── models/      # Scripts de treinamento e avaliação
│       └── config.py    # Configurações globais (Pydantic Settings)
├── tests/               # Testes unitários e de integração (Pytest)
├── Dockerfile           # Configuração da imagem Docker (Non-root)
├── Makefile             # Atalhos para comandos comuns
└── pyproject.toml       # Configuração de dependências (uv) e ferramentas
````

Desenvolvido por Henrique Botelho Gomes - Engenheiro de Software Sênior & Especialista em IA.
# Guia de Início Rápido (Getting Started)

Este guia cobre o passo a passo para executar a plataforma RetainIQ localmente ou através de contêineres Docker.

---

## 🛠️ Pré-requisitos

- **Python 3.12+**
- **uv** (gerenciador de pacotes ultrarrápido recomendado) ou `pip`
- **Node.js 20+** e `npm` (para o frontend SPA)
- **Docker** (opcional, para execução unificada)

---

## 🚀 Opção 1: Execução com Docker (Recomendado)

A imagem multi-stage compila o frontend TypeScript e o embute no servidor assíncrono FastAPI em uma única porta (`8000`).

```bash
# 1. Construir a imagem Docker
docker build -t retainiq-platform .

# 2. Executar o contêiner
docker run -p 8000:8000 retainiq-platform
```

Acesse no navegador:
- **Cockpit Web RetainIQ:** [http://localhost:8000/](http://localhost:8000/)
- **Documentação Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Métricas Prometheus:** [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 💻 Opção 2: Desenvolvimento Local

### 1. Clonar e Instalar Dependências
```bash
git clone https://github.com/henriquebotelhogomes/telco_churn.git
cd telco_churn

# Instalar dependências Python via uv
uv sync

# Instalar dependências do Frontend
cd frontend
npm install
npm run build
cd ..
```

### 2. Treinar os Modelos Iniciais do Catálogo
```bash
uv run python -m churn_prediction.models.train
```

### 3. Iniciar o Backend FastAPI
```bash
uv run uvicorn churn_prediction.api.main:app --app-dir src --reload --port 8000
```

### 4. Iniciar o Frontend com Hot Reload (Opcional)
```bash
cd frontend
npm run dev
# Acesse em http://localhost:5173
```

---

## 🧪 Executando os Testes Automatizados

```bash
# Testes do Backend (com barreira de cobertura >= 80%)
uv run pytest tests/ -v --cov=churn_prediction --cov-fail-under=80

# Testes do Frontend
cd frontend && npm test
```

---

## 📖 Executando a Documentação MkDocs Localmente

```bash
# Iniciar servidor local de documentação
uv run mkdocs serve
# Acesse em http://127.0.0.1:8000/
```

# ==============================================================================
# 🛠️ Telco Churn Prediction - Makefile
# ==============================================================================

.PHONY: help install format lint test train api docker-build docker-run clean

# Comando padrão ao digitar apenas 'make'
.DEFAULT_GOAL := help

help: ## Mostra esta mensagem de ajuda com todos os comandos disponíveis
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Instala todas as dependências (produção e desenvolvimento) usando uv
	uv sync --all-extras

format: ## Formata o código e corrige imports automaticamente usando Ruff
	uv run ruff check --fix src tests
	uv run ruff format src tests

lint: ## Roda as checagens de qualidade (Ruff e Mypy) sem alterar os arquivos
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run mypy src

test: ## Executa os testes unitários e de integração com Pytest
	uv run pytest tests/ -v

train: ## Executa o pipeline de treinamento do modelo XGBoost
	uv run python src/churn_prediction/models/train.py

api: ## Inicia a API FastAPI localmente com hot-reload (Uvicorn)
	uv run uvicorn churn_prediction.api.main:app --reload --host 127.0.0.1 --port 8000

docker-build: ## Constrói a imagem Docker da aplicação
	docker build -t telco-churn-api .

docker-run: ## Executa o container Docker mapeando a porta 8000
	docker run -p 8000:8000 telco-churn-api

clean: ## Remove arquivos de cache do Python, Pytest, Ruff e Mypy
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
# ==============================================================================
# Stage 1: Build do Frontend (React + TypeScript + Vite)
# ==============================================================================
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Stage 2: Runtime Python (API FastAPI + Serving do Frontend)
# ==============================================================================
FROM python:3.12-slim

# Metadados da imagem
LABEL authors="Henrique Botelho Gomes"
LABEL description="RetainIQ - SaaS de Inteligência de Retenção de Clientes (Telco Churn)"
LABEL version="2.1.0"

# ==============================================================================
# Variáveis de Ambiente
# ==============================================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    UV_SYSTEM_PYTHON=1

# ==============================================================================
# Instalação do uv
# ==============================================================================
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ==============================================================================
# Configuração do Diretório e Usuário
# ==============================================================================
WORKDIR /app

RUN addgroup --system appgroup && adduser --system --group appuser

# ==============================================================================
# Dependências Python
# ==============================================================================
COPY pyproject.toml ./
RUN uv pip install -e .

# ==============================================================================
# Cópia do Código, Artefatos e Frontend Dist
# ==============================================================================
COPY src/ ./src/
COPY models/ ./models/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ajusta as permissões dos arquivos para o usuário não-root
RUN chown -R appuser:appgroup /app

# Muda para o usuário seguro
USER appuser

# ==============================================================================
# 7. Healthcheck (M0 - RetainIQ)
# ==============================================================================
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=2).getcode()==200 else 1)"

# ==============================================================================
# 8. Execução
# ==============================================================================
# Expõe a porta que o FastAPI vai utilizar
EXPOSE 8000

# Comando de inicialização usando o Uvicorn
CMD ["uvicorn", "churn_prediction.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
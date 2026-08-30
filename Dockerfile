# ==============================================================================
# 1. Imagem Base
# ==============================================================================
# Utilizamos a versão slim do Python 3.12 para reduzir a superfície de ataque
# e o tamanho final da imagem, mantendo as bibliotecas essenciais do SO.
FROM python:3.12-slim

# Metadados da imagem
LABEL authors="Henrique Botelho Gomes"
LABEL description="API de Machine Learning para predição de Churn (Telco)"
LABEL version="1.0.0"

# ==============================================================================
# 2. Variáveis de Ambiente
# ==============================================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src" \
    # Força o uv a instalar no ambiente global do container (ideal para Docker)
    UV_SYSTEM_PYTHON=1

# ==============================================================================
# 3. Instalação do gerenciador de pacotes (uv)
# ==============================================================================
# Copiamos o binário compilado do uv diretamente da imagem oficial.
# Essa é a forma mais rápida e limpa de instalar o uv no Docker.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ==============================================================================
# 4. Configuração do Diretório e Usuário
# ==============================================================================
WORKDIR /app

# Cria um usuário não-root por questões de segurança (Princípio do Menor Privilégio)
RUN addgroup --system appgroup && adduser --system --group appuser

# ==============================================================================
# 5. Instalação de Dependências (Cache Layer)
# ==============================================================================
# Copiamos apenas o arquivo de dependências primeiro.
# Isso garante que o Docker faça cache dessa camada, evitando reinstalar
# tudo a menos que o pyproject.toml seja alterado.
COPY pyproject.toml ./

# Instala as dependências de produção (sem as dependências de dev como pytest/ruff)
RUN uv pip install -e .

# ==============================================================================
# 6. Cópia do Código Fonte e Artefatos
# ==============================================================================
# Agora copiamos o código e o modelo treinado
COPY src/ ./src/
COPY models/ ./models/

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
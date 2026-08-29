from contextlib import asynccontextmanager
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from churn_prediction.api.schemas import PrevisaoChurnRequest, PrevisaoChurnResponse
from churn_prediction.config import settings

# Dicionário global para manter o modelo em memória.
# Evita o carregamento do disco a cada requisição, garantindo baixa latência.
ml_models: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da API.
    Carrega o modelo de ML na inicialização e o remove da memória no encerramento.
    """
    try:
        # Carrega o pipeline completo (pré-processamento + XGBoost)
        model = joblib.load(settings.model_path)
        ml_models["churn_model"] = model
        print(f"✅ Modelo carregado com sucesso de: {settings.model_path}")
    except Exception as e:
        print(f"❌ Erro ao carregar o modelo. Rode o treinamento primeiro. Detalhes: {e}")

    yield

    # Limpeza de recursos ao desligar a API
    ml_models.clear()


# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Telco Churn Prediction API",
    description="API de Machine Learning para predição de cancelamento de clientes",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def root():
    """
    Redireciona a rota raiz para a interface interativa do Swagger.
    """
    return RedirectResponse(url="/docs")


@app.post("/predict", response_model=PrevisaoChurnResponse)
def predict_churn(request: PrevisaoChurnRequest):
    """
    Recebe os dados de um cliente (em português), processa através do pipeline
    de Machine Learning e retorna a predição de Churn.
    """
    model = ml_models.get("churn_model")
    if not model:
        raise HTTPException(
            status_code=503,
            detail="Modelo não carregado. Verifique se o treinamento foi executado.",
        )

    # O padrão Adapter no schema converte o JSON em português para o dicionário
    # em inglês esperado pelo pipeline do scikit-learn.
    input_data = pd.DataFrame([request.to_model_input()])

    try:
        # predict() retorna a classe (0 ou 1)
        # predict_proba() retorna as probabilidades para cada classe [prob_0, prob_1]
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1]

        return PrevisaoChurnResponse(
            previsao_cancelamento=int(prediction),
            probabilidade_cancelamento=float(probability),
        )
    except Exception as e:
        # Captura erros de inferência (ex: dados faltantes não tratados)
        raise HTTPException(status_code=400, detail=f"Erro durante a predição: {str(e)}")


@app.get("/health")
def health_check():
    """
    Endpoint leve para monitoramento de saúde da aplicação (Liveness Probe).
    Ideal para orquestradores como Kubernetes ou Docker Swarm.
    """
    return {"status": "ok", "model_loaded": "churn_model" in ml_models}

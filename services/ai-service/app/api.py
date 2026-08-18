"""API REST de recomendaciones con IA (v1)."""

from fastapi import APIRouter

from .models import Recommendation, RecommendationRequest
from .recommender import recommend

router = APIRouter(prefix="/v1/ai", tags=["ai"])


@router.post("/recommendations", response_model=Recommendation)
async def get_recommendation(request: RecommendationRequest) -> Recommendation:
    """Recomienda ruta, tarifa y duración para un viaje (LLM con fallback heurístico)."""
    return await recommend(request)
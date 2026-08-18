"""Modelos del servicio de IA: recomendación de rutas y tarifas."""

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    passengers: int = Field(ge=1, le=10)


class Recommendation(BaseModel):
    origin: str
    destination: str
    route: str
    fare_clp: int
    duration_minutes: int
    provider: str
    model: str | None = None
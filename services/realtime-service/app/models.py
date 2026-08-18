"""Modelos del servicio de tiempo real (Socket.IO)."""

from pydantic import BaseModel, Field


class TripEventCreate(BaseModel):
    booking_id: str = Field(min_length=3)
    event: str = Field(pattern="^(driver_assigned|trip_started|location_update|trip_completed)$")
    payload: dict = Field(default_factory=dict)
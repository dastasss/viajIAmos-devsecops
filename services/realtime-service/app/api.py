"""API REST de tiempo real: permite publicar eventos de viaje (REST → Socket.IO)."""

from fastapi import APIRouter

from .models import TripEventCreate
from .socket_events import emit_trip_event

router = APIRouter(prefix="/v1/events", tags=["realtime"])


@router.post("/trips", status_code=202)
async def publish_trip_event(data: TripEventCreate) -> dict:
    """Publica un evento de viaje; los clientes suscritos lo reciben en tiempo real."""
    receivers = await emit_trip_event(data.booking_id, data.event, data.payload)
    return {"published": True, "event": data.event, "booking_id": data.booking_id, "receivers": receivers}
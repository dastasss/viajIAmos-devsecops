"""API REST de reservas (v1)."""

from fastapi import APIRouter, HTTPException

from .models import BookingCreate, Booking, StatusUpdate
from .store import store

router = APIRouter(prefix="/v1/bookings", tags=["bookings"])


@router.post("", response_model=Booking, status_code=201)
def create_booking(data: BookingCreate) -> Booking:
    """Crea una reserva de viaje."""
    return store.create(data)


@router.get("", response_model=list[Booking])
def list_bookings(limit: int = 20) -> list[Booking]:
    """Lista las reservas recientes."""
    return store.list(limit)


@router.get("/{booking_id}", response_model=Booking)
def get_booking(booking_id: str) -> Booking:
    """Obtiene una reserva por ID."""
    booking = store.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return booking


@router.patch("/{booking_id}/status", response_model=Booking)
def update_booking_status(booking_id: str, data: StatusUpdate) -> Booking:
    """Actualiza el estado de una reserva (pago, conductor asignado, etc.)."""
    booking = store.update_status(booking_id, data.status)
    if booking is None:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return booking
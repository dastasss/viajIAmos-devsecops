"""Almacenamiento en memoria (demo). En producción: PostgreSQL/Cloud SQL."""

import threading
import uuid
from typing import Optional

from .models import Booking, BookingCreate, BookingStatus


class BookingStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._bookings: dict[str, Booking] = {}

    def create(self, data: BookingCreate) -> Booking:
        booking_id = f"bk-{uuid.uuid4().hex[:12]}"
        booking = Booking.from_create(booking_id, data)
        with self._lock:
            self._bookings[booking_id] = booking
        return booking

    def get(self, booking_id: str) -> Optional[Booking]:
        with self._lock:
            return self._bookings.get(booking_id)

    def update_status(self, booking_id: str, status: BookingStatus) -> Optional[Booking]:
        with self._lock:
            booking = self._bookings.get(booking_id)
            if booking is None:
                return None
            booking.status = status
            return booking

    def list(self, limit: int = 20) -> list[Booking]:
        with self._lock:
            return list(self._bookings.values())[-limit:]


store = BookingStore()
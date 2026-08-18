"""Modelos de dominio del servicio de reservas."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class BookingStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    DRIVER_ASSIGNED = "driver_assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BookingCreate(BaseModel):
    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    passenger_name: str = Field(min_length=2, max_length=80)
    passengers: int = Field(ge=1, le=10)
    vehicle_type: str = Field(default="sedan", pattern="^(sedan|van|bus)$")


class Booking(BaseModel):
    id: str
    origin: str
    destination: str
    passenger_name: str
    passengers: int
    vehicle_type: str
    status: BookingStatus
    created_at: str

    @classmethod
    def from_create(cls, booking_id: str, data: BookingCreate) -> "Booking":
        return cls(
            id=booking_id,
            origin=data.origin,
            destination=data.destination,
            passenger_name=data.passenger_name,
            passengers=data.passengers,
            vehicle_type=data.vehicle_type,
            status=BookingStatus.CREATED,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class StatusUpdate(BaseModel):
    status: BookingStatus
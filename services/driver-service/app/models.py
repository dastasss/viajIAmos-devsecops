"""Modelos de dominio del servicio de conductores."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    booking_id: str = Field(min_length=3)
    driver_id: str = Field(min_length=3)


class Assignment(BaseModel):
    booking_id: str
    driver_id: str
    driver_name: str
    accepted_at: str
    eta_minutes: int

    @classmethod
    def from_create(cls, data: AssignmentCreate, driver_name: str, eta: int) -> "Assignment":
        return cls(
            booking_id=data.booking_id,
            driver_id=data.driver_id,
            driver_name=driver_name,
            accepted_at=datetime.now(timezone.utc).isoformat(),
            eta_minutes=eta,
        )


class DriverCreate(BaseModel):
    id: str = Field(min_length=3)
    name: str = Field(min_length=2)
    license_plate: str = Field(min_length=4, max_length=10)


class Driver(BaseModel):
    id: str
    name: str
    license_plate: str
    available: bool
    vehicle_type: str
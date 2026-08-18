"""Modelos de dominio del servicio de pagos."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    booking_id: str = Field(min_length=3)
    amount_clp: int = Field(gt=0, le=10_000_000)
    method: str = Field(default="card", pattern="^(card|transfer|wallet)$")


class Payment(BaseModel):
    id: str
    booking_id: str
    amount_clp: int
    method: str
    status: PaymentStatus
    created_at: str

    @classmethod
    def from_create(cls, payment_id: str, data: PaymentCreate) -> "Payment":
        return cls(
            id=payment_id,
            booking_id=data.booking_id,
            amount_clp=data.amount_clp,
            method=data.method,
            status=PaymentStatus.APPROVED,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
"""API REST de pagos (v1)."""

import logging

from fastapi import APIRouter, HTTPException

from .models import Payment, PaymentCreate
from .store import store

log = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/v1/payments", tags=["payments"])


@router.post("", response_model=Payment, status_code=201)
def create_payment(data: PaymentCreate) -> Payment:
    """Procesa un pago asociado a una reserva."""
    payment = store.create(data)
    log.info("Pago %s aprobado para booking %s (%d CLP)", payment.id, payment.booking_id, payment.amount_clp)
    return payment


@router.get("", response_model=list[Payment])
def list_payments(limit: int = 20) -> list[Payment]:
    return store.list(limit)


@router.get("/{payment_id}", response_model=Payment)
def get_payment(payment_id: str) -> Payment:
    payment = store.get(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return payment
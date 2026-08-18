"""Almacenamiento en memoria (demo). En producción: Cloud SQL / BigQuery para reportes."""

import threading
import uuid
from typing import Optional

from .models import Payment, PaymentCreate


class PaymentStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._payments: dict[str, Payment] = {}

    def create(self, data: PaymentCreate) -> Payment:
        payment_id = f"py-{uuid.uuid4().hex[:12]}"
        payment = Payment.from_create(payment_id, data)
        with self._lock:
            self._payments[payment_id] = payment
        return payment

    def get(self, payment_id: str) -> Optional[Payment]:
        with self._lock:
            return self._payments.get(payment_id)

    def list(self, limit: int = 20) -> list[Payment]:
        with self._lock:
            return list(self._payments.values())[-limit:]


store = PaymentStore()
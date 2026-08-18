"""Almacenamiento en memoria (demo)."""

import threading
from typing import Optional

from .models import Assignment, AssignmentCreate, Driver, DriverCreate


class DriverStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._drivers: dict[str, Driver] = {}
        self._assignments: list[Assignment] = []
        self._seed()

    def _seed(self) -> None:
        seed = [
            DriverCreate(id="drv-001", name="Carlos Muñoz", license_plate="ABC123"),
            DriverCreate(id="drv-002", name="María Fernández", license_plate="XYZ789"),
            DriverCreate(id="drv-003", name="José Rojas", license_plate="QWE456"),
        ]
        for d in seed:
            self._drivers[d.id] = Driver(
                id=d.id, name=d.name, license_plate=d.license_plate,
                available=True, vehicle_type="sedan",
            )

    def assign(self, data: AssignmentCreate) -> Optional[Assignment]:
        with self._lock:
            driver = self._drivers.get(data.driver_id)
            if driver is None or not driver.available:
                return None
            driver.available = False
            assignment = Assignment.from_create(data, driver.name, 10)
            self._assignments.append(assignment)
            return assignment

    def list_drivers(self) -> list[Driver]:
        with self._lock:
            return list(self._drivers.values())


store = DriverStore()
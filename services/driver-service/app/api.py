"""API REST de conductores (v1)."""

from fastapi import APIRouter, HTTPException

from .models import Assignment, AssignmentCreate, Driver
from .store import store

router = APIRouter(prefix="/v1/drivers", tags=["drivers"])


@router.post("/assign", response_model=Assignment, status_code=201)
def assign_driver(data: AssignmentCreate) -> Assignment:
    """Asigna un conductor disponible a una reserva (aceptación de conductor)."""
    assignment = store.assign(data)
    if assignment is None:
        raise HTTPException(status_code=409, detail="Conductor no disponible o no existe")
    return assignment


@router.get("", response_model=list[Driver])
def list_drivers() -> list[Driver]:
    return store.list_drivers()
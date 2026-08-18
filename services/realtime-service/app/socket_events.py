"""Emisión de eventos de viaje vía Socket.IO (espeja el monolito Socket.IO real).

En producción este servicio escala con un backend de mensajería (Redis pub/sub o
Google Pub/Sub) para que múltiples réplicas compartan el estado de los viajes.
"""

import logging
import threading

import socketio

log = logging.getLogger("uvicorn.error")

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

_rooms: dict[str, set[str]] = {}
_lock = threading.Lock()


def _add_to_room(room: str, sid: str) -> None:
    with _lock:
        _rooms.setdefault(room, set()).add(sid)


def _room_size(room: str) -> int:
    with _lock:
        return len(_rooms.get(room, set()))


def _cleanup(sid: str) -> None:
    with _lock:
        for members in _rooms.values():
            members.discard(sid)


@sio.event
async def connect(sid: str, environ: dict):
    """Un cliente (app móvil / dashboard) se conecta al canal de viajes."""
    log.info("Cliente conectado: %s", sid)


@sio.event
async def join_trip(sid: str, data: dict):
    """El cliente se suscribe a los eventos de un viaje concreto."""
    booking_id = data.get("booking_id")
    if not booking_id:
        await sio.emit("error", {"message": "booking_id requerido"}, to=sid)
        return
    await sio.enter_room(sid, booking_id)
    _add_to_room(booking_id, sid)
    await sio.emit("joined", {"booking_id": booking_id, "room_size": _room_size(booking_id)}, to=sid)


@sio.event
async def disconnect(sid: str):
    log.info("Cliente desconectado: %s", sid)
    _cleanup(sid)


async def emit_trip_event(booking_id: str, event: str, payload: dict) -> int:
    """Emita un evento a todos los suscriptores del viaje. Retorna la cantidad de clientes."""
    await sio.emit("trip.event", {"booking_id": booking_id, "event": event, "payload": payload}, to=booking_id)
    return _room_size(booking_id)
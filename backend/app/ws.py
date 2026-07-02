"""Live trip updates over WebSocket.

Clients connect to /ws?token=<jwt>. Whenever a trip they belong to changes
(status transition or driver location), they receive the serialized trip.
The mobile apps also poll REST as a fallback, so a dropped socket is safe.
"""
from fastapi import WebSocket
from sqlalchemy.orm import Session


class ConnectionManager:
    def __init__(self) -> None:
        self.sockets: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, socket: WebSocket) -> None:
        await socket.accept()
        self.sockets.setdefault(user_id, set()).add(socket)

    def disconnect(self, user_id: str, socket: WebSocket) -> None:
        self.sockets.get(user_id, set()).discard(socket)

    async def send(self, user_id: str, payload: dict) -> None:
        for socket in list(self.sockets.get(user_id, set())):
            try:
                await socket.send_json(payload)
            except Exception:
                self.disconnect(user_id, socket)


manager = ConnectionManager()


async def notify_trip(trip, db: Session) -> None:
    from .serializers import trip_dict

    payload = {"type": "trip", "trip": trip_dict(trip, db)}
    await manager.send(trip.rider_id, payload)
    if trip.driver_id:
        await manager.send(trip.driver_id, payload)

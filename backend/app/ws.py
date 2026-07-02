"""Live trip updates over WebSocket.

Clients connect to /ws?token=<jwt>. Whenever a trip they belong to changes
(status transition or driver location), they receive the serialized trip.
The mobile apps also poll REST as a fallback, so a dropped socket is safe.

With REDIS_URL set, events fan out through a Redis pub/sub channel so any
number of uvicorn workers (or hosts behind a load balancer) deliver to the
sockets they hold. Without it, delivery is direct and in-memory — correct
for a single process, which is how dev and the test-suite run.
"""
import asyncio
import json

from fastapi import WebSocket
from sqlalchemy.orm import Session

from . import config

CHANNEL = "taxi:trip-events"


class ConnectionManager:
    def __init__(self) -> None:
        self.sockets: dict[str, set[WebSocket]] = {}
        self._redis = None
        self._listener: asyncio.Task | None = None

    async def start(self) -> None:
        """Connect to Redis and subscribe to the event channel (no-op without REDIS_URL)."""
        if not config.REDIS_URL:
            return
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(config.REDIS_URL, decode_responses=True)
        self._listener = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._listener is not None:
            self._listener.cancel()
            self._listener = None
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None

    async def _listen(self) -> None:
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(CHANNEL)
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    try:
                        event = json.loads(message["data"])
                    except ValueError:
                        continue
                    for user_id in event.get("user_ids", []):
                        await self._deliver(user_id, event["payload"])
            except asyncio.CancelledError:
                raise
            except Exception:
                # Redis restarting (container update, power blip): keep retrying.
                # REST polling covers clients until the subscription is back.
                await asyncio.sleep(2)

    async def connect(self, user_id: str, socket: WebSocket) -> None:
        await socket.accept()
        self.sockets.setdefault(user_id, set()).add(socket)

    def disconnect(self, user_id: str, socket: WebSocket) -> None:
        self.sockets.get(user_id, set()).discard(socket)

    async def _deliver(self, user_id: str, payload: dict) -> None:
        for socket in list(self.sockets.get(user_id, set())):
            try:
                await socket.send_json(payload)
            except Exception:
                self.disconnect(user_id, socket)

    async def send(self, user_ids: list[str], payload: dict) -> None:
        if self._redis is not None:
            try:
                message = json.dumps({"user_ids": user_ids, "payload": payload})
                await self._redis.publish(CHANNEL, message)
                return
            except Exception:
                pass  # Redis down: local delivery below, REST polling covers other workers
        for user_id in user_ids:
            await self._deliver(user_id, payload)


manager = ConnectionManager()


async def notify_trip(trip, db: Session) -> None:
    from .serializers import trip_dict

    payload = {"type": "trip", "trip": trip_dict(trip, db)}
    recipients = [trip.rider_id]
    if trip.driver_id:
        recipients.append(trip.driver_id)
    await manager.send(recipients, payload)

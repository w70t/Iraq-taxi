from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from .db import Base, engine
from .routers import admin, auth, complaints, drivers, payments, trips
from .security import decode_token
from .ws import manager

# SQLite (dev and tests) gets its schema directly; PostgreSQL and anything
# else in production is managed by Alembic — run `alembic upgrade head`
# (the production compose stack does this automatically on startup).
if engine.dialect.name == "sqlite":
    Base.metadata.create_all(engine)
    # Lightweight patch for dev databases created before the commission column.
    with engine.begin() as connection:
        try:
            connection.execute(text("ALTER TABLE trips ADD COLUMN commission INTEGER DEFAULT 0"))
        except Exception:
            pass  # column already exists


@asynccontextmanager
async def lifespan(_: FastAPI):
    await manager.start()  # Redis fan-out when REDIS_URL is set, else no-op
    yield
    await manager.stop()


app = FastAPI(
    title="Taxi One Iraq API",
    version="0.3.0",
    description="Backend for the Taxi One Iraq rider and driver apps.",
    lifespan=lifespan,
)

app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(drivers.router)
app.include_router(payments.router)
app.include_router(complaints.router)


@app.get("/health")
def health():
    return {"ok": True}


@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket, token: str):
    try:
        payload = decode_token(token)
    except Exception:
        await socket.close(code=4401)
        return
    user_id = payload["sub"]
    await manager.connect(user_id, socket)
    try:
        while True:
            await socket.receive_text()  # keepalive pings from clients
    except WebSocketDisconnect:
        manager.disconnect(user_id, socket)

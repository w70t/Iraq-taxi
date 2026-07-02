from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .db import Base, engine
from .routers import auth, drivers, payments, trips
from .security import decode_token
from .ws import manager

Base.metadata.create_all(engine)

app = FastAPI(
    title="Taxi One Iraq API",
    version="0.2.0",
    description="Backend for the Taxi One Iraq rider and driver apps.",
)

app.include_router(auth.router)
app.include_router(trips.router)
app.include_router(drivers.router)
app.include_router(payments.router)


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

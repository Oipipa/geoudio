from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from app.db import get_session
from app.routers import events
from app.config import settings
import asyncio

class ConnectionManager:
    def __init__(self):
        self._clients = set()
        self._lock = asyncio.Lock()
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            self._clients.discard(websocket)
    async def broadcast(self, message: str):
        async with self._lock:
            clients = list(self._clients)
        dead = []
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._clients.discard(ws)

app = FastAPI()
app.state.manager = ConnectionManager()
app.mount("/audio", StaticFiles(directory=f"{settings.storage_root}/audio"), name="audio")
app.include_router(events.router)

@app.get("/health")
def health(db=Depends(get_session)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=503, detail="db_unavailable")

@app.websocket("/live")
async def live(ws: WebSocket):
    await app.state.manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await app.state.manager.disconnect(ws)
    except Exception:
        await app.state.manager.disconnect(ws)

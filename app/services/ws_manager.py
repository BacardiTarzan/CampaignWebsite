# app/services/ws_manager.py
import logging
from fastapi import WebSocket

log = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception as exc:
                log.debug("WS broadcast send failed (%s) — removing client", exc)
                dead.add(ws)
        self.active -= dead


manager = ConnectionManager()

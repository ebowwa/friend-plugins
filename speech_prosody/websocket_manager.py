# app/websocket_manager.py
from fastapi import WebSocket
from typing import Dict

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        del self.active_connections[session_id]

    async def send_json(self, session_id: str, data: dict):
        await self.active_connections[session_id].send_json(data)

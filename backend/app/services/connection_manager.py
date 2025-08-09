from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, poll_id: str, user_id: str):
        await websocket.accept()
        if poll_id not in self.active_connections:
            self.active_connections[poll_id] = {}
        self.active_connections[poll_id][user_id] = websocket
        print(f"User {user_id[:10]}... connected to poll {poll_id}")

    def disconnect(self, poll_id: str, user_id: str):
        if poll_id in self.active_connections and user_id in self.active_connections[poll_id]:
            del self.active_connections[poll_id][user_id]
            print(f"User {user_id[:10]}... disconnected from poll {poll_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_poll(self, message: str, poll_id: str):
        if poll_id in self.active_connections:
            for connection in self.active_connections[poll_id].values():
                await connection.send_text(message)

manager = ConnectionManager()

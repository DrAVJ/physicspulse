"""WebSocket Connection Manager for PhysicsPulse real-time sessions."""
from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # session_id -> {"teachers": [ws,...], "students": [ws,...]}
        self.rooms: Dict[int, Dict] = {}

    def get_room(self, session_id: int) -> Dict:
        if session_id not in self.rooms:
            self.rooms[session_id] = {"teachers": [], "students": []}
        return self.rooms[session_id]

    async def connect_teacher(self, session_id: int, ws: WebSocket):
        await ws.accept()
        room = self.get_room(session_id)
        room["teachers"].append(ws)
        logger.info(f"Teacher connected to session {session_id}")

    async def connect_student(self, session_id: int, ws: WebSocket):
        await ws.accept()
        room = self.get_room(session_id)
        room["students"].append(ws)
        logger.info(f"Student connected to session {session_id}")

    def disconnect_teacher(self, session_id: int, ws: WebSocket):
        room = self.get_room(session_id)
        if ws in room["teachers"]:
            room["teachers"].remove(ws)
        logger.info(f"Teacher disconnected from session {session_id}")

    def disconnect_student(self, session_id: int, ws: WebSocket):
        room = self.get_room(session_id)
        if ws in room["students"]:
            room["students"].remove(ws)
        logger.info(f"Student disconnected from session {session_id}")

    async def broadcast_to_students(self, session_id: int, message: dict):
        room = self.get_room(session_id)
        dead = []
        for ws in room["students"]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            room["students"].remove(ws)

    async def broadcast_to_teachers(self, session_id: int, message: dict):
        room = self.get_room(session_id)
        dead = []
        for ws in room["teachers"]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            room["teachers"].remove(ws)

    async def broadcast_to_all(self, session_id: int, message: dict):
        await self.broadcast_to_students(session_id, message)
        await self.broadcast_to_teachers(session_id, message)

    def student_count(self, session_id: int) -> int:
        return len(self.get_room(session_id)["students"])


# Global singleton
manager = ConnectionManager()

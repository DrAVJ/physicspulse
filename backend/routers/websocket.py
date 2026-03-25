from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..db.session import get_db
from ..db.models import Session, Answer, Question, Student
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        # session_id -> {"teachers": [ws,...], "students": {student_id: ws}}
        self.rooms: Dict[int, Dict] = {}

    def get_room(self, session_id: int) -> Dict:
        if session_id not in self.rooms:
            self.rooms[session_id] = {"teachers": [], "students": {}}
        return self.rooms[session_id]

    async def connect_teacher(self, session_id: int, ws: WebSocket):
        await ws.accept()
        room = self.get_room(session_id)
        room["teachers"].append(ws)
        logger.info(f"Teacher connected to session {session_id}")

    async def connect_student(self, session_id: int, student_id: int, ws: WebSocket):
        await ws.accept()
        room = self.get_room(session_id)
        room["students"][student_id] = ws
        logger.info(f"Student {student_id} connected to session {session_id}")

    def disconnect_teacher(self, session_id: int, ws: WebSocket):
        room = self.get_room(session_id)
        if ws in room["teachers"]:
            room["teachers"].remove(ws)

    def disconnect_student(self, session_id: int, student_id: int):
        room = self.get_room(session_id)
        room["students"].pop(student_id, None)

    async def broadcast_to_students(self, session_id: int, message: dict):
        room = self.get_room(session_id)
        disconnected = []
        for sid, ws in room["students"].items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(sid)
        for sid in disconnected:
            room["students"].pop(sid, None)

    async def broadcast_to_teachers(self, session_id: int, message: dict):
        room = self.get_room(session_id)
        disconnected = []
        for ws in room["teachers"]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            room["teachers"].remove(ws)

    async def broadcast_to_all(self, session_id: int, message: dict):
        await self.broadcast_to_students(session_id, message)
        await self.broadcast_to_teachers(session_id, message)

manager = ConnectionManager()

@router.websocket("/teacher/{session_id}")
async def teacher_ws(session_id: int, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await manager.connect_teacher(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "activate_question":
                question_id = data.get("question_id")
                q = await db.get(Question, question_id)
                if q:
                    await manager.broadcast_to_all(session_id, {
                        "type": "question_activated",
                        "question_id": question_id,
                        "question_text": q.question_text,
                        "options": q.options,
                        "timestamp_seconds": data.get("timestamp_seconds")
                    })
            elif msg_type == "close_question":
                # Fetch distribution and broadcast
                question_id = data.get("question_id")
                result = await db.execute(
                    select(Answer.chosen_index, func.count(Answer.id).label("count"))
                    .where(Answer.session_id == session_id, Answer.question_id == question_id)
                    .group_by(Answer.chosen_index)
                )
                rows = result.all()
                distribution = {row.chosen_index: row.count for row in rows}
                await manager.broadcast_to_all(session_id, {
                    "type": "question_closed",
                    "question_id": question_id,
                    "distribution": distribution
                })
            elif msg_type == "end_session":
                await manager.broadcast_to_all(session_id, {"type": "session_ended"})
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect_teacher(session_id, websocket)
        logger.info(f"Teacher disconnected from session {session_id}")

@router.websocket("/student/{session_id}/{student_id}")
async def student_ws(session_id: int, student_id: int, websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await manager.connect_student(session_id, student_id, websocket)
    # Notify teacher of new student
    student = await db.get(Student, student_id)
    if student:
        room = manager.get_room(session_id)
        student_count = len(room["students"])
        await manager.broadcast_to_teachers(session_id, {
            "type": "student_joined",
            "student_id": student_id,
            "nickname": student.nickname,
            "student_count": student_count
        })
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "answer_submitted":
                question_id = data.get("question_id")
                # Broadcast updated live stats to teacher
                result = await db.execute(
                    select(func.count(Answer.id))
                    .where(Answer.session_id == session_id, Answer.question_id == question_id)
                )
                count = result.scalar_one_or_none() or 0
                await manager.broadcast_to_teachers(session_id, {
                    "type": "answer_count_update",
                    "question_id": question_id,
                    "count": count
                })
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect_student(session_id, student_id)
        logger.info(f"Student {student_id} disconnected from session {session_id}")

def get_manager() -> ConnectionManager:
    return manager

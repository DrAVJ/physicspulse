from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ..db.session import get_db
from ..db.models import Session, Student, Question, Answer, Video, Teacher
from ..routers.auth import get_current_teacher
from ..services.websocket_manager import manager
import random
import string
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class SessionCreate(BaseModel):
    video_id: int
    class_name: Optional[str] = None


class SessionOut(BaseModel):
    id: int
    video_id: int
    join_code: str
    class_name: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class JoinRequest(BaseModel):
    join_code: str
    name: str


class StudentOut(BaseModel):
    id: int
    name: str
    session_id: int

    class Config:
        from_attributes = True


class ActivateQuestionRequest(BaseModel):
    question_id: int


def generate_join_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


@router.get("/", response_model=List[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Session).where(Session.teacher_id == current_teacher.id).order_by(Session.created_at.desc())
    )
    return result.scalars().all()


@router.post("/", response_model=SessionOut, status_code=201)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    # Verify video exists
    result = await db.execute(select(Video).where(Video.id == session_in.video_id, Video.teacher_id == current_teacher.id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Video not found")

    # Generate unique join code
    join_code = generate_join_code()
    while True:
        result = await db.execute(select(Session).where(Session.join_code == join_code))
        if not result.scalar_one_or_none():
            break
        join_code = generate_join_code()

    session = Session(
        video_id=session_in.video_id,
        teacher_id=current_teacher.id,
        join_code=join_code,
        class_name=session_in.class_name,
        status="waiting",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.post("/join", response_model=StudentOut)
async def join_session(
    join_req: JoinRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Session).where(Session.join_code == join_req.join_code.upper(), Session.status != "closed")
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or closed")

    student = Student(session_id=session.id, name=join_req.name)
    db.add(student)
    await db.flush()
    await db.refresh(student)
    return student


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.teacher_id == current_teacher.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/activate")
async def activate_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.teacher_id == current_teacher.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = "active"
    await db.flush()
    await manager.broadcast_to_session(session_id, {"type": "session_started"})
    return {"status": "active"}


@router.post("/{session_id}/questions/activate")
async def activate_question(
    session_id: int,
    req: ActivateQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.teacher_id == current_teacher.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(select(Question).where(Question.id == req.question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    session.current_question_id = req.question_id
    await db.flush()

    await manager.broadcast_to_session(session_id, {
        "type": "question_activated",
        "question": {
            "id": question.id,
            "text": question.text,
            "options": question.options,
            "time_anchor_sec": question.time_anchor_sec,
        }
    })
    return {"status": "activated", "question_id": question.id}


@router.post("/{session_id}/close")
async def close_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.teacher_id == current_teacher.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.status = "closed"
    session.closed_at = datetime.utcnow()
    await db.flush()
    await manager.broadcast_to_session(session_id, {"type": "session_closed"})
    return {"status": "closed"}


@router.get("/{session_id}/results")
async def get_session_results(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.teacher_id == current_teacher.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all questions for this session's video
    q_result = await db.execute(
        select(Question).where(Question.video_id == session.video_id).order_by(Question.order_index)
    )
    questions = q_result.scalars().all()

    # Get all answers
    a_result = await db.execute(select(Answer).where(Answer.session_id == session_id))
    answers = a_result.scalars().all()

    # Aggregate per question
    question_stats = []
    for q in questions:
        q_answers = [a for a in answers if a.question_id == q.id]
        correct = sum(1 for a in q_answers if a.is_correct)
        total = len(q_answers)
        option_counts = {}
        for a in q_answers:
            option_counts[a.chosen_index] = option_counts.get(a.chosen_index, 0) + 1
        question_stats.append({
            "question_id": q.id,
            "text": q.text,
            "concept_tag": q.concept_tag,
            "correct": correct,
            "total": total,
            "pct_correct": round(correct / total * 100) if total > 0 else 0,
            "option_distribution": option_counts,
        })

    # Student results
    s_result = await db.execute(select(Student).where(Student.session_id == session_id))
    students = s_result.scalars().all()

    student_results = []
    for s in students:
        s_answers = [a for a in answers if a.student_id == s.id]
        correct = sum(1 for a in s_answers if a.is_correct)
        student_results.append({
            "student_id": s.id,
            "name": s.name,
            "correct": correct,
            "total": len(s_answers),
            "pct": round(correct / len(s_answers) * 100) if s_answers else 0,
        })

    return {
        "session_id": session_id,
        "video_id": session.video_id,
        "join_code": session.join_code,
        "class_name": session.class_name,
        "total_students": len(students),
        "question_stats": question_stats,
        "student_results": student_results,
    }


@router.get("/{session_id}/questions/{question_id}/stats")
async def get_question_realtime_stats(
    session_id: int,
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Answer).where(
        Answer.session_id == session_id,
        Answer.question_id == question_id,
    ))
    answers = result.scalars().all()

    result2 = await db.execute(select(Question).where(Question.id == question_id))
    question = result2.scalar_one_or_none()

    option_counts = {}
    for a in answers:
        option_counts[a.chosen_index] = option_counts.get(a.chosen_index, 0) + 1

    return {
        "question_id": question_id,
        "total_answers": len(answers),
        "correct_index": question.correct_index if question else None,
        "option_distribution": option_counts,
    }

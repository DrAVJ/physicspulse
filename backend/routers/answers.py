from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from pydantic import BaseModel
from ..db.session import get_db
from ..db.models import Answer, Session, Question, Student
from ..auth import get_current_teacher
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class AnswerCreate(BaseModel):
    student_id: int
    session_id: int
    question_id: int
    chosen_index: int

class AnswerOut(BaseModel):
    id: int
    student_id: int
    session_id: int
    question_id: int
    chosen_index: int
    is_correct: bool

    class Config:
        from_attributes = True

@router.post("/", response_model=AnswerOut)
async def submit_answer(
    payload: AnswerCreate,
    db: AsyncSession = Depends(get_db)
):
    # Verify session is active
    sess = await db.get(Session, payload.session_id)
    if not sess or sess.status != "active":
        raise HTTPException(status_code=400, detail="Session not active")
    # Verify question belongs to session and is active
    q = await db.get(Question, payload.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    # Check for duplicate
    existing = await db.execute(
        select(Answer).where(
            Answer.student_id == payload.student_id,
            Answer.session_id == payload.session_id,
            Answer.question_id == payload.question_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Answer already submitted")
    is_correct = payload.chosen_index == q.correct_index
    answer = Answer(
        student_id=payload.student_id,
        session_id=payload.session_id,
        question_id=payload.question_id,
        chosen_index=payload.chosen_index,
        is_correct=is_correct
    )
    db.add(answer)
    await db.commit()
    await db.refresh(answer)
    logger.info(f"Answer submitted: student={payload.student_id} q={payload.question_id} correct={is_correct}")
    return answer

@router.get("/session/{session_id}", response_model=List[AnswerOut])
async def get_session_answers(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    result = await db.execute(
        select(Answer).where(Answer.session_id == session_id)
    )
    return result.scalars().all()

@router.get("/session/{session_id}/question/{question_id}/distribution")
async def get_answer_distribution(
    session_id: int,
    question_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    q = await db.get(Question, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    result = await db.execute(
        select(Answer.chosen_index, func.count(Answer.id).label("count"))
        .where(Answer.session_id == session_id, Answer.question_id == question_id)
        .group_by(Answer.chosen_index)
    )
    rows = result.all()
    distribution = {row.chosen_index: row.count for row in rows}
    total = sum(distribution.values())
    options = q.options if q.options else []
    return {
        "question_id": question_id,
        "question_text": q.question_text,
        "correct_index": q.correct_index,
        "options": options,
        "distribution": distribution,
        "total_answers": total
    }

@router.get("/student/{student_id}/session/{session_id}", response_model=List[AnswerOut])
async def get_student_answers(
    student_id: int,
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Answer).where(
            Answer.student_id == student_id,
            Answer.session_id == session_id
        )
    )
    return result.scalars().all()

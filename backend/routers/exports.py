from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.session import get_db
from ..db.models import Session, Answer, Question, Student, Video
from ..auth import get_current_teacher
import csv
import json
import io
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_session_data(session_id: int, db: AsyncSession):
    sess = await db.get(Session, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    answers_result = await db.execute(
        select(Answer).where(Answer.session_id == session_id)
    )
    answers = answers_result.scalars().all()
    return sess, answers

@router.get("/session/{session_id}/csv")
async def export_session_csv(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    sess, answers = await get_session_data(session_id, db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["answer_id", "student_id", "session_id", "question_id", "chosen_index", "is_correct"])
    for a in answers:
        writer.writerow([a.id, a.student_id, a.session_id, a.question_id, a.chosen_index, a.is_correct])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}_answers.csv"}
    )

@router.get("/session/{session_id}/json")
async def export_session_json(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    sess, answers = await get_session_data(session_id, db)
    # Get questions for context
    questions_result = await db.execute(
        select(Question).where(Question.video_id == sess.video_id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}
    # Get students
    students_result = await db.execute(
        select(Student).where(Student.session_id == session_id)
    )
    students = {s.id: s for s in students_result.scalars().all()}
    data = {
        "session_id": sess.id,
        "video_id": sess.video_id,
        "join_code": sess.join_code,
        "status": sess.status,
        "total_students": len(students),
        "answers": [
            {
                "id": a.id,
                "student_id": a.student_id,
                "student_nickname": students.get(a.student_id, {}).nickname if a.student_id in students else None,
                "question_id": a.question_id,
                "question_text": questions[a.question_id].question_text if a.question_id in questions else None,
                "chosen_index": a.chosen_index,
                "is_correct": a.is_correct
            }
            for a in answers
        ]
    }
    return data

@router.get("/session/{session_id}/summary")
async def export_session_summary(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    """Per-question summary with option distribution and correct rate"""
    sess, answers = await get_session_data(session_id, db)
    questions_result = await db.execute(
        select(Question).where(Question.video_id == sess.video_id)
    )
    questions = questions_result.scalars().all()
    summary = []
    for q in questions:
        q_answers = [a for a in answers if a.question_id == q.id]
        total = len(q_answers)
        correct = sum(1 for a in q_answers if a.is_correct)
        distribution = {}
        for a in q_answers:
            distribution[a.chosen_index] = distribution.get(a.chosen_index, 0) + 1
        summary.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "concept_tag": q.concept_tag,
            "correct_index": q.correct_index,
            "total_answers": total,
            "correct_answers": correct,
            "correct_rate": round(correct / total, 3) if total > 0 else None,
            "distribution": distribution
        })
    return {"session_id": session_id, "questions": summary}

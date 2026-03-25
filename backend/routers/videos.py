from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from ..db.session import get_db
from ..db.models import Video, VideoConcept, ConceptMisconception, Question, Teacher
from ..routers.auth import get_current_teacher
from ..config import settings
import aiofiles
import os
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class VideoCreate(BaseModel):
    title: str
    youtube_id: Optional[str] = None


class VideoOut(BaseModel):
    id: int
    title: str
    youtube_id: Optional[str]
    file_path: Optional[str]
    duration_sec: Optional[int]
    status: str

    class Config:
        from_attributes = True


class ConceptOut(BaseModel):
    id: int
    concept: str
    time_sec: Optional[int]
    confidence: Optional[float]

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    id: int
    text: str
    options: list
    correct_index: int
    time_anchor_sec: Optional[int]
    concept_tag: Optional[str]
    order_index: int

    class Config:
        from_attributes = True


@router.get("/", response_model=List[VideoOut])
async def list_videos(
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Video).where(Video.teacher_id == current_teacher.id))
    return result.scalars().all()


@router.post("/", response_model=VideoOut, status_code=201)
async def create_video(
    video_in: VideoCreate,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    video = Video(
        teacher_id=current_teacher.id,
        title=video_in.title,
        youtube_id=video_in.youtube_id,
        status="draft",
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return video


@router.post("/upload", response_model=VideoOut, status_code=201)
async def upload_video(
    title: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, filename)

    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    video = Video(
        teacher_id=current_teacher.id,
        title=title,
        file_path=file_path,
        status="draft",
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return video


@router.get("/{video_id}", response_model=VideoOut)
async def get_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.teacher_id == current_teacher.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.post("/{video_id}/transcribe")
async def transcribe_video(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.teacher_id == current_teacher.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video.status = "transcribing"
    await db.flush()

    from ..services.ai_transcription import run_transcription
    background_tasks.add_task(run_transcription, video_id)

    return {"job_id": f"transcribe_{video_id}", "status": "queued"}


@router.post("/{video_id}/concept-detection")
async def detect_concepts(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.teacher_id == current_teacher.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    from ..services.ai_llm import detect_concepts_from_transcript
    background_tasks.add_task(detect_concepts_from_transcript, video_id)

    return {"status": "queued"}


@router.post("/{video_id}/generate-questions")
async def generate_questions(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(Video).where(Video.id == video_id, Video.teacher_id == current_teacher.id))
    video = result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    from ..services.ai_llm import generate_questions_for_video
    background_tasks.add_task(generate_questions_for_video, video_id)

    return {"status": "queued"}


@router.get("/{video_id}/concepts", response_model=List[ConceptOut])
async def get_concepts(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(select(VideoConcept).where(VideoConcept.video_id == video_id))
    return result.scalars().all()


@router.get("/{video_id}/questions", response_model=List[QuestionOut])
async def get_questions(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    result = await db.execute(
        select(Question).where(Question.video_id == video_id).order_by(Question.order_index)
    )
    return result.scalars().all()

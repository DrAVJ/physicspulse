"""AI LLM service - concept detection, misconception mapping, question generation."""
import logging
from sqlalchemy import select
from ..db.session import AsyncSessionLocal
from ..db.models import Video, VideoConcept, ConceptMisconception, Question
from .ai_service import detect_concepts, map_misconceptions, generate_questions

logger = logging.getLogger(__name__)


async def detect_concepts_from_transcript(video_id: int):
    """Background task: detect physics concepts from transcript using LLM."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video or not video.transcript:
                logger.error(f"Video {video_id} has no transcript")
                return

            logger.info(f"Detecting concepts for video {video_id}")
            concepts_data = await detect_concepts(video.transcript)

            # Remove existing concepts
            existing = await db.execute(
                select(VideoConcept).where(VideoConcept.video_id == video_id)
            )
            for c in existing.scalars().all():
                await db.delete(c)

            # Insert new concepts
            for item in concepts_data:
                concept = VideoConcept(
                    video_id=video_id,
                    concept=item.get("concept", ""),
                    time_sec=item.get("time_sec"),
                    confidence=item.get("confidence", 0.8),
                )
                db.add(concept)
                await db.flush()

                # Map misconceptions for each concept
                misconceptions = await map_misconceptions(item.get("concept", ""))
                for m in misconceptions:
                    mc = ConceptMisconception(
                        concept_id=concept.id,
                        title=m.get("title", ""),
                        description=m.get("description", ""),
                        source=m.get("source", "PER knowledge base"),
                        is_active=True,
                    )
                    db.add(mc)

            await db.commit()
            logger.info(f"Concept detection complete for video {video_id}: {len(concepts_data)} concepts")

        except Exception as e:
            logger.exception(f"Concept detection failed for video {video_id}: {e}")


async def generate_questions_for_video(video_id: int):
    """Background task: generate MCQ questions from concepts using LLM."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video or not video.transcript:
                logger.error(f"Video {video_id} has no transcript")
                return

            # Get concepts for context
            concept_result = await db.execute(
                select(VideoConcept).where(VideoConcept.video_id == video_id)
            )
            concepts = concept_result.scalars().all()
            concept_list = [c.concept for c in concepts]

            logger.info(f"Generating questions for video {video_id}")
            questions_data = await generate_questions(video.transcript, concept_list)

            # Remove existing questions
            existing_q = await db.execute(
                select(Question).where(Question.video_id == video_id)
            )
            for q in existing_q.scalars().all():
                await db.delete(q)

            # Insert new questions
            for idx, q_data in enumerate(questions_data):
                question = Question(
                    video_id=video_id,
                    text=q_data.get("text", ""),
                    options=q_data.get("options", []),
                    correct_index=q_data.get("correct_index", 0),
                    time_anchor_sec=q_data.get("time_anchor_sec"),
                    concept_tag=q_data.get("concept_tag", ""),
                    misconception_tag=q_data.get("misconception_tag", ""),
                    order_index=idx,
                )
                db.add(question)

            video.status = "ready"
            await db.commit()
            logger.info(f"Question generation complete for video {video_id}: {len(questions_data)} questions")

        except Exception as e:
            logger.exception(f"Question generation failed for video {video_id}: {e}")

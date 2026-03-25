"""AI Transcription service - wraps ai_service.transcribe_audio/youtube for background tasks."""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.session import AsyncSessionLocal
from ..db.models import Video
from .ai_service import transcribe_audio, transcribe_youtube_url

logger = logging.getLogger(__name__)


async def run_transcription(video_id: int):
    """Background task: transcribe video and save transcript to DB."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                logger.error(f"Video {video_id} not found for transcription")
                return

            video.status = "transcribing"
            await db.commit()

            transcript_data = None
            if video.youtube_id:
                logger.info(f"Transcribing YouTube video {video.youtube_id}")
                transcript_data = await transcribe_youtube_url(
                    f"https://www.youtube.com/watch?v={video.youtube_id}"
                )
            elif video.file_path:
                logger.info(f"Transcribing uploaded file {video.file_path}")
                transcript_data = await transcribe_audio(video.file_path)
            else:
                logger.error(f"Video {video_id} has neither youtube_id nor file_path")
                video.status = "error"
                await db.commit()
                return

            # Store transcript text
            if transcript_data and "text" in transcript_data:
                video.transcript = transcript_data["text"]
                if transcript_data.get("duration"):
                    video.duration_sec = int(transcript_data["duration"])
                video.status = "processing"
                logger.info(f"Transcription complete for video {video_id}, status -> processing")
            else:
                video.status = "error"
                logger.error(f"Transcription returned no text for video {video_id}")

            await db.commit()

        except Exception as e:
            logger.exception(f"Transcription failed for video {video_id}: {e}")
            try:
                result = await db.execute(select(Video).where(Video.id == video_id))
                video = result.scalar_one_or_none()
                if video:
                    video.status = "error"
                    await db.commit()
            except Exception:
                pass

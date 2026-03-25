from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.session import get_db
from ..db.models import Session, Answer, Question, Video, VideoConcept, ConceptMisconception
from ..auth import get_current_teacher
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# PER knowledge base for pedagogical recommendations
PER_KNOWLEDGE_BASE = """
Physics Education Research (PER) based strategies:
1. Misconception-targeted instruction: When students systematically choose wrong answers,
   address the underlying misconception directly with targeted examples.
2. Peer instruction (Mazur): Use think-pair-share around conceptual questions.
3. Interactive engagement: Replace passive lecture with active problem solving.
4. Formative assessment: Use real-time quiz data to adapt instruction.
5. Conceptual change: Confront misconceptions explicitly, show why they fail.
6. Multiple representations: Use graphs, equations, diagrams, and analogies together.
7. Worked examples: Show correct reasoning process step-by-step.
8. Scaffolding: Break complex concepts into smaller building blocks.
"""

async def build_recommendation_prompt(
    session_id: int,
    db: AsyncSession
) -> str:
    sess = await db.get(Session, session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    
    answers_result = await db.execute(
        select(Answer).where(Answer.session_id == session_id)
    )
    answers = answers_result.scalars().all()
    
    questions_result = await db.execute(
        select(Question).where(Question.video_id == sess.video_id)
    )
    questions = {q.id: q for q in questions_result.scalars().all()}
    
    # Build per-question analysis
    analysis_lines = []
    for qid, q in questions.items():
        q_answers = [a for a in answers if a.question_id == qid]
        total = len(q_answers)
        if total == 0:
            continue
        correct = sum(1 for a in q_answers if a.is_correct)
        correct_rate = correct / total
        distribution = {}
        for a in q_answers:
            distribution[a.chosen_index] = distribution.get(a.chosen_index, 0) + 1
        
        # Find dominant wrong answer
        wrong_dist = {k: v for k, v in distribution.items() if k != q.correct_index}
        dominant_wrong = max(wrong_dist, key=wrong_dist.get) if wrong_dist else None
        dominant_wrong_pct = (wrong_dist[dominant_wrong] / total * 100) if dominant_wrong is not None else 0
        
        analysis_lines.append(
            f"Q: {q.question_text}\n"
            f"  Concept: {q.concept_tag or 'general'}\n"
            f"  Correct rate: {correct_rate:.0%} ({correct}/{total})\n"
            f"  Most common wrong answer: option {dominant_wrong} ({dominant_wrong_pct:.0f}% of students)\n"
            f"  Correct answer: option {q.correct_index}\n"
            f"  Options: {q.options}\n"
        )
    
    analysis = "\n".join(analysis_lines)
    prompt = f"""You are a physics education expert. Analyze these student response data from a live session and generate specific, actionable pedagogical recommendations grounded in Physics Education Research (PER).

{PER_KNOWLEDGE_BASE}

Session results:
{analysis}

Provide:
1. Top 3 most urgent misconceptions to address (with specific student evidence)
2. Concrete instructional strategies for each misconception
3. Suggested follow-up questions or activities
4. Overall class readiness assessment for the next topic

Be specific and reference the actual student data."""
    return prompt

@router.get("/session/{session_id}")
async def get_recommendations(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    prompt = await build_recommendation_prompt(session_id, db)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        # Return mock recommendations if no API key
        return {
            "session_id": session_id,
            "recommendations": "[OpenAI API key not configured. Add OPENAI_API_KEY to enable AI recommendations.]",
            "prompt_preview": prompt[:500]
        }
    
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=openai_key)
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a physics education research expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        recommendations = response.choices[0].message.content
        return {
            "session_id": session_id,
            "recommendations": recommendations,
            "model": "gpt-4o"
        }
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")

@router.get("/video/{video_id}/misconceptions")
async def get_video_misconceptions(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    teacher=Depends(get_current_teacher)
):
    concepts_result = await db.execute(
        select(VideoConcept).where(VideoConcept.video_id == video_id)
    )
    concepts = concepts_result.scalars().all()
    result = []
    for concept in concepts:
        misconceptions_result = await db.execute(
            select(ConceptMisconception).where(ConceptMisconception.concept_id == concept.id)
        )
        misconceptions = misconceptions_result.scalars().all()
        result.append({
            "concept_id": concept.id,
            "concept_name": concept.concept_name,
            "timestamp_seconds": concept.timestamp_seconds,
            "misconceptions": [
                {"id": m.id, "description": m.description, "source": m.source}
                for m in misconceptions
            ]
        })
    return result

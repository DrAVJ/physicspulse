"""AI Service: Whisper transcription and GPT-4o concept/question generation"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def get_openai_client():
    import openai
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return openai.AsyncOpenAI(api_key=api_key)

async def transcribe_audio(file_path: str) -> dict:
    """Transcribe audio using OpenAI Whisper v3 with timestamps"""
    client = get_openai_client()
    with open(file_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    segments = []
    if hasattr(response, 'segments') and response.segments:
        for seg in response.segments:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text
            })
    return {
        "text": response.text,
        "segments": segments,
        "language": getattr(response, 'language', 'unknown')
    }

async def detect_concepts(transcript: str, video_title: str = "") -> List[dict]:
    """Use GPT-4o to detect physics concepts and their timestamps"""
    client = get_openai_client()
    prompt = f"""You are a physics education expert. Analyze this transcript from a physics lecture video titled "{video_title}".

Transcript:
{transcript[:4000]}

Identify the main physics concepts covered. For each concept provide:
- concept_name: The physics concept name
- description: Brief description (1-2 sentences)
- keywords: List of key terms associated with this concept
- estimated_position: rough position in text (beginning/middle/end)

Respond as a JSON array of objects with keys: concept_name, description, keywords, estimated_position"""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=1000,
        temperature=0.2
    )
    import json
    result = json.loads(response.choices[0].message.content)
    concepts = result.get("concepts", result) if isinstance(result, dict) else result
    return concepts if isinstance(concepts, list) else []

async def map_misconceptions(concept_name: str) -> List[dict]:
    """Use GPT-4o to find common misconceptions for a physics concept from FCIFMCE database"""
    client = get_openai_client()
    prompt = f"""You are a physics education researcher familiar with Force Concept Inventory (FCI), Force and Motion Conceptual Evaluation (FMCE), and other PER assessment tools.

For the physics concept "{concept_name}", list the 3-5 most common student misconceptions documented in physics education research.

For each misconception provide:
- description: The misconception statement
- source: PER source (e.g., FCI, FMCE, Hestenes 1992, etc.)
- correct_understanding: The scientifically correct understanding
- typical_prevalence: percentage of students who hold this misconception (if known)

Respond as JSON with key "misconceptions" containing an array."""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=800,
        temperature=0.2
    )
    import json
    result = json.loads(response.choices[0].message.content)
    return result.get("misconceptions", [])

async def generate_questions(
    concept_name: str,
    misconceptions: List[str],
    transcript_excerpt: str = "",
    num_questions: int = 3
) -> List[dict]:
    """Generate MCQ questions targeting specific misconceptions"""
    client = get_openai_client()
    misconception_text = "\n".join(f"- {m}" for m in misconceptions[:3])
    prompt = f"""You are a physics education expert creating formative assessment questions.

Concept: {concept_name}
Common misconceptions to target:
{misconception_text}

Context from lecture:
{transcript_excerpt[:500]}

Create {num_questions} multiple-choice questions (4 options each) that:
1. Test understanding of {concept_name}
2. Have distractors based on the listed misconceptions
3. Are at an introductory university physics level
4. Are clearly worded

Respond as JSON with key "questions" containing array of:
{{
  "question_text": "...",
  "options": ["A...", "B...", "C...", "D..."],
  "correct_index": 0,
  "explanation": "Why the correct answer is right",
  "misconception_targeted": "Which misconception this targets",
  "concept_tag": "{concept_name}"
}}"""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=1500,
        temperature=0.4
    )
    import json
    result = json.loads(response.choices[0].message.content)
    return result.get("questions", [])

async def transcribe_youtube_url(youtube_url: str) -> dict:
    """Download audio from YouTube and transcribe (requires yt-dlp)"""
    import subprocess
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")
        # Download audio using yt-dlp
        result = subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_path, youtube_url],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            raise ValueError(f"yt-dlp failed: {result.stderr}")
        return await transcribe_audio(audio_path)

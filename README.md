# PhysicsPulse

Video-based formative assessment platform for physics teachers.

## Overview

PhysicsPulse enables teachers to upload or link physics videos, automatically transcribe them, detect concepts, generate multiple-choice questions using AI, and run live interactive sessions where students join via a code and answer questions in real time.

## Architecture

- **Backend**: FastAPI + PostgreSQL (async via SQLAlchemy + asyncpg)
- **Frontend**: React 18 + TypeScript + Vite
- **Realtime**: WebSocket (teacher broadcast + student receive)
- **AI**: OpenAI API for transcription, concept detection, and question generation
- **Infrastructure**: Docker Compose

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Run with Docker Compose

```bash
cp .env.example .env
# Edit .env and add OPENAI_API_KEY
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Local Development

**Backend**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

## E2E Flow

1. Teacher registers and logs in
2. Teacher creates a video entry (YouTube URL or upload)
3. Backend transcribes audio via Whisper
4. AI detects physics concepts and generates MCQ questions
5. Teacher creates a session and shares join code
6. Students join at `/join` with the code
7. Teacher activates questions one at a time via TeacherPlayer
8. Students answer in real time via WebSocket
9. Teacher sees live answer distribution and percentage correct
10. After session: full results, AI-generated recommendations
11. Export results as CSV or JSON

## Project Structure

```
physicspulse/
  backend/
    db/            # SQLAlchemy models and session
    routers/       # FastAPI routers (auth, videos, sessions, answers, exports, ai, websocket)
    services/      # WebSocket manager, AI transcription, LLM service
    tests/         # pytest async tests
    main.py        # FastAPI app
    Dockerfile
  frontend/
    src/
      components/  # Layout
      hooks/       # useAuth, useSessionSocket
      pages/       # teacher/, student/, auth/
      services/    # api.ts
    Dockerfile
  docker-compose.yml
  docs/
    TODO.md
```

## Testing

**Backend**
```bash
cd backend
pip install pytest pytest-asyncio httpx aiosqlite
pytest tests/ -v
```

**Frontend**
```bash
cd frontend
npm test
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | - | PostgreSQL connection string |
| OPENAI_API_KEY | - | OpenAI API key for AI features |
| SECRET_KEY | supersecretkey | JWT signing key |
| ALGORITHM | HS256 | JWT algorithm |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1440 | Token validity (24h) |
| CORS_ORIGINS | localhost:5173,localhost:3000 | Allowed origins |

## License

MIT

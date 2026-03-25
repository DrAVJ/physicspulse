from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .db.session import engine, Base
from .routers import auth, videos, sessions, answers, ai, websocket, exports
from .config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("PhysicsPulse API started")
    yield
    logger.info("PhysicsPulse API shutdown")


app = FastAPI(
    title="PhysicsPulse API",
    version="1.0.0",
    description="Video-based pedagogical tool for physics teachers",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(videos.router, prefix="/videos", tags=["videos"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(answers.router, prefix="/answers", tags=["answers"])
app.include_router(ai.router, prefix="/ai", tags=["ai"])
app.include_router(exports.router, prefix="/exports", tags=["exports"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

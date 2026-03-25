from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from ..db.session import get_db
from ..db.models import Teacher
from ..config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TeacherCreate(BaseModel):
    email: str
    password: str
    name: str


class TeacherOut(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_teacher(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Teacher:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        teacher_id: int = payload.get("sub")
        if teacher_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Teacher).where(Teacher.id == int(teacher_id)))
    teacher = result.scalar_one_or_none()
    if teacher is None:
        raise credentials_exception
    return teacher


@router.post("/register", response_model=TeacherOut, status_code=201)
async def register(teacher_in: TeacherCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Teacher).where(Teacher.email == teacher_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    teacher = Teacher(
        email=teacher_in.email,
        hashed_password=get_password_hash(teacher_in.password),
        name=teacher_in.name,
    )
    db.add(teacher)
    await db.flush()
    await db.refresh(teacher)
    return teacher


@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Teacher).where(Teacher.email == form_data.username))
    teacher = result.scalar_one_or_none()
    if not teacher or not verify_password(form_data.password, teacher.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(teacher.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=TeacherOut)
async def get_me(current_teacher: Teacher = Depends(get_current_teacher)):
    return current_teacher

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Boolean, Float, Text,
    TIMESTAMP, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .session import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    videos = relationship("Video", back_populates="teacher")
    sessions = relationship("Session", back_populates="teacher")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    title = Column(String, nullable=False)
    youtube_id = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    duration_sec = Column(Integer, nullable=True)
    status = Column(String, default="draft")  # draft, transcribing, processing, ready
    transcript = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    teacher = relationship("Teacher", back_populates="videos")
    concepts = relationship("VideoConcept", back_populates="video", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="video", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="video")


class VideoConcept(Base):
    __tablename__ = "video_concepts"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    concept = Column(String, nullable=False)
    time_sec = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)

    video = relationship("Video", back_populates="concepts")
    misconceptions = relationship("ConceptMisconception", back_populates="concept_ref", cascade="all, delete-orphan")


class ConceptMisconception(Base):
    __tablename__ = "concept_misconceptions"

    id = Column(Integer, primary_key=True)
    concept_id = Column(Integer, ForeignKey("video_concepts.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    concept_ref = relationship("VideoConcept", back_populates="misconceptions")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # [{text, is_correct}]
    correct_index = Column(Integer, nullable=False)
    time_anchor_sec = Column(Integer, nullable=True)
    concept_tag = Column(String, nullable=True)
    misconception_tag = Column(String, nullable=True)
    order_index = Column(Integer, default=0)

    video = relationship("Video", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    join_code = Column(String(8), unique=True, index=True, nullable=False)
    class_name = Column(String, nullable=True)
    status = Column(String, default="waiting")  # waiting, active, closed
    current_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    closed_at = Column(TIMESTAMP, nullable=True)

    teacher = relationship("Teacher", back_populates="sessions")
    video = relationship("Video", back_populates="sessions")
    students = relationship("Student", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    name = Column(String, nullable=False)
    joined_at = Column(TIMESTAMP, server_default=func.now())

    session = relationship("Session", back_populates="students")
    answers = relationship("Answer", back_populates="student")


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", "student_id", name="uq_answer_session_question_student"),
    )

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    chosen_index = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(TIMESTAMP, server_default=func.now())

    session = relationship("Session", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    student = relationship("Student", back_populates="answers")

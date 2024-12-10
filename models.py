from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    credits = Column(Integer, default=0)
    total_exam_time = Column(Integer, default=0)

    exams = relationship("Exam", back_populates="user")


class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="exercise")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    question_text = Column(String)
    correct_answer = Column(String)
    metadata = Column(Text)

    exercise = relationship("Exercise", back_populates="questions")


class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    score = Column(Integer)
    credits_earned = Column(Integer, default=0)
    total_time = Column(Integer, default=0)  # in seconds
    taken_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="exams")
    exercise = relationship("Exercise")
    exam_questions = relationship("ExamQuestion", back_populates="exam")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_answer = Column(String)
    correct = Column(Boolean)

    exam = relationship("Exam", back_populates="exam_questions")

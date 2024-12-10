from pydantic import BaseModel, EmailStr
from typing import List, Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    jwt_token: str
    user_id: int


class ExerciseResponse(BaseModel):
    id: int
    title: str
    description: str


class QuestionResponse(BaseModel):
    id: int
    question_text: str


class ExamResponse(BaseModel):
    id: int
    exercise_id: int
    score: Optional[int]
    credits_earned: Optional[int]
    total_time: Optional[int]


class MakeExamBody(BaseModel):
    exercise_id: int


class SubmitExamBody(BaseModel):
    exam_object: dict


class QuestionChatBody(BaseModel):
    question_id: int
    content: str
    history_message: Optional[List[dict]] = []


# Leaderboard response
class LeaderboardUser(BaseModel):
    user_id: int
    email: str
    credits: int
    total_exam_time: int

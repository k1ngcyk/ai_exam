from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class UserRegisterParams(BaseModel):
    login_number: str
    name: str
    depart: str
    job: str
    password: str


class UserLoginParams(BaseModel):
    login_number: str
    password: str


class UserResponse(BaseModel):
    jwt_token: str
    name: str
    id: int
    depart: str
    job: str


class QuestionDetailResponse(BaseModel):
    question_id: int
    question_type: str
    content: str
    options: Any


class ExerciseDetailResponse(BaseModel):
    exercise_id: int
    title: str
    content: str
    questions: List[QuestionDetailResponse]


class ExerciseListResponse(BaseModel):
    exercises: List[ExerciseDetailResponse]
    total: int
    current_page: int
    total_page: int


class QuestionCorrectResponse(BaseModel):
    question_id: int
    question_type: str
    content: str
    options: Any
    answer: str


class ExamCreateParams(BaseModel):
    title: str
    exercise_ids: List[int]


class ExamDetail(BaseModel):
    question_ids: List[int]


class ExamDetailResponse(BaseModel):
    exam_id: int
    questions: List[QuestionDetailResponse]


class UserAnswer(BaseModel):
    question_id: int
    answer: str


class ExamSubmitParams(BaseModel):
    exam_id: int
    user_answers: List[UserAnswer]


class ExamSubmitResponse(BaseModel):
    exam_id: int
    score: int
    time: int
    questions: List[QuestionDetailResponse]
    user_answers: List[UserAnswer]


class ExamHistoryDetailResponse(BaseModel):
    exam_id: int
    score: int
    time: int
    questions: List[QuestionDetailResponse]
    user_answers: List[UserAnswer]


class ExamHistoryListResponse(BaseModel):
    exams: List[ExamHistoryDetailResponse]
    total: int
    current_page: int
    total_page: int


class QuestionHistoryDetailResponse(BaseModel):
    user_id: int
    question_id: int
    exam_id: int
    user_answer: str
    is_correct: bool


class QuestionHistoryListResponse(BaseModel):
    questions: List[QuestionHistoryDetailResponse]
    total: int
    current_page: int
    total_page: int


class AIChatParams(BaseModel):
    exam_id: int
    question_id: int
    content: str


class AIChatResponse(BaseModel):
    ai_output: str

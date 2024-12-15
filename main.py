from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from typing import List, Optional
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from jose import jwt
import time
import asyncio
from math import ceil


from models import Base, User, Exercise, Question, Exam, ExamHistory, QuestionHistory
from schemas import (
    UserRegisterParams,
    UserLoginParams,
    UserResponse,
    ExerciseDetailResponse,
    ExerciseListResponse,
    QuestionDetailResponse,
    ExamCreateParams,
    ExamDetailResponse,
    ExamSubmitParams,
    ExamSubmitResponse,
    ExamHistoryDetailResponse,
    ExamHistoryListResponse,
    QuestionHistoryDetailResponse,
    QuestionHistoryListResponse,
    AIChatParams,
    AIChatResponse,
    UserAnswer,
)
from utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(engine)

app = FastAPI()

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401, detail="Invalid authentication credentials"
            )
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.JWTError as e:
        print(e)
        raise HTTPException(status_code=401, detail="Invalid token")


# Placeholder function for making exam detail from exercises
def make_exam_from_exercise(db: Session, exercise_ids: List[int]) -> List[int]:
    # Collect all questions from these exercises
    questions = db.query(Question).filter(Question.exercise_id.in_(exercise_ids)).all()
    # WIP: create exam
    question_ids = [q.id for q in questions]
    return question_ids


@app.post("/api/user/register", response_model=UserResponse)
def user_register(params: UserRegisterParams, db: Session = Depends(get_db)):
    # Check if login_number exists
    existing = db.query(User).filter(User.login_number == params.login_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = get_password_hash(params.password)
    user = User(
        login_number=params.login_number,
        name=params.name,
        depart=params.depart,
        job=params.job,
        password=hashed,
        credit=0,
        learning_time=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = create_access_token({"sub": str(user.id)})
    return UserResponse(
        jwt_token=access_token,
        name=user.name,
        id=user.id,
        depart=user.depart,
        job=user.job,
    )


@app.post("/api/user/login", response_model=UserResponse)
def user_login(params: UserLoginParams, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login_number == params.login_number).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    if not verify_password(params.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    access_token = create_access_token({"sub": str(user.id)})
    return UserResponse(
        jwt_token=access_token,
        name=user.name,
        id=user.id,
        depart=user.depart,
        job=user.job,
    )


@app.get("/api/exercise", response_model=ExerciseListResponse)
def get_exercise_list(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    total = db.query(func.count(Exercise.id)).scalar()
    if limit <= 0:
        limit = 10  # default fallback to avoid division by zero
    total_pages = ceil(total / limit) if total > 0 else 1

    exercises = db.query(Exercise).offset((page - 1) * limit).limit(limit).all()
    response = []
    for ex in exercises:
        questions_resp = []
        for q in ex.questions:
            questions_resp.append(
                QuestionDetailResponse(
                    question_id=q.id,
                    question_type=q.question_type,
                    content=q.content,
                    options=q.options,
                )
            )
        response.append(
            ExerciseDetailResponse(
                exercise_id=ex.id,
                title=ex.title,
                content=ex.content,
                questions=questions_resp,
            )
        )
    return ExerciseListResponse(
        exercises=response,
        total=total,
        current_page=page,
        total_page=total_pages,
    )


@app.get("/api/exercise/{id}", response_model=ExerciseDetailResponse)
def get_exercise_detail(id: int, db: Session = Depends(get_db)):
    ex = db.query(Exercise).filter(Exercise.id == id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    questions_resp = []
    for q in ex.questions:
        questions_resp.append(
            QuestionDetailResponse(
                question_id=q.id,
                question_type=q.question_type,
                content=q.content,
                options=q.options,
            )
        )
    return ExerciseDetailResponse(
        exercise_id=ex.id, title=ex.title, content=ex.content, questions=questions_resp
    )


@app.post("/api/exam", response_model=ExamDetailResponse)
def create_exam(
    params: ExamCreateParams,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exam = Exam(user_id=user.id, title=params.title)
    db.add(exam)
    db.commit()
    db.refresh(exam)

    question_ids = make_exam_from_exercise(db, params.exercise_ids)

    # Insert QuestionHistory
    for q_id in question_ids:
        qh = QuestionHistory(user_id=user.id, question_id=q_id, exam_id=exam.id)
        db.add(qh)

    # Insert ExamHistory
    eh = ExamHistory(user_id=user.id, exam_id=exam.id, score=0, time_used=0)
    db.add(eh)
    db.commit()

    # Build response
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    questions_resp = []
    for q in questions:
        questions_resp.append(
            QuestionDetailResponse(
                question_id=q.id,
                question_type=q.question_type,
                content=q.content,
                options=q.options,
            )
        )

    return ExamDetailResponse(exam_id=exam.id, questions=questions_resp)


@app.post("/api/exam/submit", response_model=ExamSubmitResponse)
def submit_exam(
    params: ExamSubmitParams,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Calculate score and update question_history
    exam = (
        db.query(Exam)
        .filter(Exam.id == params.exam_id, Exam.user_id == user.id)
        .first()
    )
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Fetch exam_history
    eh = (
        db.query(ExamHistory)
        .filter(ExamHistory.exam_id == params.exam_id, ExamHistory.user_id == user.id)
        .first()
    )
    if not eh:
        raise HTTPException(status_code=400, detail="ExamHistory not found")

    # get start time
    start_time = eh.created_at
    elapsed_time = int(time.time() - start_time.timestamp())

    score = 0
    question_ids = [ua.question_id for ua in params.user_answers]
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    q_map = {q.id: q for q in questions}

    for ua in params.user_answers:
        qhist = (
            db.query(QuestionHistory)
            .filter(
                QuestionHistory.user_id == user.id,
                QuestionHistory.exam_id == params.exam_id,
                QuestionHistory.question_id == ua.question_id,
            )
            .first()
        )
        if not qhist:
            # If there's no question_history record, skip or raise
            continue
        correct_answer = q_map[ua.question_id].answer
        # WIP: check if answer is correct
        is_correct = correct_answer == ua.answer
        if is_correct:
            score += 10
        qhist.user_answer = ua.answer
        qhist.is_correct = is_correct
        db.add(qhist)

        # Check if first time correct
        # count attempts for this question by user
        count_attempts = (
            db.query(QuestionHistory)
            .filter(
                QuestionHistory.user_id == user.id,
                QuestionHistory.question_id == ua.question_id,
                QuestionHistory.user_answer.isnot(None),
            )
            .count()
        )

        if count_attempts == 0 and is_correct:
            # first time correct, update user credit
            user.credit += 10
            db.add(user)

    eh.score = score
    eh.time_used = elapsed_time
    user.learning_time += elapsed_time
    db.add(user)
    db.add(eh)
    db.commit()

    # Return response
    # questions for the exam
    exam_question_histories = (
        db.query(QuestionHistory)
        .filter(
            QuestionHistory.exam_id == params.exam_id,
            QuestionHistory.user_id == user.id,
        )
        .all()
    )
    question_ids = [qh.question_id for qh in exam_question_histories]
    exam_questions = db.query(Question).filter(Question.id.in_(question_ids)).all()

    questions_resp = []
    q_map = {q.id: q for q in exam_questions}
    for qh in exam_question_histories:
        q = q_map[qh.question_id]
        questions_resp.append(
            QuestionDetailResponse(
                question_id=q.id,
                question_type=q.question_type,
                content=q.content,
                options=q.options,
            )
        )

    return ExamSubmitResponse(
        exam_id=params.exam_id,
        score=score,
        time=elapsed_time,
        questions=questions_resp,
        user_answers=params.user_answers,
    )


@app.get("/api/leaderboard/credits")
def leaderboard_credits(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.credit.desc()).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "credit": u.credit,
            "depart": u.depart,
            "job": u.job,
        }
        for u in users
    ]


@app.get("/api/leaderboard/times")
def leaderboard_times(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.learning_time.desc()).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "learning_time": u.learning_time,
            "depart": u.depart,
            "job": u.job,
        }
        for u in users
    ]


@app.get("/api/exam/history", response_model=ExamHistoryListResponse)
def exam_history(
    page: int = 1,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = (
        db.query(func.count(ExamHistory.id))
        .filter(ExamHistory.user_id == user.id)
        .scalar()
    )
    if limit <= 0:
        limit = 10
    total_pages = ceil(total / limit) if total > 0 else 1

    histories = (
        db.query(ExamHistory)
        .filter(ExamHistory.user_id == user.id)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    results = []
    for h in histories:
        qhs = (
            db.query(QuestionHistory)
            .filter(
                QuestionHistory.exam_id == h.exam_id, QuestionHistory.user_id == user.id
            )
            .all()
        )
        q_ids = [qh.question_id for qh in qhs]
        questions = db.query(Question).filter(Question.id.in_(q_ids)).all()
        q_map = {q.id: q for q in questions}
        questions_resp = [
            QuestionDetailResponse(
                question_id=q_map[qh.question_id].id,
                question_type=q_map[qh.question_id].question_type,
                content=q_map[qh.question_id].content,
                options=q_map[qh.question_id].options,
            )
            for qh in qhs
        ]
        user_answers_resp = [
            UserAnswer(
                question_id=qh.question_id,
                answer=qh.user_answer if qh.user_answer else "",
            )
            for qh in qhs
        ]
        results.append(
            ExamHistoryDetailResponse(
                exam_id=h.exam_id,
                score=h.score,
                time=h.time_used,
                questions=questions_resp,
                user_answers=user_answers_resp,
            )
        )
    return ExamHistoryListResponse(
        exams=results, total=total, current_page=page, total_page=total_pages
    )


@app.get("/api/exam/history/{id}", response_model=ExamHistoryDetailResponse)
def exam_history_detail(
    id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    h = (
        db.query(ExamHistory)
        .filter(ExamHistory.exam_id == id, ExamHistory.user_id == user.id)
        .first()
    )
    if not h:
        raise HTTPException(status_code=404, detail="History not found")
    qhs = (
        db.query(QuestionHistory)
        .filter(
            QuestionHistory.exam_id == h.exam_id, QuestionHistory.user_id == user.id
        )
        .all()
    )
    q_ids = [qh.question_id for qh in qhs]
    questions = db.query(Question).filter(Question.id.in_(q_ids)).all()
    q_map = {q.id: q for q in questions}
    questions_resp = [
        QuestionDetailResponse(
            question_id=q_map[qh.question_id].id,
            question_type=q_map[qh.question_id].question_type,
            content=q_map[qh.question_id].content,
            options=q_map[qh.question_id].options,
        )
        for qh in qhs
    ]
    user_answers_resp = [
        UserAnswer(
            question_id=qh.question_id, answer=qh.user_answer if qh.user_answer else ""
        )
        for qh in qhs
    ]

    return ExamHistoryDetailResponse(
        exam_id=h.exam_id,
        score=h.score,
        time=h.time_used,
        questions=questions_resp,
        user_answers=user_answers_resp,
    )


@app.get("/api/question", response_model=QuestionHistoryListResponse)
def question_history_list(
    page: int = 1,
    limit: int = 10,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = (
        db.query(func.count(QuestionHistory.id))
        .filter(QuestionHistory.user_id == user.id, QuestionHistory.is_correct == False)
        .scalar()
    )
    if limit <= 0:
        limit = 10
    total_pages = ceil(total / limit) if total > 0 else 1

    qhs = (
        db.query(QuestionHistory)
        .filter(QuestionHistory.user_id == user.id, QuestionHistory.is_correct == False)
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    results = []
    for qh in qhs:
        results.append(
            QuestionHistoryDetailResponse(
                user_id=qh.user_id,
                question_id=qh.question_id,
                exam_id=qh.exam_id,
                user_answer=qh.user_answer if qh.user_answer else "",
                is_correct=qh.is_correct,
            )
        )
    return QuestionHistoryListResponse(
        questions=results, total=total, current_page=page, total_page=total_pages
    )


async def generate_text():
    """Simulates an AI chat response generator."""
    responses = [
        "Hello! How can I assist you today?",
        "It seems like you want to stream text responses.",
        "This response is streamed in real-time.",
        "FastAPI makes streaming text easy!",
        "Goodbye and take care!",
    ]
    for response in responses:
        yield response + "\n"  # Yield each response with a newline
        await asyncio.sleep(1)  # Simulate delay between chunks


@app.post("/api/question/chat", response_model=AIChatResponse)
def ai_chat(
    params: AIChatParams,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Placeholder: This would call an AI model or service
    # For now, just echo input
    return StreamingResponse(generate_text(), media_type="text/plain")

    return AIChatResponse(ai_output=f"AI response to: {params.content}")

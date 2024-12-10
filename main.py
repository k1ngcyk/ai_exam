from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from .database import SessionLocal, engine, Base
from .models import User
from .schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    ExerciseResponse,
    MakeExamBody,
    SubmitExamBody,
    QuestionChatBody,
    LeaderboardUser,
)
from .auth import create_jwt_token, get_current_user_id
from .crud import (
    create_user,
    authenticate_user,
    get_exercises,
    get_exercise_by_id,
    record_exam,
    update_user_credits_and_time,
    get_leaderboard_credits,
    get_leaderboard_times,
    get_user_exam_history,
    get_exam_by_id,
    get_questions_for_user_improvement,
)
from .predefined import make_exam_from_exercise, get_score

app = FastAPI()

# You can run migrations or create tables directly for simplicity
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/user/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing = authenticate_user(db, user_data.email, user_data.password)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = create_user(db, user_data.email, user_data.password)
    token = create_jwt_token(user.id)
    return TokenResponse(jwt_token=token, user_id=user.id)


@app.post("/api/user/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt_token(user.id)
    return TokenResponse(jwt_token=token, user_id=user.id)


@app.get("/api/exercise", response_model=list[ExerciseResponse])
def list_exercises(
    page: int = 1,
    limit: int = 10,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    exercises = get_exercises(db, skip, limit)
    return [
        ExerciseResponse(id=e.id, title=e.title, description=e.description)
        for e in exercises
    ]


@app.get("/api/exercise/{id}", response_model=ExerciseResponse)
def get_exercise_detail(
    id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    exercise = get_exercise_by_id(db, id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return ExerciseResponse(
        id=exercise.id, title=exercise.title, description=exercise.description
    )


@app.post("/api/exam", response_model=dict)
def create_exam(
    body: MakeExamBody,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    exercise = get_exercise_by_id(db, body.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    exam_object = make_exam_from_exercise(exercise)
    return exam_object


@app.post("/api/exam/submit", response_model=dict)
def submit_exam(
    body: SubmitExamBody,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # exam_object is { exercise_id, questions: [ {question_id, user_answer, correct_answer}, ...] }
    exam = body.exam_object
    score = get_score(exam)
    credits_earned = len(
        exam["questions"]
    )  # For simplicity, credits = number of questions
    total_time = (
        120  # Suppose we got the time from exam_object or client side, example static
    )
    # record exam and update user
    rec_exam = record_exam(
        db,
        user_id,
        exam["exercise_id"],
        score,
        credits_earned,
        total_time,
        exam["questions"],
    )
    update_user_credits_and_time(db, user_id, credits_earned, total_time)

    correct_exam_object = {
        "id": rec_exam.id,
        "exercise_id": rec_exam.exercise_id,
        "score": score,
        "credits_earned": credits_earned,
        "total_time": total_time,
    }
    return correct_exam_object


@app.get("/api/leaderboard/credits", response_model=dict)
def leaderboard_credits(db: Session = Depends(get_db)):
    users = get_leaderboard_credits(db)
    return {
        "leaderboard": [
            LeaderboardUser(
                user_id=u.id,
                email=u.email,
                credits=u.credits,
                total_exam_time=u.total_exam_time,
            )
            for u in users
        ]
    }


@app.get("/api/leaderboard/times", response_model=dict)
def leaderboard_times(db: Session = Depends(get_db)):
    users = get_leaderboard_times(db)
    return {
        "leaderboard": [
            LeaderboardUser(
                user_id=u.id,
                email=u.email,
                credits=u.credits,
                total_exam_time=u.total_exam_time,
            )
            for u in users
        ]
    }


@app.get("/api/exam/history", response_model=list[dict])
def exam_history(
    page: int = 1,
    limit: int = 10,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    exams = get_user_exam_history(db, user_id, skip, limit)
    return [
        {
            "id": ex.id,
            "exercise_id": ex.exercise_id,
            "score": ex.score,
            "credits_earned": ex.credits_earned,
            "total_time": ex.total_time,
            "taken_at": ex.taken_at.isoformat(),
        }
        for ex in exams
    ]


@app.get("/api/exam/history/{id}", response_model=dict)
def exam_detail(
    id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)
):
    exam = get_exam_by_id(db, id)
    if not exam or exam.user_id != user_id:
        raise HTTPException(status_code=404, detail="Exam not found")
    return {
        "id": exam.id,
        "exercise_id": exam.exercise_id,
        "score": exam.score,
        "credits_earned": exam.credits_earned,
        "total_time": exam.total_time,
        "taken_at": exam.taken_at.isoformat(),
        "questions": [
            {
                "question_id": eq.question_id,
                "user_answer": eq.user_answer,
                "correct": eq.correct,
            }
            for eq in exam.exam_questions
        ],
    }


@app.get("/api/question", response_model=list[dict])
def get_improvement_questions(
    page: int = 1,
    limit: int = 10,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    questions = get_questions_for_user_improvement(db, user_id, skip, limit)
    return [{"id": q.id, "question_text": q.question_text} for q in questions]


@app.post("/api/question/chat", response_model=dict)
def question_chat(
    body: QuestionChatBody,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Mocked AI response
    ai_output = f"AI says: The answer to question {body.question_id} is just a guess."
    # You can integrate a real LLM here and use the history messages
    return {"ai_output": ai_output}

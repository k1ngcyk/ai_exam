from sqlalchemy.orm import Session
from .models import User, Exercise, Question, Exam, ExamQuestion
from .utils import hash_password, verify_password


def create_user(db: Session, email: str, password: str):
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def get_exercises(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Exercise).offset(skip).limit(limit).all()


def get_exercise_by_id(db: Session, exercise_id: int):
    return db.query(Exercise).filter(Exercise.id == exercise_id).first()


def get_exam_by_id(db: Session, exam_id: int):
    return db.query(Exam).filter(Exam.id == exam_id).first()


def record_exam(
    db: Session,
    user_id: int,
    exercise_id: int,
    score: int,
    credits_earned: int,
    total_time: int,
    questions_data: list,
):
    exam = Exam(
        user_id=user_id,
        exercise_id=exercise_id,
        score=score,
        credits_earned=credits_earned,
        total_time=total_time,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    for qd in questions_data:
        eq = ExamQuestion(
            exam_id=exam.id,
            question_id=qd["question_id"],
            user_answer=qd["user_answer"],
            correct=qd["correct"],
        )
        db.add(eq)
    db.commit()
    return exam


def update_user_credits_and_time(
    db: Session, user_id: int, credits: int, exam_time: int
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.credits += credits
        user.total_exam_time += exam_time
        db.commit()
        db.refresh(user)
    return user


def get_leaderboard_credits(db: Session, limit: int = 10):
    return db.query(User).order_by(User.credits.desc()).limit(limit).all()


def get_leaderboard_times(db: Session, limit: int = 10):
    return db.query(User).order_by(User.total_exam_time.desc()).limit(limit).all()


def get_user_exam_history(db: Session, user_id: int, skip: int = 0, limit: int = 10):
    return (
        db.query(Exam).filter(Exam.user_id == user_id).offset(skip).limit(limit).all()
    )


def get_questions_for_user_improvement(
    db: Session, user_id: int, skip: int, limit: int
):
    # Return questions that user got wrong in previous exams
    subquery = (
        db.query(ExamQuestion.question_id)
        .join(Exam)
        .filter(Exam.user_id == user_id, ExamQuestion.correct == False)
        .subquery()
    )
    return (
        db.query(Question)
        .filter(Question.id.in_(subquery))
        .offset(skip)
        .limit(limit)
        .all()
    )

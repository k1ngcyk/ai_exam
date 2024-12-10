# FastAPI Exam Platform

This project provides a simple FastAPI-based application for user registration, login, and handling exercises, exams, and leaderboards. It uses SQLite for data storage, JWT for authentication, and SQLAlchemy as an ORM.

## Features

- **User Registration & Login**: Create and authenticate users with JWT.
- **Exercise Listing & Detail**: Protected endpoints to list and retrieve exercises and their associated questions.
- **Exam Creation & Submission**: Generate exams from exercises, submit answers, and record scores and credits.
- **Leaderboard**: Rank users by credits and total exam times.
- **Exam History**: View past exams taken by a user.
- **Question Improvement**: Retrieve questions that a user answered incorrectly for targeted practice.
- **Chat Endpoint for Questions**: Integrate with an AI assistant or custom logic to discuss questions and answers.

## Requirements

- Python 3.10+
- SQLite (built-in with Python)
- A virtual environment is recommended

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. **Create and activate a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Linux/macOS
   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations or create tables**:
   The code includes a `Base.metadata.create_all(bind=engine)` call that will create the SQLite tables automatically on the first run.

5. **Run the application**:
   ```bash
   uvicorn project.main:app --reload
   ```
   
   *Adjust `project.main:app` if your directory structure differs.*

6. **Open the browser and test**:
   Visit `http://127.0.0.1:8000/docs` to see the automatically generated Swagger UI and test the endpoints.

## Endpoints Overview

- **User**
  - `POST /api/user/register`  
    Create a new user account and returns a JWT token.
  - `POST /api/user/login`  
    Authenticate an existing user and returns a JWT token.
    
- **Exercise**
  - `GET /api/exercise?page=&limit=`  
    List exercises (JWT required).
  - `GET /api/exercise/{id}`  
    Get details of a single exercise (JWT required).

- **Exam**
  - `POST /api/exam`  
    Generate an exam object from a given exercise (JWT required).
  - `POST /api/exam/submit`  
    Submit an exam’s answers, record results, update credits, and score (JWT required).

- **Leaderboard**
  - `GET /api/leaderboard/credits`  
    Get leaderboard sorted by user credits.
  - `GET /api/leaderboard/times`  
    Get leaderboard sorted by total exam time.

- **Exam History**
  - `GET /api/exam/history?page=&limit=`  
    List past exams taken by the user (JWT required).
  - `GET /api/exam/history/{id}`  
    Get details of a single past exam (JWT required).

- **Question Improvement**
  - `GET /api/question?page=&limit=`  
    List questions the user previously answered incorrectly (JWT required).

- **Question Chat**
  - `POST /api/question/chat`  
    Send a question and message history to an AI endpoint to receive guidance (JWT required).

## Database Schema

Suggested tables include: `users`, `exercises`, `questions`, `exams`, `exam_questions`.  
Relationships:
- One `exercise` to many `questions`.
- One `exam` to many `exam_questions`.
- One `user` to many `exams`.

## Customization

- Modify `SECRET_KEY` in `auth.py` to a secure, randomly generated key.
- Adjust `make_exam_from_exercise(exercise)` and `get_score(exam)` logic in `predefined.py` as per your business rules.
- Integrate a real LLM or external API in `/api/question/chat` if needed.

## Contributing

Contributions are welcome!  
Please open issues or PRs with proposed changes.

## License

This project is licensed under the MIT License. Feel free to adapt and use it.
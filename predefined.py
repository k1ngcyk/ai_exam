def make_exam_from_exercise(exercise):
    # For simplicity, just return the exercise's questions as an exam
    # In a real scenario, you might randomize or select subsets.
    # return a dict representing the exam
    return {
        "exercise_id": exercise.id,
        "questions": [
            {"question_id": q.id, "question_text": q.question_text}
            for q in exercise.questions
        ],
    }


def get_score(exam):
    # exam_object might contain questions and user answers
    correct_count = 0
    for q in exam["questions"]:
        if q["user_answer"] == q["correct_answer"]:
            correct_count += 1
    return correct_count

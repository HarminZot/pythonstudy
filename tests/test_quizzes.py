from app.extensions import db
from app.models import Quiz, QuizOption, QuizQuestion
from .conftest import login


def create_quiz(app, **values):
    with app.app_context():
        quiz = Quiz(
            course_id=1,
            created_by=2,
            title=values.get("title", "Проверочный тест"),
            status="published",
            max_attempts=3,
            passing_score=70,
            randomize_questions=values.get("randomize_questions", False),
            randomize_options=values.get("randomize_options", False),
        )
        db.session.add(quiz)
        db.session.flush()
        for order, text in enumerate(("Первый вопрос", "Второй вопрос"), 1):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_type="single_choice",
                question_text=text,
                points=1,
                order_index=order,
            )
            db.session.add(question)
            db.session.flush()
            db.session.add_all([
                QuizOption(question_id=question.id, option_text=f"Ответ A{order}", is_correct=True, order_index=1),
                QuizOption(question_id=question.id, option_text=f"Ответ B{order}", is_correct=False, order_index=2),
            ])
        db.session.commit()
        return quiz.id


def test_quiz_randomizes_questions_and_options(client, app, monkeypatch):
    quiz_id = create_quiz(app, randomize_questions=True, randomize_options=True)
    monkeypatch.setattr("app.student.routes.random.shuffle", lambda items: items.reverse())
    login(client, "student@test.local", "Student123!")
    response = client.get(f"/student/quizzes/{quiz_id}")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert page.index("Второй вопрос") < page.index("Первый вопрос")
    assert page.index("Ответ B2") < page.index("Ответ A2")

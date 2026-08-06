from app.extensions import db
from app.models import ProgrammingTask, Quiz, QuizOption, QuizQuestion, TaskTestCase

from .conftest import login


def test_teacher_can_edit_own_task(client, app):
    login(client, "teacher@test.local", "Teacher123!")
    response = client.post(
        "/teacher/tasks/1/edit",
        data={
            "title": "Удвоение целого числа",
            "description": "Прочитайте число и выведите удвоенное значение.",
            "difficulty": "intermediate",
            "points": "20",
            "time_limit_seconds": "1.5",
            "memory_limit_mb": "128",
            "status": "published",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        task = db.session.get(ProgrammingTask, 1)
        assert task.title == "Удвоение целого числа"
        assert task.difficulty == "intermediate"
        assert task.points == 20


def test_teacher_can_edit_and_delete_test_case(client, app):
    login(client, "teacher@test.local", "Teacher123!")
    response = client.post(
        "/teacher/test-cases/1/edit",
        data={"name": "Проверка нуля", "input_data": "0\n", "expected_output": "0", "weight": "2", "timeout_seconds": "1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(TaskTestCase, 1).name == "Проверка нуля"
    response = client.post("/teacher/test-cases/2/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(TaskTestCase, 2) is None


def test_teacher_can_edit_quiz_question(client, app):
    with app.app_context():
        quiz = Quiz(course_id=1, created_by=2, title="Проверка знаний", status="draft")
        db.session.add(quiz)
        db.session.flush()
        question = QuizQuestion(quiz_id=quiz.id, question_type="single_choice", question_text="Старый текст", points=1)
        db.session.add(question)
        db.session.flush()
        db.session.add_all([
            QuizOption(question_id=question.id, option_text="Да", is_correct=True, order_index=1),
            QuizOption(question_id=question.id, option_text="Нет", is_correct=False, order_index=2),
        ])
        db.session.commit()
        question_id = question.id
    login(client, "teacher@test.local", "Teacher123!")
    response = client.post(
        f"/teacher/questions/{question_id}/edit",
        data={"question_type": "multiple_choice", "question_text": "Выберите четные числа", "options": "2\n3\n4", "correct_options": "1,3", "points": "3", "explanation": "Делятся на два."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        saved = db.session.get(QuizQuestion, question_id)
        assert saved.question_text == "Выберите четные числа"
        assert [option.option_text for option in saved.options if option.is_correct] == ["2", "4"]


def test_teacher_exports_task_submissions(client, app):
    login(client, "teacher@test.local", "Teacher123!")
    response = client.get("/teacher/tasks/1/submissions/export")
    assert response.status_code == 200
    assert response.headers["Content-Disposition"].endswith("task_1_submissions.xlsx")
    assert response.data.startswith(b"PK")

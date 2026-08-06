from app.extensions import db
from app.models import ProgrammingTask, TaskTestCase

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

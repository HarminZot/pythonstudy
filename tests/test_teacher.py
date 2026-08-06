from app.extensions import db
from app.models import ProgrammingTask

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

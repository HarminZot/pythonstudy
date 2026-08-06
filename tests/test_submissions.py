from app.extensions import db
from app.models import Notification, Submission
from .conftest import login


def test_submit_correct_solution(client, app):
    login(client, "student@test.local", "Student123!")
    response = client.post("/api/tasks/1/submit", json={"code": "value = int(input())\nprint(value * 2)"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "accepted"
    assert data["score"] == 100.0
    with app.app_context():
        assert Submission.query.count() == 1


def test_submit_wrong_solution(client):
    login(client, "student@test.local", "Student123!")
    response = client.post("/api/tasks/1/submit", json={"code": "print(0)"})
    assert response.status_code == 200
    assert response.get_json()["status"] == "wrong_answer"


def test_submission_history(client):
    login(client, "student@test.local", "Student123!")
    client.post("/api/tasks/1/submit", json={"code": "print(0)"})
    response = client.get("/student/submissions")
    assert response.status_code == 200
    assert "Удвоение числа" in response.get_data(as_text=True)


def test_teacher_can_comment_submission(client, app):
    with app.app_context():
        submission = Submission(task_id=1, user_id=1, code="print(4)", status="accepted", score=100)
        db.session.add(submission)
        db.session.commit()
        submission_id = submission.id
    login(client, "teacher@test.local", "Teacher123!")
    response = client.post(
        f"/teacher/submissions/{submission_id}/review",
        data={"teacher_comment": "Хорошее и понятное решение."},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        saved = db.session.get(Submission, submission_id)
        assert saved.teacher_comment == "Хорошее и понятное решение."
        assert saved.reviewed_by == 2
        assert Notification.query.filter_by(user_id=1, notification_type="submission_review").count() == 1

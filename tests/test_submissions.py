from app.models import Submission
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

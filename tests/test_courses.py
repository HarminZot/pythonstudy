from app.models import CourseEnrollment, LessonProgress
from .conftest import login


def test_student_my_courses(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/courses")
    assert response.status_code == 200
    assert "Тестовый курс" in response.get_data(as_text=True)


def test_student_opens_lesson(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/lessons/1")
    assert response.status_code == 200
    assert "Урок 1" in response.get_data(as_text=True)


def test_mark_lesson_complete(client, app):
    login(client, "student@test.local", "Student123!")
    response = client.post("/api/lessons/1/complete", headers={"X-CSRFToken": "unused"})
    assert response.status_code == 200
    with app.app_context():
        progress = LessonProgress.query.filter_by(user_id=1, lesson_id=1).first()
        assert progress.status == "completed"


def test_duplicate_enrollment_not_created(client, app):
    login(client, "student@test.local", "Student123!")
    response = client.post("/student/courses/1/enroll", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert CourseEnrollment.query.filter_by(user_id=1, course_id=1).count() == 1

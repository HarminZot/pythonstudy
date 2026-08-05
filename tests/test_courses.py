from app.extensions import db
from app.models import CourseEnrollment, Lesson, LessonProgress
from .conftest import login


def test_student_my_courses(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/courses")
    assert response.status_code == 200
    assert "Тестовый курс" in response.get_data(as_text=True)


def test_student_dashboard_shows_learning_statistics(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/dashboard")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "завершенных уроков" in page
    assert "средний балл" in page


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


def test_sequential_course_locks_next_lesson(client, app):
    with app.app_context():
        second_lesson = Lesson(
            module_id=1,
            title="Урок 2",
            slug="lesson-2",
            content="<p>Продолжение</p>",
            order_index=2,
            is_published=True,
            lesson_type="theory",
        )
        db.session.add(second_lesson)
        db.session.commit()
        second_lesson_id = second_lesson.id

    login(client, "student@test.local", "Student123!")
    assert client.get(f"/student/lessons/{second_lesson_id}").status_code == 403
    assert client.post("/api/lessons/1/complete").status_code == 200
    assert client.get(f"/student/lessons/{second_lesson_id}").status_code == 200


def test_lesson_navigation_unlocks_next_link(client, app):
    with app.app_context():
        second_lesson = Lesson(
            module_id=1,
            title="Навигационный урок",
            slug="navigation-lesson",
            content="<p>Продолжение</p>",
            order_index=2,
            is_published=True,
            lesson_type="theory",
        )
        db.session.add(second_lesson)
        db.session.commit()
        second_lesson_id = second_lesson.id

    login(client, "student@test.local", "Student123!")
    page = client.get("/student/lessons/1").get_data(as_text=True)
    assert "Завершите текущий урок" in page
    client.post("/api/lessons/1/complete")
    page = client.get("/student/lessons/1").get_data(as_text=True)
    assert f"/student/lessons/{second_lesson_id}" in page

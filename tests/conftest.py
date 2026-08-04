import pytest

from app import create_app
from app.extensions import db
from app.models import Course, CourseEnrollment, CourseModule, Lesson, ProgrammingTask, Role, TaskTestCase, User


@pytest.fixture()
def app(tmp_path):
    app = create_app("testing")
    app.config.update(
        UPLOAD_ROOT=tmp_path / "uploads",
        GENERATED_ROOT=tmp_path / "generated",
        TEMP_ROOT=tmp_path / "temp",
    )
    with app.app_context():
        db.create_all()
        roles = {
            code: Role(code=code, name=name)
            for code, name in (("student", "Студент"), ("teacher", "Преподаватель"), ("admin", "Администратор"))
        }
        db.session.add_all(roles.values())
        db.session.flush()
        student = User(role=roles["student"], email="student@test.local", first_name="Иван", last_name="Иванов")
        teacher = User(role=roles["teacher"], email="teacher@test.local", first_name="Анна", last_name="Петрова")
        admin = User(role=roles["admin"], email="admin@test.local", first_name="Админ", last_name="Системный")
        for user, password in ((student, "Student123!"), (teacher, "Teacher123!"), (admin, "Admin123!")):
            user.set_password(password)
            db.session.add(user)
        db.session.flush()
        course = Course(
            teacher_id=teacher.id,
            title="Тестовый курс",
            slug="test-course",
            short_description="Краткое описание",
            full_description="Полное описание курса",
            status="published",
            difficulty="beginner",
            estimated_hours=4,
        )
        db.session.add(course)
        db.session.flush()
        module = CourseModule(course_id=course.id, title="Модуль 1", order_index=1)
        db.session.add(module)
        db.session.flush()
        lesson = Lesson(
            module_id=module.id,
            title="Урок 1",
            slug="lesson-1",
            content="<p>Материал</p>",
            order_index=1,
            is_published=True,
            lesson_type="mixed",
        )
        db.session.add(lesson)
        db.session.flush()
        task = ProgrammingTask(
            lesson_id=lesson.id,
            created_by=teacher.id,
            title="Удвоение числа",
            slug="double-number",
            description="Удвойте число",
            starter_code="value = int(input())\n",
            status="published",
            points=10,
            memory_limit_mb=256,
            time_limit_seconds=2,
            order_index=1,
        )
        db.session.add(task)
        db.session.flush()
        db.session.add_all([
            TaskTestCase(task_id=task.id, name="Тест 1", input_data="2\n", expected_output="4", is_hidden=False, order_index=1),
            TaskTestCase(task_id=task.id, name="Тест 2", input_data="5\n", expected_output="10", is_hidden=True, order_index=2),
        ])
        db.session.add(CourseEnrollment(course_id=course.id, user_id=student.id))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def login(client, email, password):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)

from .conftest import login


def test_anonymous_student_dashboard_redirects(client):
    response = client.get("/student/dashboard")
    assert response.status_code in {302, 401}


def test_student_cannot_open_admin(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/admin/")
    assert response.status_code == 403


def test_teacher_can_open_teacher_dashboard(client):
    login(client, "teacher@test.local", "Teacher123!")
    response = client.get("/teacher/dashboard")
    assert response.status_code == 200


def test_admin_can_open_user_management(client):
    login(client, "admin@test.local", "Admin123!")
    response = client.get("/admin/users")
    assert response.status_code == 200

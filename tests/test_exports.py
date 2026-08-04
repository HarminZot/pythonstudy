from .conftest import login


def test_student_xlsx_export(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/export/xlsx")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/vnd.openxmlformats")


def test_student_docx_export(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/export/docx")
    assert response.status_code == 200
    assert "officedocument.wordprocessingml.document" in response.headers["Content-Type"]

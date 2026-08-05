from .conftest import login


def test_task_page_loads_codemirror(client):
    login(client, "student@test.local", "Student123!")
    response = client.get("/student/tasks/1")
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "codemirror@5.65.16" in page
    assert 'id="code-editor"' in page


def test_task_page_configures_local_draft(client):
    login(client, "student@test.local", "Student123!")
    page = client.get("/student/tasks/1").get_data(as_text=True)
    assert "pythonstudy:draft:1:1" in page
    assert 'id="draft-status"' in page

import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset task data before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all tasks and add the default priority to old tasks."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_add_task_success(client):
    """Create a task and persist its selected priority."""
    response = client.post(
        '/api/tasks',
        json={"title": "Test new task", "priority": "High"}
    )
    assert response.status_code == 201
    created_task = response.get_json()
    assert created_task['title'] == "Test new task"
    assert created_task['priority'] == "High"

    get_response = client.get('/api/tasks')
    returned_tasks = get_response.get_json()
    assert len(returned_tasks) == 3
    persisted_task = next(
        task for task in returned_tasks if task['title'] == "Test new task"
    )
    assert persisted_task['priority'] == "High"


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_accepts_all_priorities(client, priority):
    """Accept each supported task priority value."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == priority


def test_add_task_defaults_missing_priority_to_medium(client):
    """Default an omitted priority to Medium."""
    response = client.post('/api/tasks', json={"title": "Default task"})

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_empty_priority_to_medium(client):
    """Default an empty priority to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Empty priority task", "priority": ""}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_invalid_priority_to_medium(client):
    """Default an invalid priority to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": "Urgent"}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_defaults_non_string_priority_to_medium(client):
    """Default a non-string priority to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Non-string priority task", "priority": 1}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_missing_title(client):
    """Reject task creation when the title is missing."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete the task matching the requested identifier."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2


def test_frontend_has_priority_selector_and_display_support():
    """Expose priority controls and rendering support in frontend files."""
    with open('templates/index.html', encoding='utf-8') as template_file:
        template = template_file.read()
    with open('static/app.js', encoding='utf-8') as script_file:
        script = script_file.read()

    assert 'id="task-priority"' in template
    assert 'value="Low"' in template
    assert 'value="Medium"' in template
    assert 'value="High"' in template
    assert 'priorityInput.value' in script
    assert 'priority-badge' in script
    assert 'priority-${priority.toLowerCase()}' in script

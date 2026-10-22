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
    """Reset the in-memory task store before each test."""
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
    """Return existing tasks with a Medium default priority."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_add_task_success(client):
    """Create a task and preserve it in subsequent GET responses."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    assert response.get_json()['priority'] == 'Medium'

    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 3
    assert data[-1]['title'] == "Test new task"
    assert data[-1]['priority'] == 'Medium'


def test_add_task_accepts_all_valid_priorities(client):
    """Create tasks with each supported priority value."""
    for priority in ('Low', 'Medium', 'High'):
        response = client.post(
            '/api/tasks',
            json={"title": f"{priority} task", "priority": priority}
        )
        assert response.status_code == 201
        assert response.get_json()['priority'] == priority

    response = client.get('/api/tasks')
    priorities = [task['priority'] for task in response.get_json()]
    assert priorities[-3:] == ['Low', 'Medium', 'High']


def test_add_task_empty_priority_defaults_to_medium(client):
    """Normalize an explicitly empty priority to Medium."""
    response = client.post(
        '/api/tasks',
        json={"title": "Default priority task", "priority": ""}
    )
    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_add_task_rejects_invalid_priority(client):
    """Reject priorities outside the supported values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid priority task", "priority": "Urgent"}
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_task_missing_title(client):
    """Reject requests without a task title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response = client.post('/api/tasks', json={})
    assert response.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2

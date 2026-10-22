import pytest

from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset the in-memory task list before each test."""
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
    """Return existing tasks with a compatible default priority."""
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_valid_priorities(client, priority):
    """Accept and return each supported task priority."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    created_task = response.get_json()
    assert created_task['priority'] == priority


def test_add_task_priority_persists_in_get_response(client):
    """Persist a submitted priority when retrieving tasks."""
    response = client.post(
        '/api/tasks',
        json={"title": "High priority task", "priority": "High"}
    )
    assert response.status_code == 201

    tasks_response = client.get('/api/tasks')
    returned_tasks = tasks_response.get_json()
    created_task = next(
        task for task in returned_tasks
        if task['title'] == 'High priority task'
    )
    assert created_task['priority'] == 'High'


@pytest.mark.parametrize('priority', [None, '', 'Urgent'])
def test_add_task_missing_or_invalid_priority_defaults_to_medium(
    client,
    priority
):
    """Default missing or unsupported priorities to Medium."""
    payload = {"title": "Default priority task"}
    if priority is not None:
        payload['priority'] = priority

    response = client.post('/api/tasks', json=payload)

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_existing_tasks_without_priority_are_compatible(client):
    """Expose Medium for stored tasks without a priority field."""
    tasks.append({"id": 3, "title": "Legacy task"})

    response = client.get('/api/tasks')

    assert response.status_code == 200
    legacy_task = next(
        task for task in response.get_json()
        if task['title'] == 'Legacy task'
    )
    assert legacy_task['priority'] == 'Medium'


def test_add_task_success(client):
    """Create a task with the default priority."""
    response = client.post('/api/tasks', json={"title": "Test new task"})
    assert response.status_code == 201
    assert response.get_json()['title'] == "Test new task"
    assert response.get_json()['priority'] == "Medium"
    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3


def test_add_task_missing_title(client):
    """Reject task creation when the title is missing."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()
    response2 = client.post('/api/tasks', json={})
    assert response2.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200
    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2

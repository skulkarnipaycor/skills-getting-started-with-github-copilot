import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

client = TestClient(app, follow_redirects=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the module-level activities dict after every test so mutations
    made by one test never bleed into another."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects():
    response = client.get("/")
    assert response.status_code in (301, 302, 303, 307, 308)
    assert "/static/index.html" in response.headers["location"]


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    expected_activities = [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
        "Drama Club",
        "Art Studio",
        "Debate Team",
        "Science Club",
    ]
    for name in expected_activities:
        assert name in data, f"Activity '{name}' missing from response"


def test_get_activities_structure():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    required_fields = {"description", "schedule", "max_participants", "participants"}
    for name, details in data.items():
        for field in required_fields:
            assert field in details, f"Activity '{name}' missing field '{field}'"
        assert isinstance(details["participants"], list)
        assert isinstance(details["max_participants"], int)


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "newstudent@mergington.edu" in body["message"]
    # Verify the participant was actually added
    assert "newstudent@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_already_registered():
    # "michael@mergington.edu" is pre-seeded in Chess Club
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_unknown_activity():
    response = client.post(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_success():
    # "michael@mergington.edu" is pre-seeded in Chess Club
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "michael@mergington.edu" in body["message"]
    # Verify participant was actually removed
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_unregister_not_registered():
    response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "ghost@mergington.edu"},
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


def test_unregister_unknown_activity():
    response = client.delete(
        "/activities/Underwater Basket Weaving/unregister",
        params={"email": "someone@mergington.edu"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

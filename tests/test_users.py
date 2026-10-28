import pytest
from app.models.user import User


def test_admin_add_user(client, seed_data):
    """Verify administrator can register new users."""
    client.post("/login", data={"email": "admin@test.local", "password": "AdminPass123!"})
    
    res = client.post("/users/add", data={
        "name": "New Developer",
        "email": "dev@test.local",
        "role": "user",
        "department_id": seed_data["dept"].id,
        "password": "Password123!",
        "pin": "5555"
    }, follow_redirects=True)

    assert res.status_code == 200
    u = User.query.filter_by(email="dev@test.local").first()
    assert u is not None
    assert u.name == "New Developer"
    assert u.check_pin("5555") is True


def test_regular_user_cannot_add_user(client, seed_data):
    """Verify non-admin cannot access user addition endpoint."""
    client.post("/login", data={"email": "user@test.local", "password": "UserPass123!"})
    res = client.get("/users/add", follow_redirects=True)
    assert b"Only administrators" in res.data or res.status_code == 403


def test_user_deletion(client, seed_data):
    """Verify admin can delete a user."""
    client.post("/login", data={"email": "admin@test.local", "password": "AdminPass123!"})
    target_id = seed_data["user"].id

    res = client.post(f"/users/{target_id}/delete", follow_redirects=True)
    assert res.status_code == 200
    assert User.query.get(target_id) is None

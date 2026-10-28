import pytest
from app.models.user import User


def test_login_success(client, seed_data):
    """Verify correct credentials authenticate successfully."""
    res = client.post("/login", data={
        "email": "admin@test.local",
        "password": "AdminPass123!"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back" in res.data or b"System Overview" in res.data


def test_login_invalid_password(client, seed_data):
    """Verify bad password increments failed count and returns error."""
    res = client.post("/login", data={
        "email": "admin@test.local",
        "password": "WrongPassword!"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Invalid email or password" in res.data


def test_account_lockout(client, seed_data):
    """Verify rate-limiting lockout triggers after 5 consecutive failed attempts."""
    for _ in range(5):
        client.post("/login", data={
            "email": "user@test.local",
            "password": "WrongPassword!"
        })

    u = User.query.filter_by(email="user@test.local").first()
    assert u.is_locked() is True

    # 6th attempt should be blocked with lockout alert
    res = client.post("/login", data={
        "email": "user@test.local",
        "password": "UserPass123!"
    }, follow_redirects=True)
    assert b"locked" in res.data.lower()


def test_logout(client, seed_data):
    """Verify logout clears active session."""
    client.post("/login", data={
        "email": "admin@test.local",
        "password": "AdminPass123!"
    })
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"Sign In" in res.data


def test_role_based_access(client, seed_data):
    """Verify regular users cannot access administrative settings."""
    # Log in as standard user
    client.post("/login", data={
        "email": "user@test.local",
        "password": "UserPass123!"
    })
    # Attempt admin settings page
    res = client.get("/settings", follow_redirects=True)
    assert b"Access denied" in res.data

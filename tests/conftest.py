import pytest
import numpy as np
from app import create_app
from app.extensions import db
from app.models.department import Department
from app.models.user import User
from app.models.face import FaceEnrollment
from app.services.security_service import SecurityService


@pytest.fixture
def app():
    """Create and configure a clean testing app instance."""
    app_instance = create_app("testing")
    with app_instance.app_context():
        db.create_all()
        yield app_instance
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def seed_data(app):
    """Seeds test department, admin, staff, and standard user."""
    dept = Department(name="Engineering", description="Software & AI")
    db.session.add(dept)
    db.session.flush()

    admin = User(name="Admin User", email="admin@test.local", role="admin", status="active", department_id=dept.id)
    admin.set_password("AdminPass123!")
    admin.set_pin("1234")
    db.session.add(admin)

    staff = User(name="Staff User", email="staff@test.local", role="staff", status="active", department_id=dept.id)
    staff.set_password("StaffPass123!")
    staff.set_pin("4321")
    db.session.add(staff)

    user = User(name="Regular User", email="user@test.local", role="user", status="active", department_id=dept.id)
    user.set_password("UserPass123!")
    user.set_pin("9999")
    db.session.add(user)

    db.session.commit()

    return {
        "dept": dept,
        "admin": admin,
        "staff": staff,
        "user": user,
    }


@pytest.fixture
def dummy_face_embedding():
    """Generates a normalized 512-D float32 vector for mock tests."""
    vec = np.ones(512, dtype=np.float32)
    return vec / np.linalg.norm(vec)

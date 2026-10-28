from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.users import users_bp
from app.routes.recognition import recognition_bp
from app.routes.attendance import attendance_bp
from app.routes.reports import reports_bp
from app.routes.logs import logs_bp
from app.routes.api import api_bp
from app.routes.mood import mood_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "users_bp",
    "recognition_bp",
    "attendance_bp",
    "reports_bp",
    "logs_bp",
    "api_bp",
    "mood_bp",
]

import os
from datetime import datetime, timezone
from flask import Flask, render_template, jsonify, request
from app.config import config_by_name
from app.extensions import db, migrate, login_manager, csrf
from app.routes import (
    auth_bp,
    dashboard_bp,
    users_bp,
    recognition_bp,
    attendance_bp,
    reports_bp,
    logs_bp,
    api_bp,
    mood_bp,
)


def create_app(config_name=None):
    """Application factory for Face Recognition Management System (FRMS)."""
    app = Flask(__name__)

    # Determine configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure required storage directories exist
    os.makedirs(app.config.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)
    os.makedirs(app.config.get("TEMP_UPLOAD_FOLDER", "temp_uploads"), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Proxy fix for reverse proxies & SSL termination (Render, Koyeb, Hugging Face, Nginx)
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    except Exception:
        pass

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(recognition_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(mood_bp)

    # Global context processors for Jinja2 templates
    @app.context_processor
    def inject_global_template_vars():
        return {
            "app_name": "FRMS",
            "app_title": "Face Recognition Management System",
            "current_year": datetime.now(timezone.utc).year,
            "system_now": datetime.now(timezone.utc),
        }

    # Custom HTTP error handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Access forbidden."}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Endpoint not found."}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "error": "Internal server error."}), 500
        return render_template("errors/500.html"), 500

    return app

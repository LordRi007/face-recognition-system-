import os
from app import create_app
from app.extensions import db

# Determine active environment configuration
env_name = os.getenv("FLASK_ENV", "development")
app = create_app(env_name)

# Ensure database tables exist automatically on startup
with app.app_context():
    db.create_all()
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if "mood_logs" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("mood_logs")]
            if "captured_image" not in columns:
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE mood_logs ADD COLUMN captured_image TEXT"))
                    conn.commit()
    except Exception as e:
        print(f"[*] Schema check notice: {e}")

    try:
        from app.models.user import User
        if User.query.first() is None:
            print("[*] No existing users found. Auto-seeding initial admin and demo data...")
            from scripts.seed_data import seed_database
            seed_database(app=app)
    except Exception as e:
        print(f"[*] Auto-seed notice: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = env_name == "development"
    print(f"[*] Starting Face Recognition Management System (FRMS) on http://127.0.0.1:{port}")
    print(f"[*] Environment: {env_name} | Debug: {debug_mode}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)

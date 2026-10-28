import sys
import os
from datetime import datetime, timezone, timedelta, time

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models.department import Department
from app.models.user import User
from app.models.face import FaceEnrollment
from app.models.attendance import Attendance, VerificationLog
from app.models.audit_log import AuditLog
from app.models.mood_log import MoodLog
from app.services.security_service import SecurityService
from app.services.face_service import FaceService
import numpy as np
from PIL import Image, ImageDraw


def seed_database(app=None):
    if app is None:
        env_name = os.getenv("FLASK_ENV", "development")
        app = create_app(env_name)
    with app.app_context():
        print("[*] Creating database tables...")
        db.create_all()

        # 1. Departments
        dept_names = ["Engineering", "Human Resources", "Operations", "Product & Design", "Executive"]
        dept_map = {}
        for name in dept_names:
            dept = Department.query.filter_by(name=name).first()
            if not dept:
                dept = Department(name=name, description=f"{name} corporate division")
                db.session.add(dept)
                db.session.flush()
                print(f"  + Added Department: {name}")
            dept_map[name] = dept

        db.session.commit()

        # 2. Administrator Account
        admin_email = "admin@frms.local"
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                name="System Administrator",
                email=admin_email,
                phone="+1 (555) 019-9000",
                department_id=dept_map["Executive"].id,
                role="admin",
                status="active"
            )
            admin.set_password("AdminPass123!")
            admin.set_pin("1234")
            db.session.add(admin)
            db.session.flush()
            print(f"  + Added Admin: {admin_email} (Pass: AdminPass123! / PIN: 1234)")

        # 3. Staff Account
        staff_email = "staff@frms.local"
        staff = User.query.filter_by(email=staff_email).first()
        if not staff:
            staff = User(
                name="Security Officer Sarah",
                email=staff_email,
                phone="+1 (555) 019-9001",
                department_id=dept_map["Operations"].id,
                role="staff",
                status="active"
            )
            staff.set_password("StaffPass123!")
            staff.set_pin("4321")
            db.session.add(staff)
            db.session.flush()
            print(f"  + Added Staff: {staff_email} (Pass: StaffPass123! / PIN: 4321)")

        # 4. Regular Demo Users
        demo_users_data = [
            ("Dr. Alex Chen", "alex.chen@frms.local", "Engineering", "9876"),
            ("Elena Rostova", "elena.r@frms.local", "Product & Design", "5566"),
            ("Marcus Vance", "marcus.v@frms.local", "Human Resources", "1122"),
            ("Priya Patel", "priya.p@frms.local", "Engineering", "3344"),
            ("Jordan Lee", "jordan.l@frms.local", "Operations", "7788"),
        ]

        created_users = []
        for name, email, dept_name, pin in demo_users_data:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    name=name,
                    email=email,
                    department_id=dept_map[dept_name].id,
                    role="user",
                    status="active"
                )
                user.set_password("UserPass123!")
                user.set_pin(pin)
                db.session.add(user)
                db.session.flush()
                print(f"  + Added User: {email} (Pass: UserPass123! / PIN: {pin})")
            created_users.append(user)

        db.session.commit()

        # 5. Generate Synthetic Biometric Enrollments for Demo Users
        print("[*] Generating encrypted biometric templates...")
        for idx, u in enumerate([admin, staff] + created_users[:3]):
            if not u.face_enrollment:
                # Generate unique synthetic face image for each demo user and extract ArcFace embedding
                img_demo = Image.new("RGB", (640, 480), color=(180 + idx * 10, 190, 200))
                draw_demo = ImageDraw.Draw(img_demo)
                skin = (220 - idx * 15, 180 - idx * 10, 150 - idx * 8)
                draw_demo.ellipse([220, 100, 420, 360], fill=skin)
                draw_demo.ellipse([270, 185 + idx * 3, 300, 205 + idx * 3], fill=(30, 25, 20))
                draw_demo.ellipse([340, 185 + idx * 3, 370, 205 + idx * 3], fill=(30, 25, 20))
                draw_demo.ellipse([290, 285 + idx * 2, 350, 305 + idx * 2], fill=(180, 60, 60))

                arr_demo = np.array(img_demo)[:, :, ::-1]
                vector = FaceService.extract_embedding(arr_demo)
                encrypted_str = SecurityService.encrypt_embedding(vector)

                enrollment = FaceEnrollment(
                    user_id=u.id,
                    encrypted_embedding=encrypted_str,
                    model_name="ArcFace",
                    model_version="1.0",
                    embedding_dimension=512,
                    samples_count=3,
                    quality_score=94.5,
                    consent_version="1.0",
                    consent_timestamp=datetime.now(timezone.utc) - timedelta(days=10),
                    is_active=True
                )
                db.session.add(enrollment)
                print(f"  + Enrolled encrypted ArcFace 512-D for: {u.name}")

        db.session.commit()

        # 6. Generate Past 7 Days Attendance History & Logs
        print("[*] Populating 7 days of realistic attendance & verification records...")
        today = datetime.now(timezone.utc).date()
        all_users = [admin, staff] + created_users

        for day_offset in range(7, -1, -1):
            target_day = today - timedelta(days=day_offset)

            for u in all_users:
                existing_att = Attendance.query.filter_by(user_id=u.id, date=target_day).first()
                if not existing_att:
                    # 85% attendance probability
                    if (u.id + day_offset) % 6 != 0:
                        # On-time vs Late simulation
                        is_late = (u.id + day_offset) % 5 == 0
                        check_in_hour = 9 if is_late else 8
                        check_in_min = 25 if is_late else np.random.randint(40, 58)
                        
                        in_time = datetime.combine(target_day, time(check_in_hour, check_in_min, 0))
                        out_time = datetime.combine(target_day, time(17, np.random.randint(5, 30), 0))

                        att = Attendance(
                            user_id=u.id,
                            date=target_day,
                            check_in=in_time,
                            check_out=out_time,
                            verification_method="facial" if u.has_face_enrolled else "manual_pin",
                            status="late" if is_late else "present",
                            notes="Arrived past cutoff" if is_late else "On-time arrival"
                        )
                        db.session.add(att)

                        # Corresponding verification log
                        v_log = VerificationLog(
                            user_id=u.id,
                            result="success",
                            verification_method="webcam" if u.has_face_enrolled else "alternative_pin",
                            distance_score=float(np.random.uniform(0.12, 0.26)) if u.has_face_enrolled else None,
                            threshold_used=0.30 if u.has_face_enrolled else None,
                            timestamp=in_time,
                            ip_address="192.168.1.10"
                        )
                        db.session.add(v_log)
                    else:
                        # Occasional failed verification log
                        if day_offset <= 2:
                            v_fail = VerificationLog(
                                user_id=u.id,
                                result="failure",
                                verification_method="webcam",
                                distance_score=0.48,
                                threshold_used=0.30,
                                error_code="BIOMETRIC_MISMATCH",
                                timestamp=datetime.combine(target_day, time(8, 50, 0)),
                                ip_address="192.168.1.10"
                            )
                            db.session.add(v_fail)

        # 7. Audit Log Sample Entries
        AuditLog.log(
            action="SYSTEM_INIT",
            target_type="System",
            actor_id=admin.id,
            details="System initialized with production database schema and biometric encryption.",
            ip_address="127.0.0.1"
        )
        AuditLog.log(
            action="USER_CREATED",
            target_type="User",
            target_id=admin.id,
            actor_id=admin.id,
            details="Admin account provisioned.",
            ip_address="127.0.0.1"
        )

        # 8. Seed Historical Face Mood Check-Ins
        print("[*] Populating historical face mood & feeling check-ins...")
        if MoodLog.query.count() == 0:
            mood_samples = [
                ("happy", "Radiant & Cheerful", "😊", 92.4, 0.85, 0.70, "Energized after team standup"),
                ("focused", "Deep Focus & Flow", "🧐", 88.0, 0.40, 0.55, "Deep in algorithm optimization"),
                ("calm", "Peaceful & Centered", "😌", 91.2, 0.60, 0.25, "Relaxing lunch break completed"),
                ("happy", "Radiant & Cheerful", "😊", 95.0, 0.88, 0.72, "Feature launch celebration!"),
                ("neutral", "Balanced Baseline", "😐", 82.5, 0.05, 0.35, "Checking email and planning sprints"),
                ("surprised", "High Alertness & Wonder", "😲", 86.0, 0.45, 0.88, "Surprised by unexpected benchmark speedup"),
                ("fatigued", "Fatigued / Low Energy", "🥱", 78.5, -0.20, 0.20, "Long debugging afternoon, taking coffee break"),
            ]
            for day_offset in range(7, -1, -1):
                target_dt = datetime.now(timezone.utc) - timedelta(days=day_offset, hours=2)
                sample = mood_samples[day_offset % len(mood_samples)]
                m_log = MoodLog(
                    user_id=admin.id,
                    dominant_mood=sample[0],
                    feeling_tag=sample[1],
                    emoji=sample[2],
                    confidence=sample[3],
                    valence=sample[4],
                    arousal=sample[5],
                    note=sample[6],
                    context="camera_tracker",
                    timestamp=target_dt
                )
                db.session.add(m_log)

        db.session.commit()
        print("[+] Database seeding complete! You are ready to log in.")


if __name__ == "__main__":
    seed_database()

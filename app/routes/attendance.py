from datetime import datetime, timezone, date
from flask import Blueprint, render_template, request, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from app.models.attendance import Attendance
from app.models.department import Department
from app.models.user import User
from app.services.attendance_service import AttendanceService
from app.services.report_service import ReportService

attendance_bp = Blueprint("attendance", __name__, url_prefix="/attendance")


@attendance_bp.route("")
@login_required
def index():
    # Target date defaults to today
    date_str = request.args.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now(timezone.utc).date()
    else:
        target_date = datetime.now(timezone.utc).date()

    dept_id = request.args.get("dept", type=int)

    # Base query for attendance records on target date
    query = Attendance.query.filter_by(date=target_date).join(User, Attendance.user_id == User.id)
    if dept_id:
        query = query.filter(User.department_id == dept_id)

    attendances = query.order_by(Attendance.check_in.desc().nullslast()).all()
    departments = Department.query.order_by(Department.name.asc()).all()

    # Aggregate stats for today
    present_count = len([a for a in attendances if a.status in ("present", "late")])
    late_count = len([a for a in attendances if a.status == "late"])

    # Calculate absent users (active users without attendance record on target date)
    attended_user_ids = {a.user_id for a in attendances}
    absent_users_query = User.query.filter(User.status == "active", ~User.id.in_(attended_user_ids))
    if dept_id:
        absent_users_query = absent_users_query.filter(User.department_id == dept_id)
    absent_users = absent_users_query.all()

    return render_template(
        "attendance/index.html",
        attendances=attendances,
        absent_users=absent_users,
        departments=departments,
        target_date=target_date,
        selected_dept=dept_id,
        present_count=present_count,
        late_count=late_count,
        absent_count=len(absent_users)
    )


@attendance_bp.route("/history")
@login_required
def history():
    user_id = request.args.get("user_id", type=int)
    
    # If not staff, force view to own history
    if not current_user.is_staff or not user_id:
        user_id = current_user.id
        target_user = current_user
    else:
        target_user = User.query.get_or_404(user_id)

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    query = Attendance.query.filter_by(user_id=user_id)
    if start_date_str:
        try:
            sd = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date >= sd)
        except ValueError:
            pass
    if end_date_str:
        try:
            ed = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.date <= ed)
        except ValueError:
            pass

    records = query.order_by(Attendance.date.desc()).all()

    return render_template(
        "attendance/history.html",
        records=records,
        target_user=target_user,
        start_date=start_date_str,
        end_date=end_date_str
    )


@attendance_bp.route("/correct/<int:attendance_id>", methods=["POST"])
@login_required
def correct(attendance_id):
    if not current_user.is_admin:
        flash("Only administrators can adjust attendance records.", "danger")
        return redirect(url_for("attendance.index"))

    new_status = request.form.get("status", "present")
    in_time_str = request.form.get("check_in_time")
    out_time_str = request.form.get("check_out_time")
    reason = request.form.get("reason", "").strip()

    if not reason:
        flash("An audit reason is required for manual attendance correction.", "danger")
        return redirect(url_for("attendance.index"))

    target_attendance = Attendance.query.get_or_404(attendance_id)

    new_in = None
    if in_time_str:
        try:
            t = datetime.strptime(in_time_str, "%H:%M").time()
            new_in = datetime.combine(target_attendance.date, t)
        except ValueError:
            pass

    new_out = None
    if out_time_str:
        try:
            t = datetime.strptime(out_time_str, "%H:%M").time()
            new_out = datetime.combine(target_attendance.date, t)
        except ValueError:
            pass

    result = AttendanceService.admin_correct_attendance(
        attendance_id=attendance_id,
        admin_id=current_user.id,
        new_status=new_status,
        new_check_in=new_in,
        new_check_out=new_out,
        reason=reason
    )

    if result["success"]:
        flash(result["message"], "success")
    else:
        flash(result["message"], "danger")

    return redirect(url_for("attendance.index", date=target_attendance.date.isoformat()))


@attendance_bp.route("/export")
@login_required
def export_csv():
    if not current_user.is_staff:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    start_date = None
    end_date = None
    sd_str = request.args.get("start_date")
    ed_str = request.args.get("end_date")
    dept_id = request.args.get("dept", type=int)

    if sd_str:
        try:
            start_date = datetime.strptime(sd_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if ed_str:
        try:
            end_date = datetime.strptime(ed_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    csv_data = ReportService.export_attendance_csv(
        start_date=start_date,
        end_date=end_date,
        department_id=dept_id
    )

    filename = f"attendance_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

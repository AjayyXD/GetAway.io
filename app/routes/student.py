import uuid

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.database import Database
from app.utils import require_role

student_bp = Blueprint("student", __name__)
db = Database()


@student_bp.route("/student_dashboard")
def dashboard():
    if not require_role("Student"):
        return redirect(url_for("auth.login"))
    return render_template("student_dashboard.html", name=session["name"])


@student_bp.route("/create_leave", methods=["GET", "POST"])
def create_leave():
    if not require_role("Student"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        leave_data = {
            "leave_id":      str(uuid.uuid4()),
            "rollno":        session["user_id"],
            "reason":        request.form.get("reason"),
            "start_date":    request.form.get("start_date"),
            "end_date":      request.form.get("end_date"),
            "out_time":      request.form.get("out_time"),
            "in_time":       request.form.get("in_time"),
            "student_phone": request.form.get("student_phone"),
            "parent_phone":  request.form.get("parent_phone"),
            "address":       request.form.get("address"),
            "total_days":    int(request.form.get("total_days", 0)),
            "working_days":  int(request.form.get("working_days", 0)),
        }

        # Validate required fields
        optional = {"working_days"}
        for field, value in leave_data.items():
            if field not in optional and not str(value).strip():
                flash(f"{field.replace('_', ' ').title()} cannot be empty.")
                return redirect(url_for("student.create_leave"))

        if leave_data["end_date"] <= leave_data["start_date"]:
            flash("End date must be after start date.")
            return redirect(url_for("student.create_leave"))

        if leave_data["total_days"] < 0:
            flash("Total days cannot be negative.")
            return redirect(url_for("student.create_leave"))

        is_suspended = bool(session.get("suspended"))
        if db.insert_leave_request(leave_data, is_suspended):
            return redirect(url_for("student.view_leaves"))

        flash("Failed to submit leave request. Please try again.")
        return redirect(url_for("student.create_leave"))

    return render_template("createleave.html")


@student_bp.route("/student_view_leaves")
def view_leaves():
    if not require_role("Student"):
        return redirect(url_for("auth.login"))
    try:
        leaves = db.view_leaves("Student", session["user_id"])
        return render_template("student_view_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("student.dashboard"))
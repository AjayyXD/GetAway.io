from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.database import Database
from app.utils import require_role

admin_bp = Blueprint("admin", __name__)
db = Database()


# ---------------------------------------------------------------------------
# Dean
# ---------------------------------------------------------------------------

@admin_bp.route("/dean_dashboard")
def dean_dashboard():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))
    return render_template("dean_dashboard.html", name=session["name"])


@admin_bp.route("/dean_pending_leaves", methods=["GET", "POST"])
def dean_pending_leaves():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        leave_id = request.form.get("leave_id")
        action = request.form.get("action_type")

        if action == "Reject":
            success = db.reject_leave(leave_id, "dean_status")
            word = "rejected"
        else:
            success = db.approve_leave(leave_id, "dean_status")
            word = "approved"

        if success:
            flash(f"Leave {leave_id} {word}.", "success")
        else:
            flash(f"Failed to update leave {leave_id}.", "error")
        return redirect(url_for("admin.dean_pending_leaves"))

    try:
        leaves = db.view_leaves("Dean", session["user_id"])
        return render_template("dean_pending_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("admin.dean_dashboard"))


# ---------------------------------------------------------------------------
# HOD
# ---------------------------------------------------------------------------

@admin_bp.route("/hod_dashboard")
def hod_dashboard():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))
    return render_template("hod_dashboard.html", name=session["name"])


@admin_bp.route("/hod_pending_leaves", methods=["GET", "POST"])
def hod_pending_leaves():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        leave_id = request.form.get("leave_id")
        action = request.form.get("action_type")

        if action == "Reject":
            success = db.reject_leave(leave_id, "hod_status")
            word = "rejected"
        else:
            success = db.approve_leave(leave_id, "hod_status")
            word = "approved"

        if success:
            flash(f"Leave {leave_id} {word}.", "success")
        else:
            flash(f"Failed to update leave {leave_id}.", "error")
        return redirect(url_for("admin.hod_pending_leaves"))

    try:
        leaves = db.view_leaves("Hod", session["user_id"])
        return render_template("hod_pending_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("admin.hod_dashboard"))


# ---------------------------------------------------------------------------
# Academics
# ---------------------------------------------------------------------------

@admin_bp.route("/academics_dashboard")
def academics_dashboard():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))
    return render_template("academics_dashboard.html", name=session["name"])


@admin_bp.route("/academics_pending_leaves", methods=["GET", "POST"])
def academics_pending_leaves():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        leave_id = request.form.get("leave_id")
        if db.approve_leave(leave_id, "admin_status"):
            flash(f"Leave {leave_id} approved.", "success")
        else:
            flash(f"Failed to approve leave {leave_id}.", "error")
        return redirect(url_for("admin.academics_pending_leaves"))

    try:
        leaves = db.view_leaves("Admin", session["user_id"])
        return render_template("academics_pending_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("admin.academics_dashboard"))


@admin_bp.route("/academics_approved_leaves")
def academics_approved_leaves():
    if not require_role("Admin"):
        return redirect(url_for("auth.login"))
    try:
        leaves = db.view_leaves("academics2", session["user_id"])
        return render_template("academics_approved_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("admin.academics_dashboard"))
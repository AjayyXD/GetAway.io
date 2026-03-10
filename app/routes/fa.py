from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.database import Database
from app.utils import require_role

fa_bp = Blueprint("fa", __name__)
db = Database()


@fa_bp.route("/fa_dashboard")
def dashboard():
    if not require_role("FA"):
        return redirect(url_for("auth.login"))
    return render_template("fa_dashboard.html", name=session["name"])


@fa_bp.route("/fa_pending_leaves", methods=["GET", "POST"])
def pending_leaves():
    if not require_role("FA"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        leave_id = request.form.get("leave_id")
        remarks = request.form.get("remarks")
        action = request.form.get("action_type")

        if action == "Reject":
            success = db.reject_leave(leave_id, "fa_status", remarks=remarks)
            word = "rejected"
        else:
            success = db.approve_leave(leave_id, "fa_status", remarks=remarks)
            word = "approved"

        if success:
            flash(f"Leave {leave_id} {word}.", "success")
        else:
            flash(f"Failed to update leave {leave_id}.", "error")
        return redirect(url_for("fa.pending_leaves"))

    try:
        leaves = db.view_leaves("FA", session["user_id"])
        return render_template("fa_pending_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("fa.dashboard"))
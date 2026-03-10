from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.database import Database
from app.utils import require_role

warden_bp = Blueprint("warden", __name__)
db = Database()


@warden_bp.route("/warden_dashboard")
def dashboard():
    if not require_role("Warden"):
        return redirect(url_for("auth.login"))
    return render_template("warden_dashboard.html", name=session["name"])


@warden_bp.route("/warden_pending_leaves", methods=["GET", "POST"])
def pending_leaves():
    if not require_role("Warden"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        leave_id = request.form.get("leave_id")
        if db.approve_leave(leave_id, "warden_status"):
            flash(f"Leave {leave_id} approved.", "success")
        else:
            flash(f"Failed to approve leave {leave_id}.", "error")
        return redirect(url_for("warden.pending_leaves"))

    try:
        leaves = db.view_leaves("Warden", session["user_id"])
        return render_template("warden_pending_leaves.html", leaves=leaves)
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for("warden.dashboard"))
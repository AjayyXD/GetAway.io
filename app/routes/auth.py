import bcrypt
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.database import Database

auth_bp = Blueprint("auth", __name__)
db = Database()


@auth_bp.route("/")
def home():
    return render_template("home.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        role = request.form.get("role")

        user = db.get_user_data(user_id, role)

        if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            session["user_id"] = user_id
            session["role"] = role
            session["name"] = user["name"]

            if role == "Student":
                session["suspended"] = user["suspended"]
                return redirect(url_for("student.dashboard"))
            if role == "FA":
                return redirect(url_for("fa.dashboard"))
            if role == "Warden":
                return redirect(url_for("warden.dashboard"))
            if role == "Admin":
                admin_role = user.get("role")
                if admin_role == "Dean":
                    return redirect(url_for("admin.dean_dashboard"))
                if admin_role == "Hod":
                    return redirect(url_for("admin.hod_dashboard"))
                return redirect(url_for("admin.academics_dashboard"))

        flash("Invalid credentials or role. Please try again.")
        return render_template("login_form.html")

    return render_template("login_form.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
from flask import flash, session


def require_role(*roles):
    """
    Check that the current session belongs to one of the allowed roles.
    Returns True if authorised, False otherwise (and flashes an error).
    """
    if "user_id" not in session or session.get("role") not in roles:
        flash("Unauthorized access.", "error")
        return False
    return True
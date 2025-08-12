# my_app/api/auth.py
import frappe
from frappe import _
from frappe.auth import LoginManager

@frappe.whitelist(allow_guest=True)
def login_and_get_token():
    """
    POST JSON or form-data:
      { "usr": "email@example.com", "pwd": "password" }

    Returns JSON with API key, API secret, and user info.
    """
    data = frappe.local.form_dict or frappe.request.get_json(force=True, silent=True) or {}
    usr = data.get("usr") or data.get("username") or data.get("email")
    pwd = data.get("pwd") or data.get("password")

    if not usr or not pwd:
        frappe.throw(_("Username and password are required"), frappe.AuthenticationError)

    try:
        # 1️⃣ Authenticate
        lm = LoginManager()
        lm.authenticate(user=usr, pwd=pwd)
        lm.post_login()

        # 2️⃣ Create new API key + secret for this login
        user_doc = frappe.get_doc("User", frappe.session.user)
        api_key, api_secret = _generate_new_api_token(user_doc)

        # 3️⃣ Return success with tokens + user info
        return {
            "status": "success",
            "user": {
                "name": user_doc.name,
                "email": user_doc.email,
                "full_name": user_doc.full_name,
                "roles": [r.role for r in user_doc.roles]
            },
            "token": {
                "api_key": api_key,
                "api_secret": api_secret
            }
        }

    except frappe.AuthenticationError:
        frappe.local.response.http_status_code = 401
        return {"status": "error", "message": _("Invalid login credentials")}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Login and Token API Error")
        frappe.local.response.http_status_code = 500
        return {"status": "error", "message": str(e)}

def _generate_new_api_token(user_doc):
    """Generates a fresh API key & secret for the given user."""
    import secrets

    # Generate API key & secret
    api_key = secrets.token_urlsafe(16)
    api_secret = secrets.token_urlsafe(32)

    # Store in the User record (overwrite old ones)
    user_doc.api_key = api_key
    user_doc.api_secret = api_secret
    user_doc.save(ignore_permissions=True)

    return api_key, api_secret



# apps/education_api/education_api/api/login.py

import frappe
from frappe import _
from frappe.utils.password import check_password, update_password

@frappe.whitelist(allow_guest=False)
def reset_password():
    """
    Reset password for the currently logged-in user.

    POST JSON or form-data:
    {
        "previous_password": "oldPass123",
        "new_password": "NewPass456",
        "confirm_password": "NewPass456"
    }

    Requires authentication.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("You must be logged in to change your password"), frappe.PermissionError)

    data = frappe.local.form_dict or frappe.request.get_json(force=True, silent=True) or {}
    previous_password = data.get("previous_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    # Validate inputs
    if not previous_password or not new_password or not confirm_password:
        frappe.throw(_("All fields (previous_password, new_password, confirm_password) are required"))

    if new_password != confirm_password:
        frappe.throw(_("New password and confirm password do not match"))

    try:
        # Check old password
        check_password(frappe.session.user, previous_password)

        # Update password
        update_password(frappe.session.user, new_password)

        return {
            "status": "success",
            "message": _("Password updated successfully")
        }

    except frappe.AuthenticationError:
        frappe.throw(_("Previous password is incorrect"), frappe.AuthenticationError)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Reset Password API Error")
        frappe.local.response.http_status_code = 500
        return {"status": "error", "message": str(e)}

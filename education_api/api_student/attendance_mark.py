import frappe
from frappe import _

# for marking the attendance
@frappe.whitelist()
def mark_attendance(student, option, reference, status, date=None):
    if "Instructor" not in frappe.get_roles(frappe.session.user):
       frappe.local.response["http_status_code"] = 403
       frappe.local.response["message"] = "Only instructors can mark attendance"
       return {
        "http_status_code": 403,
        "message": "Only instructors can mark attendance"
      }


    if not date:
        date = frappe.utils.today()

    # check if already exists
    existing = frappe.get_value(
        "Student Attendance",
        {"student": student, "date": date, option: reference},
        "name"
    )

    if existing:
        # update existing
        attendance = frappe.get_doc("Student Attendance", existing)
        attendance.status = status
        attendance.instructor = frappe.session.user
        attendance.save(ignore_permissions=True)
        msg = "Attendance updated successfully"
    else:
        # create new
        attendance = frappe.get_doc({
            "doctype": "Student Attendance",
            "student": student,
            option: reference, 
            "status": status,
            "date": date,
            "instructor": frappe.session.user
        })
        attendance.insert(ignore_permissions=True)
        msg = "Attendance marked successfully"

    frappe.db.commit()
    return {"message": msg, "attendance_id": attendance.name}


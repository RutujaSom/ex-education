
# Pagination
# Gettign the student data

import frappe
from education.api.utils import get_paginated_data

@frappe.whitelist(allow_guest=True)
def get_students(page=1, page_size=10, search=None, sort_by="first_name", sort_order="asc"):
    """
    Get paginated students with search & sorting
    """

    page = int(page)
    page_size = int(page_size)

    students = get_paginated_data(
        doctype="Student",
        fields=["name", "first_name", "last_name", "student_email_id"],
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        search_fields=["first_name", "last_name", "student_email_id"]  
    )
    for student in students["results"]:
        enrolled_courses = frappe.get_all(
            "Course Enrollment",
            filters={"student": student["name"]},
            fields=["course", "enrollment_date"]
        )
        student["enrolled_courses"] = enrolled_courses

    return students

# Create new student data

@frappe.whitelist(allow_guest=True)
def create_student(first_name, last_name=None, student_email_id=None):
    """
    Create a new student record
    """
    try:
        student = frappe.get_doc({
            "doctype": "Student",
            "first_name": first_name,
            "last_name": last_name,
            "student_email_id": student_email_id
        })
        student.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Student created successfully", "student": student.name}
    except Exception as e:
        frappe.log_error(title="Create Student Error", message=str(e))
        return {"status": "error", "message": str(e)}



#  Updating the Student Data

@frappe.whitelist(allow_guest=True)
def update_student(student_id, first_name=None, last_name=None, student_email_id=None):
    """
    Update existing student record
    """
    try:
        student = frappe.get_doc("Student", student_id)
        if first_name: student.first_name = first_name
        if last_name: student.last_name = last_name
        if student_email_id: student.student_email_id = student_email_id
        student.save(ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": "Student updated successfully", "student": student.name}
    except Exception as e:
        frappe.log_error(title="Update Student Error", message=str(e))
        return {"status": "error", "message": str(e)}


# Delete The Student Data

@frappe.whitelist(allow_guest=True)
def delete_student(student_id):
    """
    Delete student record
    """
    try:
        frappe.delete_doc("Student", student_id, ignore_permissions=True)
        frappe.db.commit()
        return {"status": "success", "message": f"Student {student_id} deleted successfully"}
    except Exception as e:
        frappe.log_error(title="Delete Student Error", message=str(e))
        return {"status": "error", "message": str(e)}

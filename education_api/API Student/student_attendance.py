import frappe
from calendar import monthrange

# Student Attandance 
@frappe.whitelist()  
def get_student_attendance(student_id=None, month=None, page=1, page_size=10):
    """
    Fetch student attendance with filters and pagination:
    - If student_id is provided -> show that student's attendance
    - If month is provided -> filter attendance by that month
    - If none provided -> show all students' attendance
    """

    filters = {}

    # Filter by student
    if student_id:
        filters["student"] = student_id
    if month:
        year, m = map(int, month.split("-"))
        start_date = f"{month}-01"
        end_date = f"{month}-{monthrange(year, m)[1]}"
        filters["date"] = ["between", [start_date, end_date]]

    # Pagination logic
    page = int(page)
    page_size = int(page_size)
    start = (page - 1) * page_size

    total_count = frappe.db.count("Student Attendance", filters=filters)

    attendance = frappe.get_all(
        "Student Attendance",
        filters=filters,
        fields=[
            "name",
            "date",
            "student",
            "student_name",
            "status",
            "course_schedule",
            "student_group"
        ],
        order_by="date desc",
        start=start,
        page_length=page_size
    )

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "results": attendance
    }

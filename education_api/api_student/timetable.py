import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_student_timetable(student_id):
    """
    Fetch timetable (Course Schedule) for a given Student (via Student Group)
    """

    #  Fetch student name
    student_name = frappe.get_value("Student", student_id, "student_name")

    #Find the student group(s) for this student
    student_groups = frappe.get_all(
        "Student Group Student",
        filters={"student": student_id},
        fields=["parent as student_group"]
    )

    if not student_groups:
        return {
            "student_id": student_id,
            "student_name": student_name,
            "message": "No Student Group found for this student"
        }

    timetables = []
    for sg in student_groups:
        schedules = frappe.get_all(
            "Course Schedule",
            filters={"student_group": sg.student_group},
            fields=[
                "name",
                "course",
                "schedule_date",
                "from_time",
                "to_time",
                "room",
                "instructor"
            ],
            order_by="schedule_date asc, from_time asc"
        )
        timetables.append({
            "student_group": sg.student_group,
            "timetable": schedules
        })

    return {
        "student_id": student_id,
        "student_name": student_name,  
        "timetables": timetables
    }

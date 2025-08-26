# Course with the Topics
import frappe
from education.api.utils import get_paginated_data

@frappe.whitelist(allow_guest=True)
def get_courses(page=1, page_size=10, search=None, sort_by=None, sort_order="asc"):
    if not sort_by:
        sort_by = "modified"

    courses = get_paginated_data(
        doctype="Course",
        fields=["name", "course_name", "description", "department"],
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=int(page),
        page_size=int(page_size)
    )

    for course in courses["results"]:
        topics = frappe.get_all(
            "Course Topic",
            filters={"parent": course["name"]},
            fields=["topic", "topic_name"]
        )
        course["topics"] = topics

    return courses

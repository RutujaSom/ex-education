# Program API for gettin g Data 

import frappe
from education_api.api_student.utils import get_paginated_data 

@frappe.whitelist(allow_guest=True)
def get_programs(search=None, sort_by="modified", sort_order="desc", page=1, page_size=10):
    # Fetch paginated programs
    programs = get_paginated_data(
        doctype="Program",
        fields=["name", "program_name", "department"],
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=int(page),
        page_size=int(page_size),
        search_fields=["program_name", "department"]
    )

    #  available courses for each program
    for program in programs["results"]:
        courses = frappe.get_all(
            "Program Course",
            filters={"parent": program["name"]},
            fields=["course", "course_name"]
        )
        program["available_courses"] = courses

    return programs


# For creating the new Program 
@frappe.whitelist(allow_guest=True)
def create_program(program_name, department):
    doc = frappe.get_doc({
        "doctype": "Program",
        "program_name": program_name,
        "department": department
    })
    doc.insert(ignore_permissions=True)
    return doc


# for Update the Progran

@frappe.whitelist(allow_guest=True)
def update_program(program_name, program_code=None, department=None):
    try:
        program = frappe.get_doc("Program", program_name)
        if department:
            program.department = department
        program.save(ignore_permissions=True)
        return {"status": "success", "message": f"Program {program_name} updated successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


#  for deleting the program data
@frappe.whitelist(allow_guest=True)
def delete_program(program_name):
    try:
        frappe.delete_doc("Program", program_name, ignore_permissions=True)
        return {"status": "success", "message": f"Program {program_name} deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
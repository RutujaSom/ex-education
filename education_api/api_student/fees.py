import frappe

# fees Structure

@frappe.whitelist(allow_guest=True)
def get_fee_structure(program):
    """
    Get Fee Structure with components for a given Program
    """
    fee_structures = frappe.get_all(
        "Fee Structure",
        filters={"program": program},
        fields=["name", "program", "academic_year", "academic_term", "total_amount"]
    )

    if not fee_structures:
        return {"message": f"No fee structure found for program {program}"}

    result = []
    for fs in fee_structures:
        # Get Fee Components (child table)
        components = frappe.get_all(
            "Fee Component",
            filters={"parent": fs.name},
            fields=["fees_category", "amount", "discount", "total"]
        )
        
        fs["components"] = components
        result.append(fs)

    return result

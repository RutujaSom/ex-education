import frappe

def get_paginated_data(
    doctype, 
    fields=None, 
    filters=None, 
    search=None, 
    sort_by="creation", 
    sort_order="asc", 
    page=1, 
    page_size=10,
    search_fields=None
):
    """
    Generic function for fetching paginated, filtered, searchable, and sortable data.
    """
    filters = filters or {}
    or_filters = []

    # Add search condition
    if search and search_fields:
        for f in search_fields:
            or_filters.append([doctype, f, "like", f"%{search}%"])

    # Pagination start
    start = (page - 1) * page_size

    # Fetch data with OR filters
    data = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        or_filters=or_filters,
        order_by=f"{sort_by} {sort_order}",
        start=start,
        page_length=page_size
    )

    # Count manually because frappe.db.count doesn't support or_filters
    total_count = len(frappe.get_all(
        doctype,
        filters=filters,
        or_filters=or_filters,
        pluck="name"  # fetch only names for efficiency
    ))

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "results": data
    }

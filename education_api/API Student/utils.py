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

    if search and search_fields:
        search_filters = []
        for f in search_fields:
            search_filters.append([doctype, f, "like", f"%{search}%"])
        filters["or_filters"] = search_filters

    total_count = frappe.db.count(doctype, filters=filters)

    start = (page - 1) * page_size

    data = frappe.get_all(
        doctype,
        fields=fields,
        filters=filters,
        order_by=f"{sort_by} {sort_order}",
        start=start,
        page_length=page_size
    )

    return {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "results": data
    }

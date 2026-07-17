#!/usr/bin/env python
"""
Standalone (non-management-command) script to create/backfill Admin, HR, RM,
Employee and approval-role permissions for ANY organization.

This script does NOT need to live inside the Django app's
management/commands/ folder. It can be placed anywhere on disk, as long as
it's run using the same Python environment (virtualenv) as the Django app,
since it needs to import Django/DB drivers and connect to the same database.

USAGE
-----
Run for a single org by org_code (primary key):
    python setup_org_roles_external.py --org_code LONARTECH

Run for ALL organizations:
    python setup_org_roles_external.py --all

Dry run (preview only, nothing is saved):
    python setup_org_roles_external.py --org_code LONARTECH --dry_run

Re-run safely:
    Roles are matched with get_or_create() on (org, role_code), so running
    this again for an org that already has roles will NOT create duplicates.
    Only missing roles/permissions for that org will be created.

BEFORE RUNNING
--------------
1. Update PROJECT_ROOT below to the folder that contains manage.py /
   manage_prod.py for your Django project.
2. Update DJANGO_SETTINGS_MODULE below to match the value used by
   manage_prod.py (open that file and copy the exact string).
3. Activate the same virtualenv your Django app uses before running this
   script, e.g.:
       source /path/to/hrms_env/bin/activate
       python setup_org_roles_external.py --org_code LONARTECH --dry_run
"""

import os
import sys
import argparse

# ------------------------------------------------------------------
# 1. Point to your Django project so Python can find master/authentication
#    Adjust this to the folder that CONTAINS manage.py / manage_prod.py
# ------------------------------------------------------------------
PROJECT_ROOT = "/home/excellminds/python_projects/HRMS/hrms365-excellentminds"
sys.path.insert(0, PROJECT_ROOT)

# ------------------------------------------------------------------
# 2. Tell Django which settings module to use.
#    Check manage_prod.py for the exact string it sets, e.g.:
#    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms365.settings')
# ------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms365.settings_prod")  # <-- CHANGE THIS

# ------------------------------------------------------------------
# 3. Boot Django before importing any models
# ------------------------------------------------------------------
import django  # noqa: E402
django.setup()

# ------------------------------------------------------------------
# 4. Now it's safe to import Django/app internals
# ------------------------------------------------------------------
from django.db import transaction  # noqa: E402

# ---- Adjust these imports to match your actual app/model locations ----
from master.models import (  # noqa: E402
    Organizations,
    Module,
    ModulePermission,
)
from authentication.models import Role  # noqa: E402


# ============================================================
# Role -> module filter definitions (unchanged from the command)
# ============================================================

ROLE_DEFINITIONS = [
    {"role_code": "ADMIN", "role_name": "Organization Admin"},
    {"role_code": "HR", "role_name": "HR"},
    {"role_code": "RM", "role_name": "Reporting Manager"},
    {"role_code": "EMPLOYEE", "role_name": "Employee"},
    {"role_code": "DATA_APPROVAL", "role_name": "Data Approval"},
    {"role_code": "EXPENSE_APPROVAL", "role_name": "Expense Approval"},
    {"role_code": "SAVING_PLAN_APPROVAL", "role_name": "Saving Plan Approval"},
    {"role_code": "LOAN_AND_ADVANCE_APPROVAL", "role_name": "Loan And Advance Approval"},
    {"role_code": "NO_DUES_APPROVAL", "role_name": "No Dues Approval"},
    {"role_code": "ASSET_APPROVAL", "role_name": "Asset Approval"},
    {"role_code": "TICKET_MANAGER", "role_name": "Ticket Manager"},
    {"role_code": "TIME_OFFICE", "role_name": "Time Office"},
]

SIMPLE_CRUD_APPROVAL_ROLES = {
    "DATA_APPROVAL",
    "EXPENSE_APPROVAL",
    "SAVING_PLAN_APPROVAL",
    "LOAN_AND_ADVANCE_APPROVAL",
    "NO_DUES_APPROVAL",
    "ASSET_APPROVAL",
    "TICKET_MANAGER",
}

EMPLOYEE_VIEW_ONLY_MODULES = {
    "HOLIDAY",
    "HDAY-WOFF-LIST",
    "SHIFT_ROSTER",
    "EMP-VAR-PAY",
    "EMP-SALARY",
    "ASSET-ALLOCATIO",
    "TICKET-ACT-LOG",
}

EMPLOYEE_MODULE_CODES = [
    "EMPLOYEE_TBL", "HOLIDAY", "ATT_STATUS", "BIOMETIC_ATT", "MNTH_ATTE",
    "PUNCH_ATT", "ATTENDANCE", "LEAVE", "REQUEST", "SAVING_PLAN",
    "VEHILEDETAILS", "TRAVEL-PLAN", "EXPENSES-TRAN", "EXPENSE-VOUCHER",
    "HDAY-WOFF-LIST", "ROASTER", "SHIFT-CHANGE", "EMP-POLICY",
    "EMP-VAR-PAY", "EMP-SALARY", "SALARY-ADVANCE", "OPT-HOLIDAY-REQ",
    "RESIG-REQ", "FNF-REPORT", "NO-DUES-REQ", "ASSET-ACKNOWLED",
    "ASSET-RETURN", "ASSET-REPORT", "ASSET-ALLOCATIO", "TICKET-TRANS",
    "TICKET-COMM-ATTACH", "TICKET-FEEDBACK", "TICKET-ACT-LOG", "TICKET-FAQ",
]

RM_MODULE_CODES = ["REQ-APPROVAL", "EXP-APPROVAL", "ATTENDANCE", "JOBREQUISITIONS"]
APPROVAL_MODULE_CODES = {"APPROVAL": ["DATA_APPROVAL", "SAVING_PLAN_APPROVAL"]}

APPROVAL_ROLE_MODULE_MAP = {
    "EXPENSE_APPROVAL": ["EXP-APPROVAL"],
    "LOAN_AND_ADVANCE_APPROVAL": ["LA-APPR"],
    "NO_DUES_APPROVAL": ["NO-DUES-REQ", "NO-DUES-CLEARAN"],
    "ASSET_APPROVAL": [
        "ASSET-VERIFICAT", "ASSET-RETURN", "ASSET-REPORT", "ASSET-MASTER",
        "ASSET-CAT", "ASSET-ALLOCATIO", "ASSET-ACKNOWLED", "ASSET-MGT",
    ],
    "TICKET_MANAGER": [
        "TICKET-SUBJECT", "TICKET-TRANS", "TICKET-ACP-TRANS",
        "TICKET-COMM-ATTACH", "TICKET-FEEDBACK", "TICKET-ACT-LOG",
        "TICKET-FAQ-CAT", "TICKET-FAQ",
    ],
    "TIME_OFFICE": [
        "PUNCH_ATT", "ATTENDANCE", "MNTH_ATTE",
    ],
}


def get_modules_for_role(role_code):
    if role_code in ("ADMIN", "HR"):
        return Module.objects.all().exclude(module_code__in=["REQUEST", "EMP-POLICY"])
    if role_code == "RM":
        return Module.objects.filter(module_code__in=RM_MODULE_CODES)
    if role_code in ("DATA_APPROVAL", "SAVING_PLAN_APPROVAL"):
        return Module.objects.filter(module_code__in=["APPROVAL"])
    if role_code in APPROVAL_ROLE_MODULE_MAP:
        return Module.objects.filter(module_code__in=APPROVAL_ROLE_MODULE_MAP[role_code])
    if role_code == "EMPLOYEE":
        return Module.objects.filter(module_code__in=EMPLOYEE_MODULE_CODES)
    return Module.objects.none()


def build_permission_kwargs(role_code, module):
    """Returns the CRUD flags to use for a given role/module combination."""
    if role_code in ("ADMIN", "HR"):
        if str(module.module_group.module_group_code) == "MASTER":
            return dict(is_view=True, is_create=False, is_update=False,
                        is_delete=False, is_import=False, is_export=False)
        return dict(is_view=True, is_create=True, is_update=True,
                    is_delete=True, is_import=True, is_export=True)

    if role_code == "RM":
        if module.module_code in ("LEAVE", "ATTENDANCE", "APPROVAL"):
            return dict(is_view=True, is_create=True, is_update=True,
                        is_delete=True, is_import=False, is_export=False)
        return dict(is_view=True, is_create=False, is_update=True,
                    is_delete=False, is_import=False, is_export=False)

    if role_code in SIMPLE_CRUD_APPROVAL_ROLES:
        return dict(is_view=True, is_create=True, is_update=True,
                    is_delete=True, is_import=False, is_export=False)

    if role_code == "EMPLOYEE":
        if module.module_code in EMPLOYEE_VIEW_ONLY_MODULES:
            return dict(is_view=True, is_create=False, is_update=False,
                        is_delete=False, is_import=False, is_export=False)
        return dict(is_view=True, is_create=True, is_update=True,
                    is_delete=True, is_import=False, is_export=False)

    # Fallback: no access
    return dict(is_view=False, is_create=False, is_update=False,
                is_delete=False, is_import=False, is_export=False)


def setup_roles_for_org(org, dry_run=False):
    """
    Creates any missing roles + module permissions for a single org.
    Safe to re-run: existing (org, role_code) roles are skipped, and
    existing (role, module) permissions are skipped too.
    """
    created_roles = []
    created_perms = 0

    for role_def in ROLE_DEFINITIONS:
        role_code = role_def["role_code"]

        role_obj, role_created = Role.objects.get_or_create(
            org=org,
            role_code=role_code,
            defaults={
                "role_name": role_def["role_name"],
                "created_by": "Script",
                "updated_by": "Script",
            },
        )
        if role_created:
            created_roles.append(role_code)
            print(f"  [+] Created role {role_code} for org={org}")
        else:
            print(f"  [=] Role {role_code} already exists for org={org}, checking permissions...")

        modules = get_modules_for_role(role_code)
        for module in modules:
            perm_kwargs = build_permission_kwargs(role_code, module)

            existing = ModulePermission.objects.filter(
                module_id=module, role=role_obj, org=org,
            ).first()
            if existing:
                continue  # already has a permission row for this module

            if dry_run:
                created_perms += 1
                continue

            ModulePermission.objects.create(
                module_id=module,
                role=role_obj,
                org=org,
                created_by="Script",
                updated_by="Script",
                **perm_kwargs,
            )
            created_perms += 1

    return created_roles, created_perms


def main():
    parser = argparse.ArgumentParser(
        description="Backfill role & module permissions for an organization (or all organizations)."
    )
    parser.add_argument("--org_code", type=str, help="Primary key (org_code) of the organization to run for")
    parser.add_argument("--all", action="store_true", help="Run for every organization")
    parser.add_argument("--dry_run", action="store_true", help="Preview without saving anything")
    args = parser.parse_args()

    if not any([args.org_code, args.all]):
        print("ERROR: Provide one of --org_code or --all")
        sys.exit(1)

    if args.all:
        orgs = Organizations.objects.all()
    else:
        orgs = Organizations.objects.filter(org_code=args.org_code)

    if not orgs.exists():
        print("ERROR: No matching organization(s) found for the given filter.")
        sys.exit(1)

    for org in orgs:
        print(f"Processing org: {org}")
        with transaction.atomic():
            created_roles, created_perms = setup_roles_for_org(org, dry_run=args.dry_run)
            if args.dry_run:
                transaction.set_rollback(True)

        if created_roles:
            print(f"  Roles created: {', '.join(created_roles)}")
        else:
            print("  No new roles needed.")
        print(
            f"  Permissions created: {created_perms}"
            + (" (dry run, not saved)" if args.dry_run else "")
        )

    print("Done.")


if __name__ == "__main__":
    main()
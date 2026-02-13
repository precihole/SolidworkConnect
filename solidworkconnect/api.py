import frappe
import base64
from frappe.utils.file_manager import save_file


@frappe.whitelist()

def create_item_from_drawing(item_code, item_group, item_name=None, stock_uom=None,make=None, department=None,revise=0):
    revise = int(revise)

    # -------------------------
    # EXISTING ITEM
    # -------------------------
    if frappe.db.exists("Item", item_code):
        item = frappe.get_doc("Item", item_code)

        # Update editable fields (even if not revising)
        if item_name:
            item.item_name = item_name

        if item_group:
            item.item_group = item_group

        if stock_uom:
            item.stock_uom = stock_uom

        if department:
            item.custom_department=department

        if make:
            item.custom_make=make

        # Only revision logic
        if revise:
            current_rev = item.revision_c or "R0"
            try:
                rev_no = int(current_rev.replace("R", ""))
            except Exception:
                rev_no = 0

            item.revision_c = f"R{rev_no + 1}"

        item.save(ignore_permissions=True)

        return {
            "status": "revised" if revise else "updated",
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "stock_uom": item.stock_uom,
            "revision": item.revision_c,
            "make":item.custom_make
        }

    # -------------------------
    # NEW ITEM
    # -------------------------
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_name or item_code,
        "item_group": item_group,
        "stock_uom": stock_uom or "Nos",
        "is_stock_item": 1,
        "custom_department":department,
        "revision_c": "R0",
        "custom_make":make
    })
    

    item.insert(ignore_permissions=True)

    return {
        "status": "created",
        "item_code": item.item_code,
        "item_name": item.item_name,
        "item_group": item.item_group,
        "stock_uom": item.stock_uom,
        "revision": "R0",
        "is_private":0
    }


# @frappe.whitelist()
# def attach_pdf_to_item(item_code, file_name, file_content):
#     """
#     If item is new → attach drawing
#     If item exists → remove old drawing PDF and attach new one
#     """

#     import base64
#     from frappe.utils.file_manager import save_file

#     # Find existing DRAWING PDFs only (by filename pattern)
#     existing_files = frappe.get_all(
#         "File",
#         filters={
#             "attached_to_doctype": "Item",
#             "attached_to_name": item_code,
#             "file_name": ["like", f"{item_code}%.pdf"]
#         },
#         pluck="name"
#     )

#     # Delete old drawing PDFs (if any)
#     for file_name_db in existing_files:
#         frappe.delete_doc("File", file_name_db, force=1)

#     # Decode new PDF
#     pdf_bytes = base64.b64decode(file_content)

#     # Attach new drawing PDF
#     file_doc = save_file(
#         fname=file_name,
#         content=pdf_bytes,
#         dt="Item",
#         dn=item_code,
#         is_private=1
#     )

#     return {
#         "status": "attached",
#         "item_code": item_code,
#         "file_url": file_doc.file_url
#     }

@frappe.whitelist()
def attach_pdf_to_item(item_code, file_content):
    import base64
    import re

    # Get Item Name
    item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
    safe_item_name = re.sub(r'[\\/:*?"<>|]+', '-', item_name)
    final_file_name = f"{item_code} {safe_item_name}.pdf"

    existing_files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Item",
            "attached_to_name": item_code,
            "file_name": ["like", "%.pdf"]
        },
        pluck="name"
    )

    for file_name in existing_files:
        frappe.delete_doc("File", file_name, ignore_permissions=True)

    filedata = base64.b64decode(file_content)

    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": final_file_name,
        "attached_to_doctype": "Item",
        "attached_to_name": item_code,
        "content": filedata,
        "is_private": 0
    })

    file_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "file_name": final_file_name,
        "deleted_old_files": len(existing_files)
    }


@frappe.whitelist()
def get_item_groups():
    return frappe.get_all(
        "Item Group",
        filters={"is_group": 0},
        fields=["name"],
        order_by="name"
    )
@frappe.whitelist()
def get_stock_uoms():
    return frappe.get_all(
        "UOM",
        filters={"enabled":1},
        fields=["name"],
        order_by="name"
    )
# @frappe.whitelist()
# def get_departments():
#     frappe.set_user("Administrator")

#     return frappe.db.get_all(
#         "Department",
#         fields=["name"],
#         order_by="name"
#     )

@frappe.whitelist()
def get_departments():
    frappe.set_user("Administrator")

    allowed_departments = [
        "PURCHASE - PMTPL",
        "MANUFACTURING - PMTPL",
        "PRODUCTION - PMTPL",
        "ASSEMBLY - PMTPL"
    ]

    return frappe.db.get_all(
        "Department",
        filters={"name": ["in", allowed_departments]},
        fields=["name"],
        order_by="name"
    )

@frappe.whitelist()
def get_allowed_departments():
    return [
        "PURCHASE - PMTPL",
        "MANUFACTURING - PMTPL",
        "PRODUCTION - PMTPL",
        "ASSEMBLY - PMTPL"
    ]


@frappe.whitelist()
def get_modification_types():
    return frappe.get_all(
        "Modification Type",
        fields=["name"],
        order_by="name"
    )


@frappe.whitelist()
def get_item_details(item_code):
    if not frappe.db.exists("Item", item_code):
        return {
            "exists": False
        }

    item = frappe.get_doc("Item", item_code)

    return {
        "exists": True,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "item_group": item.item_group,
        "stock_uom": item.stock_uom,
        "revision":item.revision_c or "R0",
        "department":item.custom_department,
        "make":item.custom_make
    }
@frappe.whitelist()
def get_design_department_employees():
    return frappe.get_all(
        "Employee",
        filters={
            "department": "DESIGN - PMTPL",
            "status": "Active"
        },
        fields=[
            "name",
            "employee_name",
            "user_id",
            "department"
        ],
        order_by="employee_name"
    )
@frappe.whitelist()
def get_item_groups():
    return frappe.get_all(
        "Item Group",
        fields=["name"],
        order_by="name"
    )
@frappe.whitelist()
def get_dmrn_defaults():
    user = frappe.session.user

    if not user or user == "Guest":
        return {}

    emp = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["employee_name", "department"],
        as_dict=True
    )

    return {
        "originator": emp.employee_name if emp else frappe.utils.get_fullname(user),
        "approver": "",
        "department": emp.department if emp else ""
    }

@frappe.whitelist()
def create_dmrn(
    item_code,
    originator,
    approved_by,
    from_department,
    design_engineer,
    old_revision,
    new_revision,
    to_department=None,
    modification_type=None,
    reason_for_change=None,
    nature_of_change=None,
    remark=None,
    file_name=None,
    file_content=None
):
    frappe.log_error("DEBUG REMARK RECEIVED", str(remark))
    dmrn = frappe.new_doc("DMRN")

    dmrn.posting_date = frappe.utils.today()
    dmrn.originator = originator
    dmrn.approved_by = approved_by
    dmrn.from_department = from_department
    dmrn.design_engineer = design_engineer
    dmrn.to_department = to_department
    dmrn.type = modification_type
    dmrn.remarks=remark
    # Child row
    child = dmrn.append("dmrn_details", {
        "item_code": item_code,
        "old_revision": old_revision,
        "new_revision": new_revision,
        "posting_date": frappe.utils.today(),
        "change_reason": reason_for_change,
        "change_nature": nature_of_change,
        "remarks":remark
    })

    # Insert parent first
    dmrn.insert(ignore_permissions=True)

    # Attach PDF to child field
    if file_name and file_content:
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "DMRN Detail",   # ⚠ verify exact name
            "attached_to_name": child.name,
            "attached_to_field": "new_drawing",
            "content": file_content,
            "decode": True,
            "is_private": 0
        }).insert(ignore_permissions=True)

        child.new_drawing = file_doc.file_url
        child.db_update()

    frappe.db.commit()

    return {
        "status": "success",
        "dmrn": dmrn.name
    }


import frappe

@frappe.whitelist(methods=["POST"])
def update_item_fields(**kwargs):

    item_code = kwargs.get("item_code")
    if not item_code:
        frappe.throw("item_code is required")

    item = frappe.get_doc("Item", item_code)

    # Optional updates
    if kwargs.get("item_name"):
        item.item_name = kwargs.get("item_name")

    if kwargs.get("item_group"):
        item.item_group = kwargs.get("item_group")

    if kwargs.get("stock_uom"):
        item.stock_uom = kwargs.get("stock_uom")

    if kwargs.get("department"):
        item.custom_department = kwargs.get("department")

    if kwargs.get("make"):
        item.custom_make = kwargs.get("make")

    item.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "updated",
        "item_code": item.item_code
    }

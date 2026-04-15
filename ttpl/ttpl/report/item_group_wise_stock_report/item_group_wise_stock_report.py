import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = filters or {}
    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def validate_filters(filters):
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are required"))
    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be greater than To Date"))


def get_columns():
    return [
        {"label": _("#"), "fieldname": "idx", "fieldtype": "Int", "width": 50},
        {"label": _("ERP Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 280},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 180},

        {"label": _("O/B Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 100},
        {"label": _("O/B Rate"), "fieldname": "opening_rate", "fieldtype": "Currency", "width": 110},
        {"label": _("O/B Amount"), "fieldname": "opening_amount", "fieldtype": "Currency", "width": 130},

        {"label": _("Received Qty"), "fieldname": "received_qty", "fieldtype": "Float", "width": 110},
        {"label": _("Received Rate"), "fieldname": "received_rate", "fieldtype": "Currency", "width": 110},
        {"label": _("Received Amount"), "fieldname": "received_amount", "fieldtype": "Currency", "width": 130},

        {"label": _("Issued Qty"), "fieldname": "issued_qty", "fieldtype": "Float", "width": 100},
        {"label": _("C/B Qty"), "fieldname": "closing_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Avg Rate Inc GST"), "fieldname": "avg_rate_inc_gst", "fieldtype": "Currency", "width": 140},
    ]


def get_data(filters):
    conditions = ""
    values = {"from_date": filters.get("from_date"), "to_date": filters.get("to_date")}

    if filters.get("item_group"):
        item_groups = get_child_item_groups(filters.get("item_group"))
        conditions += " AND item.item_group IN %(item_groups)s"
        values["item_groups"] = tuple(item_groups)

    items = frappe.db.sql(f"""
        SELECT name AS item_code, item_name, item_group
        FROM `tabItem` item
        WHERE item.is_stock_item = 1 AND item.disabled = 0
        {conditions}
        ORDER BY item.item_group, item.name
    """, values, as_dict=1)

    if not items:
        return []

    item_codes = [d.item_code for d in items]
    values["item_codes"] = tuple(item_codes)

    sle_data = frappe.db.sql("""
        SELECT 
            sle.item_code,
            SUM(CASE WHEN sle.posting_date < %(from_date)s THEN sle.actual_qty ELSE 0 END) AS opening_qty,
            SUM(CASE WHEN sle.posting_date < %(from_date)s THEN sle.stock_value_difference ELSE 0 END) AS opening_value,
            
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty > 0 
                THEN sle.actual_qty ELSE 0 END) AS received_qty,
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty > 0 
                THEN sle.stock_value_difference ELSE 0 END) AS received_value,

            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0 
                THEN ABS(sle.actual_qty) ELSE 0 END) AS issued_qty,
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0 
                THEN ABS(sle.stock_value_difference) ELSE 0 END) AS issued_value

        FROM `tabStock Ledger Entry` sle
        WHERE sle.item_code IN %(item_codes)s
        GROUP BY sle.item_code
    """, values, as_dict=1)

    sle_map = {d.item_code: d for d in sle_data}

    data = []
    sr_no = 1

    for item in items:
        sle = sle_map.get(item.item_code, {})

        opening_qty    = flt(sle.get("opening_qty"))
        opening_value  = flt(sle.get("opening_value"))
        received_qty   = flt(sle.get("received_qty"))
        received_value = flt(sle.get("received_value"))
        issued_qty     = flt(sle.get("issued_qty"))
        issued_value   = flt(sle.get("issued_value"))

        closing_qty    = opening_qty + received_qty - issued_qty
        closing_value  = opening_value + received_value - issued_value

        # ===================== MAIN FIX - Handle Negative & Zero Values =====================
        # This prevents negative or zero amount when quantity is positive

        if opening_qty > 0.0001 and opening_value <= 0:
            opening_value = abs(opening_value)      # Convert negative/zero to positive

        if received_qty > 0.0001 and received_value <= 0:
            received_value = abs(received_value)

        # Safe rate calculations
        opening_rate   = opening_value / opening_qty if opening_qty != 0 else 0
        received_rate  = received_value / received_qty if received_qty != 0 else 0
        closing_rate   = closing_value / closing_qty if closing_qty != 0 else 0

        # Average Rate Inc GST
        total_in_qty   = opening_qty + received_qty
        total_in_value = opening_value + received_value
        avg_rate_inc_gst = total_in_value / total_in_qty if total_in_qty != 0 else 0
        # ===================================================================================

        # Skip items with no activity
        if not (opening_qty or received_qty or issued_qty or abs(closing_qty) > 0.0001):
            continue

        data.append({
            "idx": sr_no,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,

            "opening_qty": opening_qty,
            "opening_rate": opening_rate,
            "opening_amount": opening_value,

            "received_qty": received_qty,
            "received_rate": received_rate,
            "received_amount": received_value,

            "issued_qty": issued_qty,
            "closing_qty": closing_qty,
        
            "avg_rate_inc_gst": avg_rate_inc_gst,
        })
        sr_no += 1

    return data


def get_child_item_groups(parent):
    groups = frappe.db.sql("""
        SELECT name FROM `tabItem Group`
        WHERE lft >= (SELECT lft FROM `tabItem Group` WHERE name=%s)
          AND rgt <= (SELECT rgt FROM `tabItem Group` WHERE name=%s)
    """, (parent, parent), as_list=1)
    return [g[0] for g in groups]
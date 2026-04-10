
import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    filters = filters or {}

    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)

    return columns, data


# ---------------- VALIDATION ----------------

def validate_filters(filters):
    if not filters.get("from_date"):
        frappe.throw(_("From Date is required"))

    if not filters.get("to_date"):
        frappe.throw(_("To Date is required"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be greater than To Date"))


# ---------------- COLUMNS ----------------

def get_columns():
    return [
        {"label": _("#"), "fieldname": "idx", "fieldtype": "Int", "width": 50},
        {"label": _("ERP Code"), "fieldname": "item_code", "fieldtype": "Data", "width": 140},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 260},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 180},

        {"label": _("O/B"), "fieldname": "opening_balance", "fieldtype": "Float", "width": 100},
        {"label": _("O/B Rate"), "fieldname": "opening_rate", "fieldtype": "Float", "width": 100},
        {"label": _("O/B Amount"), "fieldname": "opening_amount", "fieldtype": "Currency", "width": 120},

        {"label": _("Received"), "fieldname": "received_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Received Rate"), "fieldname": "received_rate", "fieldtype": "Float", "width": 100},
        {"label": _("Received Amount"), "fieldname": "received_amount", "fieldtype": "Currency", "width": 120},

        {"label": _("Issued"), "fieldname": "issued_qty", "fieldtype": "Float", "width": 100},
        {"label": _("C/B"), "fieldname": "closing_balance", "fieldtype": "Float", "width": 100},
        {"label": _("Average Rate Inc Gst"), "fieldname": "avg_rate_inc_gst", "fieldtype": "Currency", "width": 160},
    ]


# ---------------- MAIN DATA ----------------

def get_data(filters):
    conditions = ""
    values = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }

    # Item Group Filter (with children)
    if filters.get("item_group"):
        item_groups = get_child_item_groups(filters.get("item_group"))
        conditions += " AND item.item_group IN %(item_groups)s"
        values["item_groups"] = tuple(item_groups)

    # Get Items
    items = frappe.db.sql(f"""
        SELECT item.name AS item_code, item.item_name, item.item_group
        FROM `tabItem` item
        WHERE item.is_stock_item = 1
          AND item.disabled = 0
          {conditions}
        ORDER BY item.item_group, item.name
    """, values, as_dict=1)

    if not items:
        return []

    item_codes = [d.item_code for d in items]

    # 🔥 OPTIMIZED QUERY
    sle_data = frappe.db.sql("""
        SELECT 
            sle.item_code,

            -- Fetch Opening Qty from the last entry before the date range
            (SELECT COALESCE(sle2.qty_after_transaction, 0)
             FROM `tabStock Ledger Entry` sle2
             WHERE sle2.item_code = sle.item_code
               AND sle2.posting_date < %(from_date)s
             ORDER BY sle2.posting_date DESC, sle2.creation DESC LIMIT 1) as opening_qty,

            -- Fetch Opening Value from the last entry before the date range
            (SELECT COALESCE(sle3.stock_value, 0)
             FROM `tabStock Ledger Entry` sle3
             WHERE sle3.item_code = sle.item_code
               AND sle3.posting_date < %(from_date)s
             ORDER BY sle3.posting_date DESC, sle3.creation DESC LIMIT 1) as opening_value,

            -- Received Qty & Value
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty > 0 THEN sle.actual_qty ELSE 0 END) AS received_qty,
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty > 0 THEN sle.stock_value_difference ELSE 0 END) AS received_value,

            -- Issued Qty & Value
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0 THEN ABS(sle.actual_qty) ELSE 0 END) AS issued_qty,
            SUM(CASE WHEN sle.posting_date BETWEEN %(from_date)s AND %(to_date)s AND sle.actual_qty < 0 THEN sle.stock_value_difference ELSE 0 END) AS issued_value

        FROM `tabStock Ledger Entry` sle
        WHERE sle.item_code IN %(item_codes)s
        GROUP BY sle.item_code
    """, {
        "item_codes": tuple(item_codes),
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
    }, as_dict=1)

    sle_map = {d.item_code: d for d in sle_data}

    data = []
    sr_no = 1

    for item in items:
        sle = sle_map.get(item.item_code, {})

        opening_qty = flt(sle.get("opening_qty"))
        opening_value = flt(sle.get("opening_value"))
        
        received_qty = flt(sle.get("received_qty"))
        received_value = flt(sle.get("received_value"))
        
        issued_qty = flt(sle.get("issued_qty"))

        closing_qty = opening_qty + received_qty - issued_qty

        # 🔥 UPDATED AVERAGE RATE CALCULATION
        # Formula: (opening_value + received_value) / (opening_qty + received_qty)
        total_qty_in = opening_qty + received_qty
        total_value_in = opening_value + received_value
        
        avg_rate = total_value_in / total_qty_in if total_qty_in else 0

        # Rates
        opening_rate = opening_value / opening_qty if opening_qty else 0
        received_rate = received_value / received_qty if received_qty else 0

        # Skip if no movement or balance
        if not (opening_qty or received_qty or issued_qty or closing_qty):
            continue

        data.append({
            "idx": sr_no,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,

            "opening_balance": opening_qty,
            "opening_rate": opening_rate,
            "opening_amount": opening_value,

            "received_qty": received_qty,
            "received_rate": received_rate,
            "received_amount": received_value,

            "issued_qty": issued_qty,
            "closing_balance": closing_qty,
            "avg_rate_inc_gst": avg_rate,
        })

        sr_no += 1

    return data


# ---------------- ITEM GROUP TREE ----------------

def get_child_item_groups(parent):
    groups = frappe.db.sql("""
        SELECT name FROM `tabItem Group`
        WHERE lft >= (SELECT lft FROM `tabItem Group` WHERE name=%s)
        AND rgt <= (SELECT rgt FROM `tabItem Group` WHERE name=%s)
    """, (parent, parent), as_list=1)

    return [g[0] for g in groups]

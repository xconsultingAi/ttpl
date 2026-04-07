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
    if not filters.get("from_date"):
        frappe.throw(_("From Date is required"))

    if not filters.get("to_date"):
        frappe.throw(_("To Date is required"))

    if getdate(filters.get("from_date")) > getdate(filters.get("to_date")):
        frappe.throw(_("From Date cannot be greater than To Date"))


def get_columns():
    return [
        {
            "label": _("#"),
            "fieldname": "idx",
            "fieldtype": "Int",
            "width": 50
        },
        {
            "label": _("ERP Code"),
            "fieldname": "item_code",
            "fieldtype": "Data",
            "width": 140,
            "align": "left"
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 260,
            "align": "left"
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Data",
            "width": 180,
            "align": "left"
        },
        {
            "label": _("O/B"),
            "fieldname": "opening_balance",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Received"),
            "fieldname": "received_qty",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Issued"),
            "fieldname": "issued_qty",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("C/B"),
            "fieldname": "closing_balance",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Average Rate Inc Gst"),
            "fieldname": "avg_rate_inc_gst",
            "fieldtype": "Currency",
            "width": 160
        }
    ]


def get_data(filters):
    conditions = ""
    values = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date")
    }

    if filters.get("item_group"):
        item_groups = get_child_item_groups(filters.get("item_group"))
        conditions += " AND item.item_group IN %(item_groups)s"
        values["item_groups"] = tuple(item_groups)

    items = frappe.db.sql("""
        SELECT
            item.name AS item_code,
            item.item_name,
            item.item_group
        FROM `tabItem` item
        WHERE item.is_stock_item = 1
          AND item.disabled = 0
          {conditions}
        ORDER BY item.item_group, item.name
    """.format(conditions=conditions), values, as_dict=1)

    if not items:
        return []

    item_codes = [d.item_code for d in items]

    opening_map = get_opening_balance(item_codes, filters.get("from_date"))
    received_map = get_received_qty(item_codes, filters.get("from_date"), filters.get("to_date"))
    issued_map = get_issued_qty(item_codes, filters.get("from_date"), filters.get("to_date"))
    avg_rate_map = get_average_rate_inc_gst(item_codes, filters.get("from_date"), filters.get("to_date"))

    data = []
    current_group = None
    sr_no = 1

    for item in items:
        opening = flt(opening_map.get(item.item_code))
        received = flt(received_map.get(item.item_code))
        issued = flt(issued_map.get(item.item_code))
        closing = opening + received - issued
        avg_rate = flt(avg_rate_map.get(item.item_code))

        if not (opening or received or issued or closing):
            continue

        if current_group != item.item_group:
            current_group = item.item_group

          

        data.append({
            "idx": sr_no,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "opening_balance": opening,
            "received_qty": received,
            "issued_qty": issued,
            "closing_balance": closing,
            "avg_rate_inc_gst": avg_rate,
            "is_group": 0
        })
        sr_no += 1

    return data


def get_child_item_groups(item_group):
    groups = frappe.db.sql("""
        SELECT name
        FROM `tabItem Group`
        WHERE lft >= (SELECT lft FROM `tabItem Group` WHERE name = %(item_group)s)
          AND rgt <= (SELECT rgt FROM `tabItem Group` WHERE name = %(item_group)s)
    """, {"item_group": item_group}, as_list=1)

    return [g[0] for g in groups] if groups else [item_group]


def get_opening_balance(item_codes, from_date):
    if not item_codes:
        return {}

    data = frappe.db.sql("""
        SELECT
            item_code,
            SUM(actual_qty) AS qty
        FROM `tabStock Ledger Entry`
        WHERE posting_date < %(from_date)s
          AND is_cancelled = 0
          AND item_code IN %(item_codes)s
        GROUP BY item_code
    """, {
        "from_date": from_date,
        "item_codes": tuple(item_codes)
    }, as_dict=1)

    return {d.item_code: flt(d.qty) for d in data}


def get_received_qty(item_codes, from_date, to_date):
    if not item_codes:
        return {}

    data = frappe.db.sql("""
        SELECT
            item_code,
            SUM(actual_qty) AS qty
        FROM `tabStock Ledger Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND is_cancelled = 0
          AND actual_qty > 0
          AND item_code IN %(item_codes)s
        GROUP BY item_code
    """, {
        "from_date": from_date,
        "to_date": to_date,
        "item_codes": tuple(item_codes)
    }, as_dict=1)

    return {d.item_code: flt(d.qty) for d in data}


def get_issued_qty(item_codes, from_date, to_date):
    if not item_codes:
        return {}

    data = frappe.db.sql("""
        SELECT
            item_code,
            ABS(SUM(actual_qty)) AS qty
        FROM `tabStock Ledger Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND is_cancelled = 0
          AND actual_qty < 0
          AND item_code IN %(item_codes)s
        GROUP BY item_code
    """, {
        "from_date": from_date,
        "to_date": to_date,
        "item_codes": tuple(item_codes)
    }, as_dict=1)

    return {d.item_code: flt(d.qty) for d in data}


def get_average_rate_inc_gst(item_codes, from_date, to_date):
    if not item_codes:
        return {}

    data = frappe.db.sql("""
        SELECT
            pii.item_code,
            SUM(pii.qty) AS total_qty,
            SUM(
                IFNULL(pii.amount, 0) +
                IFNULL(
                    CASE
                        WHEN pi.net_total > 0 THEN (pii.amount / pi.net_total) * pi.total_taxes_and_charges
                        ELSE 0
                    END,
                    0
                )
            ) AS total_amount_with_tax
        FROM `tabPurchase Invoice Item` pii
        INNER JOIN `tabPurchase Invoice` pi
            ON pi.name = pii.parent
        WHERE pi.docstatus = 1
          AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND pii.item_code IN %(item_codes)s
        GROUP BY pii.item_code
    """, {
        "from_date": from_date,
        "to_date": to_date,
        "item_codes": tuple(item_codes)
    }, as_dict=1)

    result = {}
    for row in data:
        if flt(row.total_qty):
            result[row.item_code] = flt(row.total_amount_with_tax) / flt(row.total_qty)

    return result
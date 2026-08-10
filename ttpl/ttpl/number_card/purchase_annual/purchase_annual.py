import frappe


@frappe.whitelist()
def purchase_annual():
	query = """SELECT
        SUM(grand_total)
        FROM `tabPurchase Invoice`
        WHERE docstatus = 1
        AND YEAR(posting_date) = YEAR(CURRENT_DATE())
    """

	value = frappe.db.sql(query)
	return {"value": value, "fieldtype": "Currency"}

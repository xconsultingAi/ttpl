import frappe


@frappe.whitelist()
def get_account_balance():
	"""
	Returns the total balance of selected stock-related accounts as a single Currency value.
	"""

	query = """
        SELECT
            SUM(debit - credit) AS balance
        FROM
            `tabGL Entry`
        WHERE
            `account` IN (
                '10203001 - STORE & SPARES - TTPL',
                '10205001 - STOCK IN TRADE - TTPL',
                '10205002 - STOCK IN TRANSIT - TTPL',
                '10205004 - HEATER FUEL MATERIAL - TTPL',
                '10206001 - Polyester Virging - TTPL',
                '10206002 - Viscose Virgin - TTPL',
                '10206003 - Polyester Pet Re-Cycle - TTPL',
                '10206004 - Cotton - TTPL',
                '10206005 - PP Cardfly - TTPL',
                '10206006 - Mix Material - TTPL',
                '10206007 - RAW MATERIAL (ALL TYPES) - TTPL',
                '10207003 - FINISHED GOODS (ALL GSM STOCK IN HAND) - TTPL',
                '10209000 - WORK IN PROCESS - TTPL'
            )
            AND is_cancelled = 0

    """

	value = frappe.db.sql(query)[0][0] or 0.0
	return {"value": value, "fieldtype": "Currency"}

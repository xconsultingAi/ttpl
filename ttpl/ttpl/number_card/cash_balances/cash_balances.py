import frappe


@frappe.whitelist()
def get_cash_balances():
	accounts = ["10202001 - CASH IN HAND HEAD OFFICE - TTPL", "10202002 - CASH IN HAND FACTORY - TTPL"]

	company = "Tapal Tex Pvt. Ltd"
	balance = 0.0

	for account in accounts:
		if frappe.db.exists("Account", account):
			# Get balance from GL Entry
			result = frappe.db.sql(
				"""
                SELECT SUM(debit) - SUM(credit) AS balance
                FROM `tabGL Entry`
                WHERE account = %s AND company = %s
            """,
				(account, company),
				as_dict=True,
			)

			account_balance = result[0].balance or 0.0
			balance += account_balance

	return {"value": balance, "fieldtype": "Currency"}

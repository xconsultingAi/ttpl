import frappe

from ttpl.accounts import DEFAULT_COMPANY, get_total_balance


@frappe.whitelist()
def calculate_trade_debtors_balance(company: str = DEFAULT_COMPANY):
	account_names = [
		"10211001 - Nonwoven - TTPL",
		"10211002 - Trading - TTPL",
		"10211003 - Exports - TTPL",
	]

	return get_total_balance(account_names, company)

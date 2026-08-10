import frappe

from ttpl.accounts import DEFAULT_COMPANY, get_total_balance


@frappe.whitelist()
def calculate_running_finance_loan(company: str = DEFAULT_COMPANY):
	account_names = [
		"20201001 - PRINCIPAL SHORT TERM LOAN-BAFL - TTPL",
		"20201002 - PRINCIPAL SHORT TERM LOAN- PCICL - TTPL",
	]

	return get_total_balance(account_names, company)

import frappe

from ttpl.accounts import DEFAULT_COMPANY, get_total_balance


@frappe.whitelist()
def calculate_longterm_loan(company: str = DEFAULT_COMPANY):
	account_names = [
		"20108001 - LONG TERM LOAN  BANK ALFALAH LTD ISLAMIC - TTPL",
		"20108002 - LONGTERM LOAN from PAK CHINA INVESTMENT - TTPL",
	]

	return get_total_balance(account_names, company)

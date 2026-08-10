import frappe

from ttpl.accounts import DEFAULT_COMPANY, get_total_balance


@frappe.whitelist()
def get_bank_balances(company: str = DEFAULT_COMPANY):
	account_names = [
		"10201001 - BANK ALFALAH LTD ISLAMIC - GB - TTPL",
		"10201002 - HABIB METRO - DHA VIII - TTPL",
		"10201003 - MEEZAN BANK LIMITED - DHA VIII - TTPL",
		"10201004 - BANK AL HABIB DHA Phase VIII Branch - TTPL",
		"10201005 - Bank Alfalah Chak Jhumra - TTPL",
		"10201006 - BANK ALFALAH KARACHI - TTPL",
		"10201007 - Al BARAKA BANK LIMITED - TTPL",
	]

	return get_total_balance(account_names, company)

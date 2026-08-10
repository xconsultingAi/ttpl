import frappe

from ttpl.accounts import DEFAULT_COMPANY, get_total_balance


@frappe.whitelist()
def calculate_creditors(company: str = DEFAULT_COMPANY):
	account_names = [
		"20202001 - STORE SUPPLIERS - TTPL",
		"20202002 - RAW MATERIAL SUPPLIERS - TTPL",
		"20202003 - PACKING MATERIAL SUPPLIER - TTPL",
		"20202004 - BROKER COMMISSION ON RAW MATERIAL - TTPL",
		"20202005 - BROKER COMMISSION ON LOCAL SALE - TTPL",
		"20202006 - BROKER COMMISSION ON EXPORT SALE - TTPL",
		"20202007 - SERVICES CREDITORS - TTPL",
		"20202008 - FREIGHT PAYABLE ON FG SALE - TTPL",
		"20202009 - OTHER PAYABLES - TTPL",
	]

	return get_total_balance(account_names, company)

import frappe
import frappe.defaults
import frappe.utils
from frappe.desk.query_report import run


@frappe.whitelist()
def rm_received_value():
	from_date = frappe.utils.get_year_start(frappe.utils.today())
	to_date = frappe.utils.get_year_ending(frappe.utils.today())
	company = frappe.defaults.get_user_default("company")

	filters = {
		"from_date": from_date,
		"to_date": to_date,
		"company": company,
	}

	data = run("Item-wise Purchase Register", filters)

	result = data.get("result", [])
	# Sum up the total values
	total_value = 0.0
	for row in result:
		if isinstance(row, dict) and row.get("item_group") == "Raw Material":
			total_value += float(row.get("total", 0) or 0)
		elif isinstance(row, list):
			# If it's a list, find the correct index (optional fallback)
			pass
	return {"value": total_value, "fieldtype": "Currency"}

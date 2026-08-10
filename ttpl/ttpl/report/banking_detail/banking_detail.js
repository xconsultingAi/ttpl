// Copyright (c) 2025, ashuar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Banking Detail"] = {
	filters: [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: __("From Date"),
			reqd: "1",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: __("To Date"),
			reqd: "1",
			default: frappe.datetime.get_today(),
		},
	],
};

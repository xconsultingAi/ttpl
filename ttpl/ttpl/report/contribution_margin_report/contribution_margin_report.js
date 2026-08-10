// Copyright (c) 2025, ashuar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Contribution Margin Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.nowdate(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			default: frappe.datetime.nowdate(),
			reqd: 1,
		},
	],
};

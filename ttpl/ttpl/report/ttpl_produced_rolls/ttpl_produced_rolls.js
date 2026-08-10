// Copyright (c) 2026, ashuar and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["TTPL Produced Rolls"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "work_order",
			label: __("Work Order"),
			fieldtype: "Link",
			options: "Work Order",
		},
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "only_in_stock",
			label: __("Show Only Rolls In Stock"),
			fieldtype: "Check",
			default: 0,
		},
	],
};

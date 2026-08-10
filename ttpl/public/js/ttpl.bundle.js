frappe.provide("frappe.utils");

frappe.utils.get_number_system = function (country) {
	return [
		{
			divisor: 1.0e12,
			symbol: __("T", null, "Number system"),
		},
		{
			divisor: 1.0e9,
			symbol: __("B", null, "Number system"),
		},
		{
			divisor: 1.0e6,
			symbol: __("M", null, "Number system"),
		},
		{
			divisor: 1.0e3,
			symbol: __("K", null, "Number system"),
		},
	];
};

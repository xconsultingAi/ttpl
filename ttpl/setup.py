"""
Custom fields and property setters owned by the TTPL app.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

CUSTOM_FIELDS = {
	"Work Order": [
		{
			"fieldname": "roll_no_base",
			"label": "Roll No Base",
			"fieldtype": "Data",
			"insert_after": "qty",
			"allow_on_submit": 1,
			"description": "Rolls produced from this order are numbered &lt;base&gt;-1, &lt;base&gt;-2 and so on.",
		}
	],
	"Delivery Note": [
		{
			"fieldname": "production_section",
			"label": "Production Reference",
			"fieldtype": "Section Break",
			"insert_after": "set_warehouse",
		},
		{
			"fieldname": "production_document_type",
			"label": "Fetch Rolls From",
			"fieldtype": "Select",
			"options": "\nWork Order\nJob Card",
			"insert_after": "production_section",
		},
		{
			"fieldname": "production_document",
			"label": "Production Document",
			"fieldtype": "Dynamic Link",
			"options": "production_document_type",
			"depends_on": "production_document_type",
			"insert_after": "production_document_type",
		},
		{
			"fieldname": "production_column_break",
			"fieldtype": "Column Break",
			"insert_after": "production_document",
		},
		{
			"fieldname": "get_rolls",
			"label": "Get Rolls",
			"fieldtype": "Button",
			"depends_on": "production_document",
			"insert_after": "production_column_break",
		},
	],
	"Delivery Note Item": [
		{
			"fieldname": "work_order",
			"label": "Work Order",
			"fieldtype": "Link",
			"options": "Work Order",
			"insert_after": "batch_no",
			"read_only": 1,
			"no_copy": 1,
		}
	],
	"Batch": [
		{
			"fieldname": "work_order",
			"label": "Work Order",
			"fieldtype": "Link",
			"options": "Work Order",
			"insert_after": "reference_name",
			"read_only": 1,
			"search_index": 1,
		}
	],
}

# (doctype, fieldname, property, value, property_type)
PROPERTY_SETTERS = [
	("Delivery Note Item", "batch_no", "label", "Roll No", "Data"),
	("Delivery Note Item", "batch_no", "in_list_view", "1", "Check"),
	("Delivery Note Item", "batch_no", "columns", "2", "Int"),
	("Stock Entry Detail", "batch_no", "label", "Roll No", "Data"),
	("Batch", "batch_id", "label", "Roll No", "Data"),
	("Batch", "batch_qty", "label", "Roll Weight", "Data"),
]


def setup_customizations():
	"""Create every TTPL custom field and property setter."""
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)

	for doctype, fieldname, property_name, value, property_type in PROPERTY_SETTERS:
		make_property_setter(
			doctype,
			fieldname,
			property_name,
			value,
			property_type,
			validate_fields_for_doctype=False,
		)

	frappe.clear_cache()


def after_install():
	setup_customizations()


def after_migrate():
	setup_customizations()

"""Rolls produced by a work order, with what is still on hand.

Each roll is a Batch. Produced weight comes from the inward bundle entries of the
Manufacture Stock Entry; remaining weight is live batch stock, so a roll drops to
zero the moment it is delivered.
"""

import frappe
from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import get_auto_batch_nos
from frappe import _
from frappe.query_builder.functions import Max, Sum
from frappe.utils import cint, flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	rolls = get_rolls(filters)

	if not rolls:
		return get_columns(), []

	roll_names = [roll.name for roll in rolls]
	produced = get_produced_details(roll_names)
	remaining = get_remaining_qty(rolls, filters)

	data = []
	for roll in rolls:
		on_hand = remaining.get(roll.name, frappe._dict())
		if cint(filters.only_in_stock) and flt(on_hand.get("qty")) <= 0:
			continue

		details = produced.get(roll.name, frappe._dict())
		data.append(
			{
				"roll_no": roll.name,
				"item_code": roll.item,
				"work_order": roll.work_order,
				"stock_entry": details.get("voucher_no"),
				"produced_qty": flt(details.get("qty")),
				"remaining_qty": flt(on_hand.get("qty")),
				"warehouse": on_hand.get("warehouse"),
			}
		)

	return get_columns(), data


def get_columns():
	return [
		{
			"fieldname": "roll_no",
			"label": _("Roll No"),
			"fieldtype": "Link",
			"options": "Batch",
			"width": 180,
		},
		{
			"fieldname": "item_code",
			"label": _("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 180,
		},
		{
			"fieldname": "work_order",
			"label": _("Work Order"),
			"fieldtype": "Link",
			"options": "Work Order",
			"width": 150,
		},
		{
			"fieldname": "stock_entry",
			"label": _("Manufacture Entry"),
			"fieldtype": "Link",
			"options": "Stock Entry",
			"width": 150,
		},
		{
			"fieldname": "produced_qty",
			"label": _("Produced Weight"),
			"fieldtype": "Float",
			"precision": 3,
			"width": 140,
		},
		{
			"fieldname": "remaining_qty",
			"label": _("Remaining Weight"),
			"fieldtype": "Float",
			"precision": 3,
			"width": 140,
		},
		{
			"fieldname": "warehouse",
			"label": _("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 160,
		},
	]


def get_rolls(filters):
	"""Batches created by the TTPL roll flow, newest first."""
	conditions = {"work_order": ("is", "set")}

	if filters.work_order:
		conditions["work_order"] = filters.work_order
	if filters.item_code:
		conditions["item"] = filters.item_code

	return frappe.get_all(
		"Batch",
		filters=conditions,
		fields=["name", "item", "work_order"],
		order_by="creation desc",
	)


def get_produced_details(roll_names):
	"""Inward weight and the Manufacture Stock Entry that booked each roll."""
	entry = frappe.qb.DocType("Serial and Batch Entry")
	bundle = frappe.qb.DocType("Serial and Batch Bundle")

	rows = (
		frappe.qb.from_(entry)
		.inner_join(bundle)
		.on(entry.parent == bundle.name)
		.select(entry.batch_no, Sum(entry.qty).as_("qty"), Max(bundle.voucher_no).as_("voucher_no"))
		.where(entry.batch_no.isin(roll_names))
		.where(bundle.docstatus == 1)
		.where(bundle.is_cancelled == 0)
		.where(bundle.type_of_transaction == "Inward")
		.where(bundle.voucher_type == "Stock Entry")
		.groupby(entry.batch_no)
	).run(as_dict=True)

	return {row.batch_no: row for row in rows}


def get_remaining_qty(rolls, filters):
	"""Live stock per roll, one lookup per item."""
	by_item = frappe._dict()
	for roll in rolls:
		by_item.setdefault(roll.item, []).append(roll.name)

	remaining = frappe._dict()
	based_on = frappe.get_single_value("Stock Settings", "pick_serial_and_batch_based_on")

	for item_code, roll_names in by_item.items():
		batches = get_auto_batch_nos(
			frappe._dict(
				{
					"item_code": item_code,
					"batch_no": roll_names,
					"warehouse": filters.warehouse or None,
					"company": filters.company or None,
					"based_on": based_on,
				}
			)
		)

		for batch in batches:
			row = remaining.setdefault(batch.batch_no, frappe._dict({"qty": 0.0, "warehouse": None}))
			row.qty += flt(batch.qty)
			row.warehouse = batch.warehouse

	return remaining

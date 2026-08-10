"""
Pull the rolls a Work Order produced onto a Delivery Note.

Each roll is a Batch, so "still available" is simply the batch's live stock. That
means cancellations, sales returns and partially consumed rolls all resolve
themselves without a bespoke delivered/undelivered counter.
"""

import frappe
from erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle import get_auto_batch_nos
from erpnext.stock.get_item_details import get_item_details
from frappe import _
from frappe.utils import cint, flt


@frappe.whitelist()
def get_available_rolls(production_doctype, production_name, doc):
	"""Return the rolls of `production_name` that are still deliverable."""
	if isinstance(doc, str):
		doc = frappe.parse_json(doc)

	doc = frappe._dict(doc or {})
	work_order = resolve_work_order(production_doctype, production_name)

	roll_batches = frappe.get_all(
		"Batch",
		filters={"work_order": work_order, "disabled": 0},
		fields=["name", "item"],
	)
	if not roll_batches:
		return []

	items = {row.item for row in roll_batches}
	roll_names = [row.name for row in roll_batches]

	reserved = get_qty_on_draft_delivery_notes(roll_names, doc.get("name"))

	rolls = []
	for item_code in sorted(items):
		item_rolls = [row.name for row in roll_batches if row.item == item_code]
		details = get_delivery_item_details(doc, item_code)

		for batch in get_batch_stock(item_code, item_rolls, doc):
			qty = flt(batch.qty) - flt(reserved.get(batch.batch_no))
			if qty <= 0:
				continue

			rolls.append(
				{
					"roll_no": batch.batch_no,
					"item_code": item_code,
					"item_name": details.get("item_name"),
					"description": details.get("description"),
					"warehouse": batch.warehouse,
					"qty": qty,
					"uom": details.get("stock_uom"),
					"stock_uom": details.get("stock_uom"),
					"conversion_factor": 1,
					"price_list_rate": flt(details.get("price_list_rate")),
					"rate": flt(details.get("rate")),
					"work_order": work_order,
				}
			)

	return rolls


def resolve_work_order(production_doctype, production_name):
	"""A Job Card is accepted as a shortcut to the Work Order it belongs to."""
	if production_doctype not in ("Work Order", "Job Card"):
		frappe.throw(_("Rolls can only be fetched from a Work Order or a Job Card."))

	if production_doctype == "Job Card":
		work_order = frappe.db.get_value("Job Card", production_name, "work_order")
		if not work_order:
			frappe.throw(_("Job Card {0} is not linked to a Work Order.").format(production_name))
		return work_order

	return production_name


def get_batch_stock(item_code, roll_names, doc):
	"""Live stock per roll, honouring warehouse and existing stock reservations."""
	return get_auto_batch_nos(
		frappe._dict(
			{
				"item_code": item_code,
				"batch_no": roll_names,
				"warehouse": doc.get("set_warehouse") or None,
				"company": doc.get("company"),
				"based_on": frappe.get_single_value("Stock Settings", "pick_serial_and_batch_based_on"),
			}
		)
	)


def get_qty_on_draft_delivery_notes(roll_names, delivery_note=None):
	"""Rolls already claimed by other draft notes.

	Submitted notes need no subtraction, they are already out of the ledger.
	"""
	filters = {"batch_no": ("in", roll_names), "docstatus": 0}
	if delivery_note:
		filters["parent"] = ("!=", delivery_note)

	claimed = frappe._dict()
	for row in frappe.get_all("Delivery Note Item", filters=filters, fields=["batch_no", "stock_qty"]):
		claimed[row.batch_no] = flt(claimed.get(row.batch_no)) + flt(row.stock_qty)

	return claimed


def get_delivery_item_details(doc, item_code):
	"""Fetch item defaults and the customer's rate once per item."""
	ctx = frappe._dict(
		{
			"doctype": "Delivery Note",
			"name": doc.get("name"),
			"company": doc.get("company"),
			"item_code": item_code,
			"customer": doc.get("customer"),
			"currency": doc.get("currency"),
			"conversion_rate": flt(doc.get("conversion_rate")) or 1.0,
			"price_list": doc.get("selling_price_list"),
			"price_list_currency": doc.get("price_list_currency"),
			"plc_conversion_rate": flt(doc.get("plc_conversion_rate")) or 1.0,
			"set_warehouse": doc.get("set_warehouse"),
			"warehouse": doc.get("set_warehouse"),
			"transaction_date": doc.get("posting_date"),
			"posting_date": doc.get("posting_date"),
			"is_return": cint(doc.get("is_return")),
			"ignore_pricing_rule": cint(doc.get("ignore_pricing_rule")),
			"tax_category": doc.get("tax_category"),
			"project": doc.get("project"),
			"qty": 1,
		}
	)

	return get_item_details(ctx, doc=doc)

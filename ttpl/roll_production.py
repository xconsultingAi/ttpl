"""
Roll-wise production capture for TTPL work orders.

TTPL cuts a tissue mother roll into many smaller rolls. Every roll has its own
number and its own weight, and the stock UOM is Kg, so the produced quantity is
the sum of the individual roll weights rather than a figure the operator types.
"""

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from frappe import _
from frappe.utils import cint, flt, get_link_to_form, nowdate, nowtime


@frappe.whitelist()
def make_manufacture_entry_with_rolls(work_order, rolls, roll_no_base=None):
	"""Build a draft Manufacture Stock Entry that books one Batch per roll.

	Returns the unsaved Stock Entry as a dict so the client can sync and route to
	it, mirroring what `erpnext.work_order.make_se` does for the plain qty flow.
	"""
	work_order = frappe.get_doc("Work Order", work_order)
	work_order.check_permission("write")

	rolls = clean_rolls(rolls)
	validate_production_settings(work_order)
	total_weight = validate_rolls(work_order, rolls)

	stock_entry = frappe.get_doc(make_stock_entry(work_order.name, "Manufacture", qty=total_weight))
	if not stock_entry.posting_date:
		stock_entry.posting_date = nowdate()
	if not stock_entry.posting_time:
		stock_entry.posting_time = nowtime()

	finished_row = get_finished_good_row(stock_entry, work_order)
	drop_auto_bundle(finished_row)

	create_roll_batches(work_order, stock_entry, finished_row, rolls)

	bundle = build_roll_bundle(stock_entry, finished_row, rolls, total_weight)
	finished_row.serial_and_batch_bundle = bundle.name
	finished_row.use_serial_batch_fields = 0

	finished_row.qty = total_weight
	stock_entry.fg_completed_qty = total_weight

	if roll_no_base and roll_no_base != work_order.get("roll_no_base"):
		work_order.db_set("roll_no_base", roll_no_base, update_modified=False)

	return stock_entry.as_dict()


def clean_rolls(rolls):
	"""Normalise the client payload into `[{"roll_no": str, "weight": float}]`."""
	if isinstance(rolls, str):
		rolls = frappe.parse_json(rolls)

	if not rolls:
		frappe.throw(_("Enter at least one roll before finishing this Work Order."))

	cleaned = []
	for idx, row in enumerate(rolls, start=1):
		row = frappe._dict(row)
		roll_no = (row.roll_no or "").strip()
		if not roll_no:
			frappe.throw(_("Row #{0}: Roll No is required.").format(idx))

		weight = flt(row.weight)
		if weight <= 0:
			frappe.throw(_("Row #{0}: Roll {1} must have a weight greater than zero.").format(idx, roll_no))

		cleaned.append({"roll_no": roll_no, "weight": weight})

	return cleaned


def validate_production_settings(work_order):
	"""Refuse to run when the item or settings would produce wrong stock."""
	item = frappe.get_cached_value(
		"Item", work_order.production_item, ["has_batch_no", "has_serial_no"], as_dict=True
	)

	if not item.has_batch_no:
		frappe.throw(
			_("Item {0} must have {1} enabled to be produced as individually weighed rolls.").format(
				frappe.bold(work_order.production_item), frappe.bold(_("Has Batch No"))
			)
		)

	if item.has_serial_no:
		frappe.throw(
			_(
				"Item {0} has {1} enabled. A serial no always counts as one unit of the stock UOM, "
				"so it cannot carry a roll weight. Disable it and use rolls as batches instead."
			).format(frappe.bold(work_order.production_item), frappe.bold(_("Has Serial No")))
		)

	if cint(frappe.db.get_single_value("Manufacturing Settings", "make_serial_no_batch_from_work_order")):
		frappe.throw(
			_(
				"Disable {0} in {1}. It pre-creates equally sized batches and splits the finished good "
				"into several rows, which cannot represent rolls of differing weights."
			).format(
				frappe.bold(_("Make Serial No / Batch from Work Order")),
				get_link_to_form("Manufacturing Settings", "Manufacturing Settings"),
			)
		)


def validate_rolls(work_order, rolls):
	"""Check the roll numbers are free and the weights fit the Work Order."""
	roll_nos = [row["roll_no"] for row in rolls]

	duplicates = {roll_no for roll_no in roll_nos if roll_nos.count(roll_no) > 1}
	if duplicates:
		frappe.throw(
			_("Duplicate Roll No in this entry: {0}").format(frappe.bold(", ".join(sorted(duplicates))))
		)

	taken = frappe.get_all("Batch", filters={"name": ("in", roll_nos)}, pluck="name")
	if taken:
		frappe.throw(
			_("These Roll Nos already exist: {0}. Use a different Roll No Base.").format(
				frappe.bold(", ".join(sorted(taken)))
			)
		)

	precision = frappe.get_precision("Stock Entry Detail", "qty")
	total_weight = flt(sum(row["weight"] for row in rolls), precision)

	max_qty = flt(get_max_producible_qty(work_order), precision)
	if flt(total_weight, precision) > max_qty:
		frappe.throw(
			_("Total roll weight {0} exceeds the {1} still available to produce against {2}.").format(
				frappe.bold(total_weight), frappe.bold(max_qty), frappe.bold(work_order.name)
			)
		)

	return total_weight


def get_max_producible_qty(work_order):
	"""Mirror `erpnext.work_order.get_max_transferable_qty` plus the overproduction allowance."""
	if work_order.skip_transfer:
		max_qty = flt(work_order.qty) - flt(work_order.produced_qty)
	else:
		max_qty = flt(work_order.material_transferred_for_manufacturing) - flt(work_order.produced_qty)

	allowance = flt(
		frappe.db.get_single_value("Manufacturing Settings", "overproduction_percentage_for_work_order")
	)

	return max_qty + (flt(work_order.qty) * allowance / 100)


def get_finished_good_row(stock_entry, work_order):
	"""Return the single finished-good row the roll batches attach to."""
	rows = [
		row
		for row in stock_entry.items
		if row.is_finished_item and row.item_code == work_order.production_item
	]

	if len(rows) != 1:
		frappe.throw(
			_("Expected exactly one finished good row for {0} but found {1}.").format(
				frappe.bold(work_order.production_item), len(rows)
			)
		)

	return rows[0]


def drop_auto_bundle(finished_row):
	"""Discard any bundle ERPNext pre-attached, so the roll bundle is the only one."""
	bundle = finished_row.serial_and_batch_bundle
	finished_row.serial_and_batch_bundle = None

	if bundle and frappe.db.get_value("Serial and Batch Bundle", bundle, "docstatus") == 0:
		frappe.delete_doc("Serial and Batch Bundle", bundle, force=True, ignore_permissions=True)


def create_roll_batches(work_order, stock_entry, finished_row, rolls):
	"""Insert one Batch per roll, named after the roll and tagged to the Work Order.

	`Batch.autoname` uses an explicit `batch_id` verbatim, so the roll number the
	operator typed becomes the batch name.
	"""
	for row in rolls:
		frappe.get_doc(
			{
				"doctype": "Batch",
				"batch_id": row["roll_no"],
				"item": finished_row.item_code,
				"reference_doctype": "Work Order",
				"reference_name": work_order.name,
				"work_order": work_order.name,
				"manufacturing_date": stock_entry.posting_date,
			}
		).insert(ignore_permissions=True)


def build_roll_bundle(stock_entry, finished_row, rolls, total_weight):
	"""Create the draft inward bundle carrying one entry per roll.

	The bundle stays in draft with a blank voucher_no; `Stock Entry.on_update`
	backfills the voucher details and submit posts it. This is the same handoff
	ERPNext uses in `set_serial_no_batch_for_finished_good`.
	"""
	from erpnext.stock.serial_batch_bundle import SerialBatchCreation

	bundle = SerialBatchCreation(
		{
			"item_code": finished_row.item_code,
			"warehouse": finished_row.t_warehouse,
			"company": stock_entry.company,
			"voucher_type": "Stock Entry",
			"type_of_transaction": "Inward",
			"posting_date": stock_entry.posting_date,
			"posting_time": stock_entry.posting_time,
			"qty": total_weight,
			"batches": {row["roll_no"]: row["weight"] for row in rolls},
			"do_not_submit": True,
		}
	).make_serial_and_batch_bundle()

	if not bundle.get("name"):
		frappe.throw(_("Could not build the roll bundle for {0}.").format(finished_row.item_code))

	return bundle

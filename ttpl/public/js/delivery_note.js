// Pull the rolls a Work Order produced onto the Delivery Note.
//
// Each roll is a Batch, so "still available" is the batch's live stock. Deliver
// 8 of 10 rolls today and the same Work Order offers exactly the other 2 next
// time, with no delivered/undelivered counter to keep in step.

frappe.provide("ttpl.rolls");

frappe.ui.form.on("Delivery Note", {
	setup(frm) {
		frm.set_query("production_document", () => {
			return { filters: { docstatus: 1, company: frm.doc.company } };
		});
	},

	production_document_type(frm) {
		if (frm.doc.production_document) {
			frm.set_value("production_document", null);
		}
	},

	production_document(frm) {
		if (frm.doc.production_document) {
			ttpl.rolls.fetch_rolls(frm);
		}
	},

	get_rolls(frm) {
		ttpl.rolls.fetch_rolls(frm);
	},
});

ttpl.rolls.fetch_rolls = function (frm) {
	if (!frm.doc.production_document_type || !frm.doc.production_document) {
		frappe.throw(__("Select a Work Order or Job Card first."));
	}
	if (!frm.doc.customer) {
		frappe.throw(__("Select a Customer first."));
	}

	frappe.call({
		method: "ttpl.roll_delivery.get_available_rolls",
		args: {
			production_doctype: frm.doc.production_document_type,
			production_name: frm.doc.production_document,
			doc: frm.doc,
		},
		freeze: true,
		freeze_message: __("Fetching rolls..."),
		callback(r) {
			if (r.exc) {
				return;
			}

			// Rows already on this note may not be saved yet, so the server
			// cannot see them. Filter them out here.
			const already_added = new Set((frm.doc.items || []).map((row) => row.batch_no).filter(Boolean));
			const rolls = (r.message || []).filter((roll) => !already_added.has(roll.roll_no));

			if (!rolls.length) {
				frappe.msgprint({
					title: __("No Rolls Available"),
					indicator: "orange",
					message: __("No undelivered rolls are left against {0}.", [frm.doc.production_document]),
				});
				return;
			}

			ttpl.rolls.show_roll_picker(frm, rolls);
		},
	});
};

ttpl.rolls.show_roll_picker = function (frm, rolls) {
	const uom = rolls[0].stock_uom || "";

	const dialog = new frappe.ui.Dialog({
		title: __("Select Rolls to Deliver"),
		size: "large",
		fields: [
			{
				fieldname: "rolls",
				fieldtype: "Table",
				label: __("Available Rolls"),
				cannot_add_rows: true,
				cannot_delete_rows: true,
				in_place_edit: true,
				data: rolls.map((roll) => Object.assign({}, roll, { __checked: 1 })),
				fields: [
					{
						fieldname: "roll_no",
						fieldtype: "Data",
						label: __("Roll No"),
						in_list_view: 1,
						columns: 3,
						read_only: 1,
					},
					{
						fieldname: "item_code",
						fieldtype: "Link",
						options: "Item",
						label: __("Item"),
						in_list_view: 1,
						columns: 3,
						read_only: 1,
					},
					{
						fieldname: "warehouse",
						fieldtype: "Link",
						options: "Warehouse",
						label: __("Warehouse"),
						in_list_view: 1,
						columns: 2,
						read_only: 1,
					},
					{
						fieldname: "qty",
						fieldtype: "Float",
						label: __("Weight ({0})", [uom]),
						in_list_view: 1,
						columns: 2,
						read_only: 1,
					},
				],
			},
		],
		primary_action_label: __("Add to Delivery Note"),
		primary_action() {
			const selected = dialog.fields_dict.rolls.grid.get_selected_children();
			if (!selected.length) {
				frappe.throw(__("Select at least one roll."));
			}

			ttpl.rolls.add_rolls_to_items(frm, selected);
			dialog.hide();
		},
	});

	dialog.show();
};

ttpl.rolls.add_rolls_to_items = function (frm, rolls) {
	erpnext.utils.remove_empty_first_row(frm, "items");

	rolls.forEach((roll) => {
		const row = frappe.model.add_child(frm.doc, "Delivery Note Item", "items");

		// Fields are assigned straight from the server payload rather than
		// firing the item_code trigger, which would cost one round trip per
		// roll. Rates already came back priced for this customer.
		row.item_code = roll.item_code;
		row.item_name = roll.item_name;
		row.description = roll.description;
		row.uom = roll.uom;
		row.stock_uom = roll.stock_uom;
		row.conversion_factor = flt(roll.conversion_factor) || 1;
		row.warehouse = roll.warehouse;
		row.qty = flt(roll.qty);
		row.stock_qty = flt(roll.qty) * (flt(roll.conversion_factor) || 1);
		row.price_list_rate = flt(roll.price_list_rate);
		row.rate = flt(roll.rate);
		row.batch_no = roll.roll_no;
		row.use_serial_batch_fields = 1;
		row.work_order = roll.work_order;
	});

	frm.refresh_field("items");
	frm.cscript.calculate_taxes_and_totals();
};

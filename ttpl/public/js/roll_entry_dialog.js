// Roll entry grid used when finishing a TTPL work order.
//
// The operator types a base number and how many rolls came off the mother roll.
// One row is rendered per roll, pre-numbered <base>-1, <base>-2 and so on, and
// each row carries that roll's own weight. The produced quantity is the sum of
// those weights, never a figure typed by hand.

frappe.provide("ttpl.rolls");

ttpl.rolls.roll_no_for = function (base, index) {
	return base ? `${base}-${index}` : "";
};

ttpl.rolls.escape_regex = function (value) {
	return (value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
};

ttpl.rolls.show_roll_entry_dialog = function (opts) {
	const frm = opts.frm;
	const uom = opts.stock_uom || "";
	const max_qty = flt(opts.max_qty);
	let current_base = (opts.default_base || "").trim();

	const rows_of = () => dialog.fields_dict.rolls.df.data || [];

	const update_summary = () => {
		const rows = rows_of().filter((row) => row.roll_no || flt(row.weight));
		const total = rows.reduce((sum, row) => sum + flt(row.weight), 0);
		const over = total > max_qty;

		dialog.fields_dict.summary.$wrapper.html(`
			<div class="text-muted" style="margin-top: 5px;">
				<b>${rows.length}</b> ${__("rolls")} &middot;
				<b class="${over ? "text-danger" : ""}">${format_number(total, null, 3)} ${frappe.utils.escape_html(uom)}</b>
				${__("of max")} <b>${format_number(max_qty, null, 3)} ${frappe.utils.escape_html(uom)}</b>
			</div>
		`);
	};

	const floor3 = (value) => Math.floor(flt(value) * 1000) / 1000;

	let last_default = null;

	const apply_default_weight = () => {
		const weight = flt(dialog.get_value("default_weight"));

		if (last_default !== null && Math.abs(weight - last_default) < 1e-9) {
			return;
		}

		rows_of().forEach((row) => {
			const untouched = last_default !== null && Math.abs(flt(row.weight) - last_default) < 1e-9;
			if (!flt(row.weight) || untouched) {
				row.weight = weight;
			}
		});

		last_default = weight;
		dialog.fields_dict.rolls.grid.refresh();
		update_summary();
	};

	const sync_rows = () => {
		const count = cint(dialog.get_value("no_of_rolls"));
		const base = (dialog.get_value("roll_no_base") || "").trim();
		const data = rows_of();

		if (data.length === count) {
			return;
		}

		let weight = flt(dialog.get_value("default_weight"));
		if (count > 0 && !weight) {
			weight = floor3(max_qty / count);
			dialog.set_value("default_weight", weight);
		}

		while (data.length > count) {
			data.pop();
		}
		while (data.length < count) {
			data.push({
				roll_no: ttpl.rolls.roll_no_for(base, data.length + 1),
				weight: weight,
			});
		}

		last_default = weight;
		dialog.fields_dict.rolls.grid.refresh();
		update_summary();
	};

	const renumber_rows = () => {
		const base = (dialog.get_value("roll_no_base") || "").trim();

		if (base === current_base) {
			return;
		}

		const auto = current_base ? new RegExp(`^${ttpl.rolls.escape_regex(current_base)}-\\d+$`) : null;

		rows_of().forEach((row, index) => {
			if (!row.roll_no || (auto && auto.test(row.roll_no))) {
				row.roll_no = ttpl.rolls.roll_no_for(base, index + 1);
			}
		});

		current_base = base;
		dialog.fields_dict.rolls.grid.refresh();
		update_summary();
	};

	const collect_rolls = () => {
		const rows = rows_of().filter((row) => (row.roll_no || "").trim() || flt(row.weight));

		if (!rows.length) {
			frappe.throw(__("Enter at least one roll."));
		}

		const seen = new Set();
		const duplicates = new Set();

		rows.forEach((row, index) => {
			const roll_no = (row.roll_no || "").trim();
			if (!roll_no) {
				frappe.throw(__("Row #{0}: Roll No is required.", [index + 1]));
			}
			if (flt(row.weight) <= 0) {
				frappe.throw(
					__("Row #{0}: Roll {1} needs a weight greater than zero.", [index + 1, roll_no]),
				);
			}
			if (seen.has(roll_no)) {
				duplicates.add(roll_no);
			}
			seen.add(roll_no);
		});

		if (duplicates.size) {
			frappe.throw(__("Duplicate Roll No: {0}", [[...duplicates].join(", ")]));
		}

		const total = rows.reduce((sum, row) => sum + flt(row.weight), 0);
		if (total - max_qty > 0.001) {
			frappe.throw(
				__("Total roll weight {0} is more than the {1} still available to produce.", [
					format_number(total, null, 3),
					format_number(max_qty, null, 3),
				]),
			);
		}

		return rows.map((row) => ({
			roll_no: (row.roll_no || "").trim(),
			weight: flt(row.weight),
		}));
	};

	const dialog = new frappe.ui.Dialog({
		title: __("Enter Produced Rolls"),
		size: "large",
		fields: [
			{
				fieldname: "roll_no_base",
				fieldtype: "Data",
				label: __("Roll No Base"),
				reqd: 1,
				default: current_base,
				description: __("Rolls are numbered &lt;base&gt;-1, &lt;base&gt;-2 and so on."),
				onchange: renumber_rows,
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "no_of_rolls",
				fieldtype: "Int",
				label: __("No. of Rolls"),
				reqd: 1,
				description: __("One row is rendered per roll."),
				onchange: sync_rows,
			},
			{ fieldtype: "Column Break" },
			{
				fieldname: "default_weight",
				fieldtype: "Float",
				label: __("Default Weight per Roll ({0})", [uom]),
				precision: 3,
				description: __("Applied to every row you have not edited by hand."),
				onchange: apply_default_weight,
			},
			{ fieldtype: "Section Break" },
			{
				fieldname: "rolls",
				fieldtype: "Table",
				label: __("Rolls"),
				data: [],
				in_place_edit: true,
				cannot_delete_rows: false,
				fields: [
					{
						fieldname: "roll_no",
						fieldtype: "Data",
						label: __("Roll No"),
						in_list_view: 1,
						columns: 5,
						reqd: 1,
						onchange: update_summary,
					},
					{
						fieldname: "weight",
						fieldtype: "Float",
						label: __("Weight ({0})", [uom]),
						in_list_view: 1,
						columns: 4,
						reqd: 1,
						precision: 3,
						onchange: update_summary,
					},
				],
			},
			{ fieldname: "summary", fieldtype: "HTML" },
		],
		primary_action_label: __("Create Manufacture Entry"),
		primary_action() {
			const rolls = collect_rolls();

			frappe.call({
				method: "ttpl.roll_production.make_manufacture_entry_with_rolls",
				args: {
					work_order: frm.doc.name,
					rolls: rolls,
					roll_no_base: (dialog.get_value("roll_no_base") || "").trim(),
				},
				freeze: true,
				freeze_message: __("Creating Manufacture Entry..."),
				callback(r) {
					if (r.exc || !r.message) {
						return;
					}
					dialog.hide();
					frappe.model.sync(r.message);
					frappe.set_route("Form", r.message.doctype, r.message.name);
				},
			});
		},
	});

	dialog.show();
	update_summary();

	// Catch row deletions and any edit the per-field handlers miss.
	dialog.fields_dict.rolls.grid.wrapper.on("change click", () => {
		setTimeout(update_summary, 100);
	});

	return dialog;
};

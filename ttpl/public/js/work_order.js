// Replace the stock "Finish" prompt for batched items with the TTPL roll grid.
//
// ERPNext asks for a single produced quantity. TTPL cuts a mother roll into
// rolls of differing weights, so the quantity has to be built up from the
// individual rolls instead. Items that are not batched keep stock behaviour.

frappe.provide("ttpl.rolls");

frappe.ui.form.on("Work Order", {
	refresh(frm) {
		if (!frm.has_finish_btn || !frm.doc.has_batch_no || frm.doc.track_semi_finished_goods) {
			return;
		}

		frm.remove_custom_button(__("Finish"));

		const finish_btn = frm.add_custom_button(__("Finish"), () => {
			ttpl.rolls.show_roll_entry_dialog({
				frm: frm,
				item_code: frm.doc.production_item,
				stock_uom: frm.doc.stock_uom,
				max_qty: ttpl.rolls.max_producible_qty(frm),
				default_base: frm.doc.roll_no_base,
			});
		});

		if (flt(frm.doc.material_transferred_for_manufacturing) >= flt(frm.doc.qty)) {
			finish_btn.addClass("btn-primary");
		}

		frm.add_custom_button(
			__("Produced Rolls"),
			() => {
				frappe.set_route("query-report", "TTPL Produced Rolls", { work_order: frm.doc.name });
			},
			__("View"),
		);
	},
});

// Mirrors erpnext.work_order.get_max_transferable_qty plus the overproduction
// allowance that erpnext.work_order.show_prompt_for_qty_input adds on top.
ttpl.rolls.max_producible_qty = function (frm) {
	let max = frm.doc.skip_transfer
		? flt(frm.doc.qty) - flt(frm.doc.produced_qty)
		: flt(frm.doc.material_transferred_for_manufacturing) - flt(frm.doc.produced_qty);

	const allowance = (frm.doc.__onload && frm.doc.__onload.overproduction_percentage) || 0.0;
	max += (flt(frm.doc.qty) * flt(allowance)) / 100;

	return flt(max, precision("qty"));
};

from erpnext.accounts.doctype.payment_entry import payment_entry
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from erpnext.accounts.doctype.tax_withholding_entry.tax_withholding_entry import PaymentTaxWithholding
from frappe.utils import flt


class TTPLPaymentTaxWithholding(PaymentTaxWithholding):
	def _update_taxable_amounts(self):
		category = next(iter(self.category_details.values()))
		taxable_amount = flt(self.doc.total_allocated_amount) * self.get_conversion_rate()
		category["taxable_amount"] = flt(taxable_amount, self.precision)


payment_entry.PaymentTaxWithholding = TTPLPaymentTaxWithholding


class CustomPaymentEntry(PaymentEntry):
	pass

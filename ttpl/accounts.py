"""Shared account helpers for the TTPL number cards."""

import frappe
from erpnext.accounts.utils import get_account_balances

DEFAULT_COMPANY = "Tapal Tex Pvt. Ltd"


def get_balance_accounts(account_names, company):
	"""Load the named accounts in the shape `get_account_balances` expects.

	Accounts that do not exist for the company are skipped, so a chart of
	accounts that has been renamed does not break the card.
	"""
	return [
		{
			"value": account.name,
			"expandable": 0,
			"root_type": account.root_type,
			"account_currency": account.account_currency,
			"parent": account.parent_account,
		}
		for account in frappe.get_all(
			"Account",
			filters={"name": ["in", account_names], "company": company},
			fields=["name", "root_type", "account_currency", "parent_account"],
		)
	]


def get_total_balance(account_names, company=DEFAULT_COMPANY):
	"""Sum the current balance of the named accounts, as a number card value."""
	accounts = get_balance_accounts(account_names, company)
	data = get_account_balances(accounts=accounts, company=company)

	balance = sum(row.get("balance", 0.0) for row in data)
	return {"value": balance, "fieldtype": "Currency"}

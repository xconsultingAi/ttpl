<div align="center">

# TTPL

**Tapal Tex customizations for Frappe & ERPNext**

[![Frappe](https://img.shields.io/badge/Frappe-v16-blue)](https://github.com/frappe/frappe)
[![ERPNext](https://img.shields.io/badge/ERPNext-v16-blue)](https://github.com/frappe/erpnext)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## Overview

TTPL is a site-specific ERPNext customization app for Tapal Tex. It layers custom
fields, financial and stock reports, print formats, dashboards and a customized
`Payment Entry` controller on top of a standard ERPNext installation.

The app does not stand alone: **ERPNext is a required dependency.**

## Compatibility

| Branch       | Frappe | ERPNext | Status                |
| ------------ | ------ | ------- | --------------------- |
| `version-16` | v16    | v16     | Active development    |
| `develop`    | v15    | v15     | Legacy, reference only |

## What's Inside

### Reports

| Report                      | Type   | Purpose                                             |
| --------------------------- | ------ | --------------------------------------------------- |
| Banking Detail              | Script | Bank account movement detail                        |
| Contribution Margin Report  | Script | Item/order level contribution margin analysis       |
| Item Group Wise Stock Report| Script | Stock position rolled up by item group              |
| Tax Withholding Report      | Script | Withholding tax deducted per party and period       |

### Dashboards & Number Cards

- **Stock Dashboard** page with live stock and account balances
- Dashboard charts: *TTPL Account Balances*, *TTPL Stock Balances*
- Dashboards: *Accounts*, *Buying*, *TTPL Accounts*, *TTPL Stock Balances*
- 15 number cards covering cash and bank balances, trade debtors, creditors,
  accruals, long-term and running finance loans, raw material quantity/value,
  stores and spares quantity/value, and annual purchase/sales totals

### Print Formats

- Sales Invoice
- Sales Tax Invoice
- Sales Order
- Purchase Order (Vendor Copy)

### Customizations

Custom fields on Company, Item, Item Barcode, Packed Item, Sales Order (+ Item),
Sales Invoice (+ Item), Delivery Note (+ Item), Purchase Order (+ Item), and both
Sales and Purchase Taxes and Charges.

### Overrides

- `Payment Entry` &rarr; `ttpl.override.payment_entry.CustomPaymentEntry`

## Installation

```bash
cd $PATH_TO_YOUR_BENCH

# ERPNext is required
bench get-app erpnext --branch version-16

bench get-app https://github.com/xconsultingAi/ttpl --branch version-16
bench --site your-site.com install-app ttpl
```

## Development

```bash
cd apps/ttpl
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

Run the linters and tests:

```bash
ruff check ttpl/
pre-commit run --all-files
bench --site your-site.com run-tests --app ttpl
```

Rebuild the desk bundle after editing `ttpl/public/js/ttpl.bundle.js`:

```bash
bench build --app ttpl
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow, branch policy and
commit conventions.

## Releases

Releases are cut automatically from `version-16` by
[semantic-release](https://semantic-release.gitbook.io/) based on
[Conventional Commits](https://www.conventionalcommits.org/). The version in
`ttpl/__init__.py` is bumped by the release workflow.

## Security

Please report vulnerabilities privately. See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)

# Copyright (c) 2025, ashuar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = []

	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	conditions = ""
	if from_date:
		conditions += " AND posting_date >= %(from_date)s"
	if to_date:
		conditions += " AND posting_date <= %(to_date)s"
	# Total Finished Goods Qty
	total_qty = (
		frappe.db.sql(
			"""
        SELECT ABS(SUM(sle.actual_qty))
        FROM `tabStock Ledger Entry` sle
        JOIN `tabItem` item ON sle.item_code = item.name
        WHERE item.item_group = 'Finished Goods' AND sle.actual_qty > 0 AND sle.docstatus = 1 AND sle.is_cancelled = 0
          AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	if not total_qty:
		frappe.msgprint(_("No Finished Goods quantity found in the given date range."))
		return columns, []

	# RM Value (COGS + Stock Adjustment)
	trm_value = (
		frappe.db.sql(
			"""
        SELECT
            SUM(CASE WHEN account = '50101006 - COST OF GOOD SOLD - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50101019 - STOCK ADJUSTMENT - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	# RM Rate (calculated using actual finished goods qty)
	rm_rate = trm_value / total_qty
	# print("RM Rate:", rm_rate)

	# electricity_rate
	electricity_value = (
		frappe.db.sql(
			"""
        SELECT
            SUM(CASE WHEN account = '50115002 - ELECTRICITY BILL MILLS - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	electricity_rate = electricity_value / total_qty

	# Stores Warehouse Rate
	stores_value = (
		frappe.db.sql(
			"""
    SELECT
        SUM(CASE WHEN account = '50101007 - LPG Consumption - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)
	stores_rate = flt(stores_value / total_qty)

	# Waste Fuel
	lpg_value = (
		frappe.db.sql(
			"""
        SELECT
        SUM(CASE WHEN account = '50101008 - WASTE FUEL CONSUMPTION - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)
	lpg_rate = flt(lpg_value / total_qty)

	# Heater Fuel
	heater_value = (
		frappe.db.sql(
			"""
     SELECT
        SUM(CASE WHEN account = '50102003 - STORE CONSUMPTION - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)
	heater_rate = flt(heater_value / total_qty)

	# factory_salary
	factory_salary = (
		frappe.db.sql(
			"""
        SELECT
            SUM(CASE WHEN account = '50108005 - GENERAL OVERTIME MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50109001 - SALARY PRODUCTION - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	factory_salary = factory_salary / total_qty

	# factory_foh

	# factory_salary
	factory_foh = (
		frappe.db.sql(
			"""
        SELECT
            SUM(CASE WHEN account = '50101003 - FREIGHT ON RAW MATERIAL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '"account": "50101004 - Loading / Unloading Charges on RM - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50101008 - PACKING MATERIAL CONSUMPTION - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50101009 - Expenses Included In Valuation - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50104001 - STAFF PUNJAB ALLOWANCE MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50104010 - Salary Staff Mills - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50104007 - STAFF OVERTIME MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50104008 - STAFF FINAL SETTLEMENT MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50106001 - VEHICLE REPAIR & MAINTENANCE-SITE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50108006 - GENERAL FINALSATTLEMENT MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50113002 - ELECTRICITY BILL MILL (MAIN) - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50113010 - MOBILE EXPENSE MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50114002 - GRATUITY MILL EXPENSE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50119001 - FEE & SUBSCRIPTION MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50190013 - CULTIVATION EXPENSE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50190014 - FIEDMC MAINTENANCE CHARGES - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50101020 - FIBRE SORTING EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50101021 - CHEMICAL CONSUMPTION - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50101018 - Round Off - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50102001 - STORE DIRECT EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50103001 - INSURANCE EXPENSE FACTORY CGS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50107004 - REPAIR & MAINTENANCE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50108009 - DIESEL GENERATORMILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50108010 - REPAIRAND MAINTENANCE MILLS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50108011 - REPAIR& MAINTENANCE PLANT & MACHINERY - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50111010 - FREIGHT & CARTAGE (MILL) - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50112002 - MEDICAL EXPENSE MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50112003 - SOCIAL SECURITY MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50112005 - EMPLOYEES WELFARE (MILL) - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50113001 - MOBILE CARD ADMIN MANAGER - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50113005 - TELEPHONE #4500100 MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50113009 - INTERNET CHARGES (MILL) - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50113011 - MOBILE CARD MILL MANAGER - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50108009 - DIESEL FOR GENERATOR MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50124001 - FUEL & DIESEL LIFTER COS MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50116001 - PRINTINGS & STATIONERY MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50117001 - GUEST HOUSE EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50117002 - ENTERTAINMENT MILL GROCERY - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50117003 - ENTERTAINMENT MILL OTHERS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50118002 - LOADING UNLOADING OTHERS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50119002 - VEHICLE TOLL TAX - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50119003 - PROFESSIONAL TAX - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50120002 - TRAVELLING EXPENSES MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50121001 - POSTAGE & COURIER MILLS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50122003 - MISCELLANEOUS EXPENSES MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50190001 - REPAIR& MAINTENANCE MILLS BUILDING - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50190002 - PORT LINE SHIPPING & LOGISTIC - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50190010 - REPAIR& MAINTENANCE OFFICE EQUIPMENT - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50190012 - REPAIR& MAINTENANCE ELECTRICINSTALLATIONS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50123001 - FREIGHT ON MATERIAL USED IN PROCESSING - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50123003 - OTHER EXPENSE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50124001 - FUEL & DIESEL COS MILL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '60000001 - Freight Paid On Sale - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '50123002 - FREIGHT PAID ON SALE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '60101001 - CLEARING & FORWARDING CHARGES - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '60104002 - BANK CHARGES (INLAND LC) - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '60104006 - COMMISSION ON SALE - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '60104007 - PRICE DISCOUNT TO CUSTOMERS - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '60104004 - BANK COMMISSION(INLAND LC) - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '70101106 - NOC-FACTORY - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	factory_foh = factory_foh / total_qty
	# ho_foh
	ho_foh_value = (
		frappe.db.sql(
			"""
    SELECT
        SUM(CASE WHEN account = '70101003 - TELEPHONE BILLS HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101004 - Mobile Bills Head Office Employees - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101005 - MISC EXP HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101007 - CLOUD SERVER EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101101 - R&D EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101102 - NOC-HO - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101103 - Consultancy Charges - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101104 - Accomodation (Hotel Rent) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70116001 - REPAIR& MAINTENANCE GENERAL HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101107 - Business development Muree project - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70106008 - DOMAIN CHARGES E-MAIL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101105 - Travelling Expenses - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103001 - STAFF WELFARE MILLS - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103005 - STAFF WELFARE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103004 - EARNED LEAVES HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103006 - STAFF SALARIES HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70120001 - GRATUITY EXPENSE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103101 - S.W House Rent Rehman Villas 155 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103102 - S.W  Gas bill Rehman Villas 155 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103103 - S.W Electricity Bill Rehaman Villas 155 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103104 - S.W Water & Security Charges Rehman Villas 155 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70103105 - S.W Waste Busters Charges Rehaman Villas 155 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70104001 - ENTERTAINMENT HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70104002 - ENTERTAINMENT DIRECTORS - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70106003 - WATERBILL EXPENSE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70106004 - ELECTRICITY EXPENSE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70106005 - ELECTRICITY EXPENSES DIRECTOR RESIDENCE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70106007 - INTERNET CHARGES HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70106009 - PRINTING AND STATIONERY EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70107001 - PRINTING & STATIONERY HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70108001 - HEAD OFFICE RENT - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70108002 - Boiler Rent - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70109003 - INSURANCE EXPENSE VEHICELS HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70109005 - INSURANCE EXPENSES OTHERS - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70110001 - OFFICE SUPPLIES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70110002 - OTHER EXPENSES MILL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70112001 - LEGAL AND PROFESSIONAL EXPENSES HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70111001 - TRAVELLING EXPENSE DIRECTORS - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70111002 - TRAVELLING EXPENSES CHIEF EXECUTIVE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70111003 - TRAVELLING EXPENSE EMPLOYEE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70111005 - FREIGHT & CARTAGE HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70111006 - TRAVELLING AND CONVEYANCE EXPENSES (OTHERS) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113001 - VEHICLE RUNNING  HEAD OFFICE  KIA SPORTAGE AGT-813 (M. ZAHID HASSAN - MD) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113002 - VEHICLE RUNNING HEAD OFFICE CHANGAN ALSVIN AND-902  (ZUHAIB TUFAIL - NSM) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113003 - VEHICLE RUNNING HEAD OFFICE CHANGAN ALSVIN AND-967 (SARWAR BHATTI - PurM) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113004 - VEHICLE RUNNING HEAD OFFICE SUZUKI CULTUS ANJ-442 (USMAN ZAIGHAM - ProjM) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113005 - VEHICLE RUNNING HEAD OFFICE (Sunny Office Boy) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113006 - VEHICLE RUNNING HEAD OFFICE Hamza Iqbal (DM Accounts) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113007 - VEHICLE RUNNING HEAD OFFICE Muhammad Bilal Khalid (Accountant) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113009 - VEHICLE RUNNING HEAD OFFICE ALSVIN AND-902 (ZOHAIB TUFAIL - NSM) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113010 - VEHICLE RUNNING HEAD OFFICE TOYOTA COROLA AEU-101 (M. SAJID HASSAN ) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113011 - VEHICLE RUNNING HEAD OFFICE Tapal tex pvt ltd AQJ 4156 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113012 - VEHICLE RUNNING HEAD OFFICE M.SAUD ALI (OFICE BOY) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113013 - VEHICLE RUNNING HEAD OFFICE FAISAL MANSOOR - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113014 - VEHICLE RUNNING HEAD OFFICE Yasir Arif (Sweeper) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113015 - VEHICLE RUNNING HEAD OFFICE AXZ-256 Miss Shazia hussain - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113016 - VEHICLE RUNNING SITE, CAN-1061 MAZDA TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113017 - VEHICLE RUNNING SITE, LE-3284 WEGONR TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113018 - VEHICLE RUNNING SITE, AMY 4533 BIKE, TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113019 - VEHICLE RUNNING HEAD OFFICE Honda City LEF 1805 (Waqas Azeem) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113020 - VEHICLE RUNNING FACTORY Shafat Haidery sb (Technical Manager)V#AUB-502 WEGNOR - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70113021 - VEHICLE RUNNING SITE ADMIN MANAGER, V#AUC-880 WEGNOR - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114001 - Vehicle Repair & Maintance (M.Zahid Hassan) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114002 - Vehicle Repair & Maintance(M.Usman Zaigham) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114003 - Vehicle Repair & Maintance (Zohaib Tufail) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114004 - Vehicle Repair & Maintance (Ghulam Sarwar Bhatti) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114005 - Vehicle Repair & Maintance (M.Sajid Hassan) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114006 - Vehicle Repair & Maintance BIKE AQJ 4156 - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114007 - Vehicle Repair & Maintance (M.Sadiq Tapal) - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114008 - Vehicle Repair & Maintance CAN-1061 MAZDA (SITE) - TTPL - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114009 - Vehicle Repair & Maintance LE-3284 Wegon R(SITE)  - TTPL - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114010 - Vehicle Repair & Maintance AMY 4533 Bike(site) - TTPL - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114011 - Vehicle Repair & Maintenace ( Miss Shazia) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114013 - Vehicle Repair & Maintenance ,Shafat Haidery sb (Technical Manager). V#AUB-502 Wegnor - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114014 - Vehicle Repair & Maintenance, Admin Manager V#AUC 880, WEGNOR - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114015 - Vehicle Repair & Maintance LEF-1805 (Waqas Azeem) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70101006 - VEHICLE REGISTRATION CHARGES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70114012 - Vehicle Repair & Maintance LEM-588 (Yasir) - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70115001 - DONATION HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70117001 - AUDIT FEE EXPENSE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70118003 - LEASE RENTAL EXPENSES (AGT-813) - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70118005 - LEASE RENTAL EXPENSE AVS - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70120003 - POSTAGE & COURIER EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70120004 - VEHICLE TOKENS - TTPLL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70120007 - Marketing Expense - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70120008 - PURE CARE EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70120009 - PAK WIPE EXPENSES - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70122001 - FEES & SUBSCRIPTION HEAD OFFICE - TTPL' THEN debit - credit ELSE 0 END) +
        SUM(CASE WHEN account = '70118004 - MEDICAL EXPENSE DIRECTOR - TTPL' THEN debit - credit ELSE 0 END)

        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)
	ho_foh = flt(ho_foh_value / total_qty)
	# fc
	fc = (
		frappe.db.sql(
			"""
        SELECT
            SUM(CASE WHEN account = '80000001 - MARK UP ON LONG TERM LOAN BAFL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '80000003 - MARK UP ON SHORT TERM LOAN PCICL - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '80000002 - MARK UP ON SHORT TERM LOAN BAFL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '80000004 - MARK UP ON LONG TERM LOAN PCICL - TTPL - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '80110002 - OTHER CHARGES - TTPL' THEN debit - credit ELSE 0 END) +
            SUM(CASE WHEN account = '80110008 - BANK CHARGE - TTPL' THEN debit - credit ELSE 0 END)
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	fc = fc / total_qty

	# Total Finished Goods Qty
	total_actual_qty = (
		frappe.db.sql(
			"""
        SELECT ABS(SUM(sle.actual_qty) )
         FROM `tabStock Ledger Entry` sle
         JOIN `tabItem` item ON sle.item_code = item.name
         WHERE item.item_group = 'Finished Goods' AND sle.actual_qty < 0 AND sle.docstatus = 1 AND sle.is_cancelled = 0
          AND sle.posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	if not total_actual_qty:
		frappe.msgprint(_("No Finished Goods quantity found in the given date range."))
		return columns, []
	# sale_price
	toatal_sale_price = (
		frappe.db.sql(
			"""
        SELECT
            ABS(SUM(CASE WHEN account = '40100001 - Sales - TTPL' THEN debit - credit ELSE 0 END))
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %(from_date)s AND %(to_date)s
    """,
			filters,
			as_list=True,
		)[0][0]
		or 0
	)

	sale_price = toatal_sale_price / total_actual_qty
	# variable_cost
	variable_cost = (
		rm_rate + electricity_rate + stores_rate + lpg_rate + heater_rate + factory_salary + factory_foh
	)
	# contribution_margin
	contribution_margin = sale_price - variable_cost
	contribution_ratio = (contribution_margin / sale_price) * 100

	total_fixed_cost = ho_foh + fc
	total_cost = variable_cost + total_fixed_cost
	net_profit = sale_price - total_cost

	data.append(
		[
			"Kg",  # UOM fixed
			rm_rate,
			electricity_rate,
			stores_rate,
			lpg_rate,
			heater_rate,
			factory_salary,
			factory_foh,
			variable_cost,
			total_actual_qty,
			sale_price,
			total_qty,
			contribution_margin,
			contribution_ratio,
			ho_foh,
			fc,
			total_fixed_cost,
			total_cost,
			net_profit,
		]
	)

	return columns, data


def get_columns():
	return [
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 120},
		{"label": _("RM Rate"), "fieldname": "trm_value", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Electricity Rate"),
			"fieldname": "electricity_rate",
			"fieldtype": "Currency",
			"width": 120,
		},
		{"label": _("Stores Warehouse Rate"), "fieldname": "stores_rate", "fieldtype": "Float", "width": 120},
		{"label": _("LPG Rate"), "fieldname": "lpg_rate", "fieldtype": "Currency", "width": 120},
		{"label": _("Heater Fuel"), "fieldname": "heater_rate", "fieldtype": "Currency", "width": 120},
		{"label": _("Factory Salary"), "fieldname": "factory_salary", "fieldtype": "Currency", "width": 120},
		{"label": _("Factory FOH"), "fieldname": "factory_foh", "fieldtype": "Currency", "width": 120},
		{"label": _("Variable Cost"), "fieldname": "variable_cost", "fieldtype": "Currency", "width": 120},
		{"label": _("Sold Qty"), "fieldname": "sold_qty", "fieldtype": "Float", "width": 120},
		{"label": _("Sale Price"), "fieldname": "sale_price", "fieldtype": "Currency", "width": 120},
		{"label": _("Net Production"), "fieldname": "net_production", "fieldtype": "Float", "width": 120},
		{
			"label": _("Contribution Margin"),
			"fieldname": "contribution_margin",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": _("Contribution Ratio (%)"),
			"fieldname": "contribution_ratio",
			"fieldtype": "Percent",
			"width": 120,
		},
		{"label": _("HO FOH"), "fieldname": "HO_FOH", "fieldtype": "Currency", "width": 120},
		{"label": _("FC"), "fieldname": "FC", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Total Fixed Cost"),
			"fieldname": "total_fixed_cost",
			"fieldtype": "Currency",
			"width": 120,
		},
		{"label": _("Total Cost (VC+FC)"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 120},
		{
			"label": _("Net Profit/(Loss) per Unit"),
			"fieldname": "net_profit",
			"fieldtype": "Currency",
			"width": 120,
		},
	]

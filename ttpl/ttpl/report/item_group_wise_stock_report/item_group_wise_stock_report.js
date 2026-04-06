frappe.query_reports["Item Group Wise Stock Report"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_start()
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.month_end()
        },
        {
            fieldname: "item_group",
            label: __("Item Group"),
            fieldtype: "Link",
            options: "Item Group"
        }
    ],

    formatter: function(value, row, column, data, default_formatter) {
        if (!data) return value;

        value = default_formatter(value, row, column, data);

        if (data.is_group) {
            if (column.fieldname === "item_code") {
                return `<b style="font-size:14px;">${data.item_code}</b>`;
            } else {
                return "";
            }
        }

        return value;
    }
};
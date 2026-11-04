console.log("🔥 CVS Coil Summary Report 🔥 1 ");

frappe.query_reports["CVS Coil Summary Report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
			get_data: function(txt) {
				return frappe.db.get_link_options("Warehouse", txt, {
					company: frappe.query_report.get_filter_value("company")
				});
			}
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group"
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		}
	],

	get_datatable_options: function(options) {
		return Object.assign(options, {
			showTotalRow: false,
			clusterize: false
		});
	},

	after_datatable_render: function(datatable) {
		var raw = frappe.query_report && frappe.query_report.raw_data;
		if (!raw || !raw.result || !raw.result.length) return;

		var html = raw.result[0] && raw.result[0].report_html;
		if (!html) return;

		datatable.wrapper.innerHTML =
			'<div style="width:100%;padding:4px 0;">' +
			html +
			'</div>';
	}
};
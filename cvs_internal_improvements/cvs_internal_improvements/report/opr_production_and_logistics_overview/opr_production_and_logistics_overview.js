// Column order must match get_columns() in opr_production_and_logistics_overview.py
// Customer and Project are always the first two columns, in that fixed order,
// regardless of the "Group By" filter (which only controls subtotal grouping).
const OPR_FROZEN_FIELDS = ["customer_name", "project", "region", "opr_name", "product_type"];

// Merged header definitions, one set per "View Mode". Row 1 = broad section
// headers, Row 2 = SQM/Nos pair headers. Field lists must match get_columns()
// for that view exactly (same fields, same order).
const OPR_IDENTITY_FIELDS = ["customer_name", "project", "region", "opr_name"];

const OPR_HEADER_GROUPS = {
	Logistics: {
		top: [
			{ label: "", fields: [...OPR_IDENTITY_FIELDS, "product_type"] },
			{ label: "OPR Info", fields: ["total_sqm", "total_no"] },
			{
				label: "Logistics Info",
				fields: [
					"total_sqm_delivered",
					"total_nos_delivered",
					"remaining_sqm_delivery",
					"remaining_nos_delivery",
					"remaining_produced_sqm_to_delivered",
					"remaining_produced_no_to_delivered",
				],
			},
			{ label: "", fields: ["workflow_state"] },
		],
		sub: [
			{ label: "", fields: [...OPR_IDENTITY_FIELDS, "product_type"] },
			{ label: "Total OPR Qty", fields: ["total_sqm", "total_no"] },
			{ label: "Delivered Qty", fields: ["total_sqm_delivered", "total_nos_delivered"] },
			{ label: "Balance Delivery Qty", fields: ["remaining_sqm_delivery", "remaining_nos_delivery"] },
			{
				label: "Ready for Dispatch",
				fields: ["remaining_produced_sqm_to_delivered", "remaining_produced_no_to_delivered"],
			},
			{ label: "", fields: ["workflow_state"] },
		],
	},

	Production: {
		top: [
			{ label: "", fields: [...OPR_IDENTITY_FIELDS, "product_type", "committed_end_date"] },
			{
				label: "OPR Info",
				fields: [
					"total_sqm",
					"total_no",
					"total_straight_sqm",
					"total_straight_nos",
					"total_fittings_sqm",
					"total_fittings_nos",
				],
			},
			{
				label: "Manufacturing Info",
				fields: [
					"total_sqm_produced",
					"total_nos_produced",
					"remaining_sqm_production",
					"remaining_nos_production",
				],
			},
			{ label: "", fields: ["workflow_state"] },
		],
		sub: [
			{
				label: "",
				fields: [...OPR_IDENTITY_FIELDS, "product_type", "committed_end_date"],
			},
			{ label: "Total OPR Qty", fields: ["total_sqm", "total_no"] },
			{ label: "Total STS", fields: ["total_straight_sqm", "total_straight_nos"] },
			{ label: "Total FTS", fields: ["total_fittings_sqm", "total_fittings_nos"] },
			{ label: "Produced Qty", fields: ["total_sqm_produced", "total_nos_produced"] },
			{
				label: "Balance Production Qty",
				fields: ["remaining_sqm_production", "remaining_nos_production"],
			},
			{ label: "", fields: ["workflow_state"] },
		],
	},

	Operations: {
		top: [
			{ label: "", fields: [...OPR_IDENTITY_FIELDS, "product_type"] },
			{
				label: "OPR Info",
				fields: [
					"total_sqm",
					"total_no",
					"total_straight_sqm",
					"total_straight_nos",
					"total_fittings_sqm",
					"total_fittings_nos",
				],
			},
			{
				label: "Manufacturing Info",
				fields: [
					"total_sqm_produced",
					"total_nos_produced",
					"remaining_sqm_production",
					"remaining_nos_production",
				],
			},
			{
				label: "Logistics Info",
				fields: [
					"total_sqm_delivered",
					"total_nos_delivered",
					"remaining_sqm_delivery",
					"remaining_nos_delivery",
					"remaining_produced_sqm_to_delivered",
					"remaining_produced_no_to_delivered",
				],
			},
			{ label: "", fields: ["workflow_state"] },
		],
		sub: [
			{ label: "", fields: [...OPR_IDENTITY_FIELDS, "product_type"] },
			{ label: "Total OPR Qty", fields: ["total_sqm", "total_no"] },
			{ label: "Total STS", fields: ["total_straight_sqm", "total_straight_nos"] },
			{ label: "Total FTS", fields: ["total_fittings_sqm", "total_fittings_nos"] },
			{ label: "Produced Qty", fields: ["total_sqm_produced", "total_nos_produced"] },
			{
				label: "Balance Production Qty",
				fields: ["remaining_sqm_production", "remaining_nos_production"],
			},
			{ label: "Delivered Qty", fields: ["total_sqm_delivered", "total_nos_delivered"] },
			{
				label: "Balance Delivery Qty",
				fields: ["remaining_sqm_delivery", "remaining_nos_delivery"],
			},
			{
				label: "Ready for Dispatch",
				fields: ["remaining_produced_sqm_to_delivered", "remaining_produced_no_to_delivered"],
			},
			{ label: "", fields: ["workflow_state"] },
		],
	},
};

frappe.query_reports["OPR Production and Logistics Overview"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Data",
		},
		{
			fieldname: "customer_name",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "sales_order",
			label: __("Sales Order"),
			fieldtype: "Link",
			options: "Sales Order",
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
		},
		{
			fieldname: "product_type",
			label: __("Product Type"),
			fieldtype: "Link",
			options: "Product Type",
		},
		{
			fieldname: "region",
			label: __("Region"),
			fieldtype: "Link",
			options: "Territory",
		},
		{
			fieldname: "workflow_state",
			label: __("Workflow State"),
			fieldtype: "Link",
			options: "Workflow State",
		},
		{
			fieldname: "active_only",
			label: __("Active Only"),
			fieldtype: "Check",
			default: 1,
		},
		{
			fieldname: "pending_only",
			label: __("Pending Only"),
			fieldtype: "Check",
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["Project", "Customer"],
			default: "Project",
		},
		{
			fieldname: "view_mode",
			label: __("View Mode"),
			fieldtype: "Select",
			options: ["Logistics", "Production", "Operations"],
			default: "Logistics",
		},
	],

	get_datatable_options(options) {
		// Predictable column indices (Customer = 0, Project = 1, ...) for freezing.
		options.serialNoColumn = false;
		return options;
	},

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && (data.row_type === "group_total" || data.row_type === "grand_total")) {
			value = `<b>${value}</b>`;
		}
		return value;
	},

	after_datatable_render(datatable) {
		const view_mode = frappe.query_report.get_filter_value("view_mode") || "Logistics";
		datatable._opr_view_mode = view_mode;
		setup_header_wrap();
		setup_total_row_style(datatable);
		setup_group_headers(datatable, view_mode);
		setup_freeze_toggle(datatable);
		bind_resize_handler(datatable);
	},

	onload(report) {
		report.page.add_inner_button(__("Toggle Freeze Columns"), () => {
			const datatable = report.datatable;
			if (!datatable) return;
			if (datatable._opr_freeze_on) {
				remove_freeze(datatable);
			} else {
				apply_freeze(datatable);
			}
		});
	},
};

function setup_header_wrap() {
	const styleId = "opr-overview-header-wrap-style";
	if (document.getElementById(styleId)) return;

	const style = document.createElement("style");
	style.id = styleId;
	style.textContent = `
		.dt-header .dt-cell {
			height: auto !important;
			overflow: visible !important;
		}
		.dt-header .dt-cell__content {
			white-space: normal !important;
			word-break: break-word !important;
			line-height: 1.35 !important;
			height: auto !important;
			overflow: visible !important;
			padding-top: 8px !important;
			padding-bottom: 8px !important;
			text-align: center !important;
			justify-content: center !important;
		}
		.dt-header .dt-row {
			height: auto !important;
			min-height: 40px;
		}
		.opr-group-header-row {
			border-bottom: 1px solid var(--dt-border-color);
			font-weight: bold;
		}
		.opr-group-header__content {
			display: flex !important;
			align-items: center;
			justify-content: center;
			text-align: center;
			font-weight: bold;
		}
	`;
	document.head.appendChild(style);
}

function setup_total_row_style(datatable) {
	const rows = datatable.datamanager && datatable.datamanager.data;
	if (!rows) return;

	const group_total_rows = [];
	const grand_total_rows = [];

	rows.forEach((row, i) => {
		if (row.row_type === "group_total") group_total_rows.push(i);
		if (row.row_type === "grand_total") grand_total_rows.push(i);
	});

	// No fill colour - bold text (via the formatter) plus a plain border
	// is enough to mark totals without a highlight.
	if (group_total_rows.length) {
		datatable.style.setStyle(
			group_total_rows.map((i) => `.dt-row-${i}`).join(","),
			{ "border-top": "1px solid var(--dt-border-color)" }
		);
	}

	if (grand_total_rows.length) {
		datatable.style.setStyle(
			grand_total_rows.map((i) => `.dt-row-${i}`).join(","),
			{ "border-top": "2px solid var(--dt-border-color)" }
		);
	}
}

function get_field_to_col_index(datatable) {
	const map = {};
	datatable.datamanager.getColumns().forEach((col) => {
		map[col.id] = col.colIndex;
	});
	return map;
}

function get_column_widths(datatable) {
	const widths = [];
	datatable.datamanager.getColumns().forEach((col) => {
		const cell = datatable.header.querySelector(`.dt-cell--header-${col.colIndex}`);
		widths[col.colIndex] = cell ? cell.offsetWidth : col.width || 100;
	});
	return widths;
}

function build_group_row_html(groups, fieldToCol, colWidths, rowClass) {
	const cells = groups.map((group, idx) => {
		const width = group.fields.reduce((sum, fieldname) => {
			const colIndex = fieldToCol[fieldname];
			return sum + (colWidths[colIndex] || 0);
		}, 0);

		const is_frozen_cell = idx === 0;
		const is_labeled = !!(group.label && group.label.trim());

		return `
			<div class="dt-cell dt-cell--header ${is_frozen_cell ? "opr-group-freeze-cell" : ""} ${
			is_labeled ? "opr-group-header-cell--labeled" : ""
		}"
				style="width:${width}px;min-width:${width}px;max-width:${width}px;">
				<div class="dt-cell__content opr-group-header__content">${frappe.utils.escape_html(group.label)}</div>
			</div>
		`;
	});

	return `<div class="dt-row ${rowClass}">${cells.join("")}</div>`;
}

function setup_group_headers(datatable, view_mode) {
	// remove any group header rows from a previous render
	datatable.header.querySelectorAll(".opr-group-header-row").forEach((el) => el.remove());

	const groups = OPR_HEADER_GROUPS[view_mode] || OPR_HEADER_GROUPS.Logistics;

	const headerInner = datatable.header.querySelector(":scope > div") || datatable.header;
	const headerRow = headerInner.querySelector(".dt-row-header");
	if (!headerRow) return;

	const fieldToCol = get_field_to_col_index(datatable);
	const colWidths = get_column_widths(datatable);

	const topRowHtml = build_group_row_html(
		groups.top,
		fieldToCol,
		colWidths,
		"opr-group-header-row opr-group-header-row--top"
	);
	const subRowHtml = build_group_row_html(
		groups.sub,
		fieldToCol,
		colWidths,
		"opr-group-header-row opr-group-header-row--sub"
	);

	headerRow.insertAdjacentHTML("beforebegin", topRowHtml + subRowHtml);
}

function apply_freeze(datatable) {
	if (datatable._opr_freeze_on) return;
	datatable._opr_freeze_on = true;

	const fieldToCol = get_field_to_col_index(datatable);
	const frozenIndices = OPR_FROZEN_FIELDS.map((f) => fieldToCol[f]);

	const bodyScrollable = datatable.bodyScrollable;
	const header = datatable.header;
	if (!bodyScrollable || !header) return;

	// Pin the body cells for the frozen columns using sticky positioning
	// (bodyScrollable has real horizontal overflow, so sticky works there).
	const offsets = {};
	let cumLeft = 0;
	frozenIndices.forEach((i) => {
		offsets[i] = cumLeft;
		const cell = header.querySelector(`.dt-cell--header-${i}`);
		cumLeft += cell ? cell.offsetWidth : 0;
	});
	const frozenWidth = cumLeft;

	const styleId = "opr-overview-freeze-style";
	let style = document.getElementById(styleId);
	if (!style) {
		style = document.createElement("style");
		style.id = styleId;
		document.head.appendChild(style);
	}
	style.textContent = frozenIndices
		.map(
			(i) =>
				`.dt-cell--col-${i} { position: sticky !important; left: ${offsets[i]}px !important; z-index: 2 !important; background: var(--dt-cell-bg) !important; }`
		)
		.join("\n");

	// The header (and our injected group-header rows) scroll via a JS-driven
	// translateX on the whole .dt-header, so sticky won't engage there.
	// Counter-translate the frozen header/group cells to keep them visually pinned.
	const onScroll = function () {
		const scrollLeft = this.scrollLeft;

		frozenIndices.forEach((i) => {
			header.querySelectorAll(`.dt-cell--header-${i}`).forEach((cell) => {
				cell.style.transform = `translateX(${scrollLeft}px)`;
				cell.style.position = "relative";
				cell.style.zIndex = "3";
				cell.style.background = "var(--dt-header-cell-bg)";
			});
		});

		header.querySelectorAll(".opr-group-freeze-cell").forEach((cell) => {
			cell.style.transform = `translateX(${scrollLeft}px)`;
			cell.style.position = "relative";
			cell.style.zIndex = "3";
			cell.style.width = `${frozenWidth}px`;
		});
	};

	datatable._opr_freeze_scroll_handler = onScroll;
	bodyScrollable.addEventListener("scroll", onScroll);
	onScroll.call(bodyScrollable);
}

function remove_freeze(datatable) {
	if (!datatable._opr_freeze_on) return;
	datatable._opr_freeze_on = false;

	const style = document.getElementById("opr-overview-freeze-style");
	if (style) style.remove();

	const header = datatable.header;
	if (datatable._opr_freeze_scroll_handler && datatable.bodyScrollable) {
		datatable.bodyScrollable.removeEventListener("scroll", datatable._opr_freeze_scroll_handler);
	}

	header.querySelectorAll('[class*="dt-cell--header-"], .opr-group-freeze-cell').forEach((cell) => {
		cell.style.transform = "";
		cell.style.position = "";
		cell.style.zIndex = "";
	});
}

function bind_resize_handler(datatable) {
	if (datatable._opr_resize_bound) return;
	datatable._opr_resize_bound = true;

	window.addEventListener(
		"resize",
		frappe.utils.debounce(() => {
			// Read the view mode fresh each time (set on every
			// after_datatable_render) instead of closing over the value
			// from whichever render first bound this listener - the
			// datatable instance is reused across "View Mode" filter
			// changes, so a stale closure would rebuild the merged
			// header for the wrong view.
			setup_group_headers(datatable, datatable._opr_view_mode || "Logistics");
			if (datatable._opr_freeze_on) {
				remove_freeze(datatable);
				apply_freeze(datatable);
			}
		}, 300)
	);
}

function setup_freeze_toggle(datatable) {
	// Freeze the first 2 columns (Customer, Project) by default; user can
	// toggle it off/on via the "Toggle Freeze Columns" button. Re-applied
	// (not just left as-is) on every render since column widths can change.
	const was_on = datatable._opr_freeze_on !== false;
	if (datatable._opr_freeze_on) remove_freeze(datatable);
	if (was_on) apply_freeze(datatable);
}

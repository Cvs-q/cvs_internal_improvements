import frappe


def execute(filters=None):
	filters = filters or {}

	group_by = filters.get("group_by") or "Project"
	if group_by not in ("Project", "Customer"):
		group_by = "Project"

	view_mode = filters.get("view_mode") or "Logistics"
	if view_mode not in ("Logistics", "Production", "Operations"):
		view_mode = "Logistics"

	columns = get_columns(view_mode)
	data = get_data(filters, group_by)

	return columns, data


def get_data(filters, group_by):

	# =========================================================
	# FILTER VALUES
	# =========================================================

	values = {
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),

		"project": filters.get("project") or "",
		"project_like": "%" + (filters.get("project") or "") + "%",

		"customer_name": filters.get("customer_name") or "",
		"sales_order": filters.get("sales_order") or "",
		"sales_person": filters.get("sales_person") or "",
		"product_type": filters.get("product_type") or "",
		"region": filters.get("region") or "",
		"workflow_state": filters.get("workflow_state") or "",

		"active_only": 1 if filters.get("active_only") else 0,
		"pending_only": 1 if filters.get("pending_only") else 0,

		"excluded_customer": "Central Ventilation Systems Co. LLC",
	}

	# Sort order follows whichever grouping is selected.
	group_sort_column = "opr.customer_name" if group_by == "Customer" else "opr.project"

	# =========================================================
	# DATABASE QUERY
	#
	# NOTE: "Order Processing Request" has no region column of its
	# own. Region is looked up from the linked Project (matched on
	# opr.project = tabProject.name) since that is the only place
	# a "Region" field exists today.
	# =========================================================

	opr_rows = frappe.db.sql(
		f"""
		SELECT
			opr.name AS opr_name,

			COALESCE(
				NULLIF(TRIM(opr.project), ''),
				'Project Not Specified'
			) AS project,

			COALESCE(
				NULLIF(TRIM(opr.customer_name), ''),
				'Customer Not Specified'
			) AS customer_name,

			COALESCE(
				NULLIF(TRIM(proj.region), ''),
				'Not Specified'
			) AS region,

			COALESCE(
				NULLIF(TRIM(opr.workflow_state), ''),
				'Not Specified'
			) AS workflow_state,

			COALESCE(
				NULLIF(TRIM(opr.product_type1), ''),
				'Not Specified'
			) AS product_type,

			opr.committed_end_date AS committed_end_date,

			COALESCE(opr.total_sqm, 0)
				AS total_sqm,

			COALESCE(opr.total_no, 0)
				AS total_no,

			COALESCE(opr.total_straight_sqm, 0)
				AS total_straight_sqm,

			COALESCE(opr.total_straight_nos, 0)
				AS total_straight_nos,

			COALESCE(opr.total_fittings_sqm, 0)
				AS total_fittings_sqm,

			COALESCE(opr.total_fittings_nos, 0)
				AS total_fittings_nos,

			COALESCE(opr.total_sqm_produced, 0)
				AS total_sqm_produced,

			COALESCE(opr.total_nos_produced, 0)
				AS total_nos_produced,

			COALESCE(opr.remaining_sqm_production, 0)
				AS remaining_sqm_production,

			COALESCE(opr.remaining_nos_production, 0)
				AS remaining_nos_production,

			COALESCE(opr.total_sqm_delivered, 0)
				AS total_sqm_delivered,

			COALESCE(opr.total_nos_delivered, 0)
				AS total_nos_delivered,

			COALESCE(opr.remaining_sqm_delivery, 0)
				AS remaining_sqm_delivery,

			COALESCE(opr.remaining_nos_delivery, 0)
				AS remaining_nos_delivery,

			COALESCE(
				opr.remaining_produced_sqm_to_delivered,
				0
			) AS remaining_produced_sqm_to_delivered,

			COALESCE(
				opr.remaining_produced_no_to_delivered,
				0
			) AS remaining_produced_no_to_delivered

		FROM `tabOrder Processing Request` opr

		LEFT JOIN `tabProject` proj
			ON proj.name = opr.project

		WHERE opr.docstatus < 2

			/* Permanently exclude internal customer */
			AND COALESCE(opr.customer_name, '') <>
				%(excluded_customer)s

			AND (
				%(from_date)s IS NULL
				OR opr.date >= %(from_date)s
			)

			AND (
				%(to_date)s IS NULL
				OR opr.date <= %(to_date)s
			)

			AND (
				%(project)s = ''
				OR COALESCE(opr.project, '') LIKE %(project_like)s
			)

			AND (
				%(customer_name)s = ''
				OR opr.customer_name = %(customer_name)s
			)

			AND (
				%(sales_order)s = ''
				OR opr.sales_order = %(sales_order)s
			)

			AND (
				%(sales_person)s = ''
				OR opr.sales_person = %(sales_person)s
			)

			AND (
				%(product_type)s = ''
				OR opr.product_type1 = %(product_type)s
			)

			AND (
				%(region)s = ''
				OR COALESCE(proj.region, '') = %(region)s
			)

			AND (
				%(workflow_state)s = ''
				OR COALESCE(opr.workflow_state, '') = %(workflow_state)s
			)

			AND (
				%(active_only)s = 0
				OR COALESCE(opr.workflow_state, '') NOT IN (
					'Completed',
					'Canceled',
					'Cancelled',
					'Draft',
					'Submitted for Approval',
					'Approved by General Manager',
					'On Hold',
					'Delivery Completed',
					'PO Verified'
				)
			)

			/*
			 * Pending filter:
			 * - SQM fields intentionally excluded
			 * - Checks remaining Nos and Remaining Value
			 */
			AND (
				%(pending_only)s = 0
				OR (
					COALESCE(
						opr.remaining_nos_production,
						0
					) <> 0

					OR COALESCE(
						opr.remaining_nos_delivery,
						0
					) <> 0

					OR COALESCE(
						opr.remaining_produced_no_to_delivered,
						0
					) <> 0
				)
			)

		ORDER BY
			COALESCE(NULLIF(TRIM({group_sort_column}), ''), 'Not Specified') ASC,
			opr.name ASC
		""",
		values,
		as_dict=True,
	)

	# =========================================================
	# FIELDS TO TOTAL
	# =========================================================

	numeric_fields = [
		"total_sqm",
		"total_no",
		"total_straight_sqm",
		"total_straight_nos",
		"total_fittings_sqm",
		"total_fittings_nos",
		"total_sqm_produced",
		"total_nos_produced",
		"remaining_sqm_production",
		"remaining_nos_production",
		"total_sqm_delivered",
		"total_nos_delivered",
		"remaining_sqm_delivery",
		"remaining_nos_delivery",
		"remaining_produced_sqm_to_delivered",
		"remaining_produced_no_to_delivered",
	]

	# =========================================================
	# GROUP RECORDS (by Project or Customer, per group_by)
	# =========================================================

	grouped_rows = {}
	group_order = []

	for opr in opr_rows:

		if group_by == "Customer":
			group_name = opr.get("customer_name") or "Customer Not Specified"
		else:
			group_name = opr.get("project") or "Project Not Specified"

		if group_name not in grouped_rows:
			grouped_rows[group_name] = []
			group_order.append(group_name)

		grouped_rows[group_name].append(opr)

	# =========================================================
	# INITIALISE TOTALS
	# =========================================================

	grand_total = {fieldname: 0.0 for fieldname in numeric_fields}

	rows = []

	# =========================================================
	# BUILD GROUP SUMMARY ROW + OPR DETAIL ROWS
	# =========================================================

	for group_name in group_order:

		group_total = {fieldname: 0.0 for fieldname in numeric_fields}

		group_oprs = grouped_rows.get(group_name) or []

		group_regions = []
		group_workflow_states = []

		# -----------------------------------------------------
		# CALCULATE GROUP TOTALS
		# -----------------------------------------------------

		for opr in group_oprs:

			region_name = opr.get("region") or "Not Specified"
			workflow_name = opr.get("workflow_state") or "Not Specified"

			if region_name not in group_regions:
				group_regions.append(region_name)

			if workflow_name not in group_workflow_states:
				group_workflow_states.append(workflow_name)

			for fieldname in numeric_fields:

				value = opr.get(fieldname) or 0.0

				group_total[fieldname] = group_total.get(fieldname, 0.0) + value
				grand_total[fieldname] = grand_total.get(fieldname, 0.0) + value

		# -----------------------------------------------------
		# DETERMINE GROUP SUMMARY DISPLAY VALUES
		# -----------------------------------------------------

		group_region = ""
		if len(group_regions) == 1:
			group_region = group_regions[0]
		if len(group_regions) > 1:
			group_region = "Multiple"

		group_workflow_state = ""
		if len(group_workflow_states) == 1:
			group_workflow_state = group_workflow_states[0]
		if len(group_workflow_states) > 1:
			group_workflow_state = "Multiple"

		# -----------------------------------------------------
		# GROUP SUMMARY ROW
		# Customer and Project are always separate columns now;
		# only the field matching the active "Group By" carries
		# the group name, the other stays blank on this row.
		# -----------------------------------------------------

		group_row = {
			"customer_name": group_name if group_by == "Customer" else "",
			"project": group_name if group_by == "Project" else "",
			"region": group_region,
			"workflow_state": group_workflow_state,
			"opr_name": "",
			"committed_end_date": None,
			"product_type": "",
			"indent": 0,
			"row_type": "group_total",
		}

		for fieldname in numeric_fields:
			group_row[fieldname] = group_total.get(fieldname, 0.0)

		rows.append(group_row)

		# -----------------------------------------------------
		# OPR DETAIL ROWS
		# -----------------------------------------------------

		for opr in group_oprs:

			detail_row = {
				"customer_name": opr.get("customer_name"),
				"project": opr.get("project"),
				"region": opr.get("region"),
				"workflow_state": opr.get("workflow_state"),
				"opr_name": opr.get("opr_name"),
				"committed_end_date": opr.get("committed_end_date"),
				"product_type": opr.get("product_type"),
				"indent": 1,
				"row_type": "opr",
			}

			for fieldname in numeric_fields:
				detail_row[fieldname] = opr.get(fieldname) or 0.0

			rows.append(detail_row)

	# =========================================================
	# GRAND TOTAL
	# =========================================================

	grand_total_row = {
		"customer_name": "Grand Total",
		"project": "",
		"region": "",
		"workflow_state": "",
		"opr_name": "",
		"committed_end_date": None,
		"product_type": "",
		"indent": 0,
		"row_type": "grand_total",
	}

	for fieldname in numeric_fields:
		grand_total_row[fieldname] = grand_total.get(fieldname, 0.0)

	rows.append(grand_total_row)

	return rows


def get_columns(view_mode):

	customer_column = {"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 200}
	project_column = {"label": "Project", "fieldname": "project", "fieldtype": "Data", "width": 200}
	region_column = {"label": "Region", "fieldname": "region", "fieldtype": "Data", "width": 120}
	opr_no_column = {
		"label": "OPR No",
		"fieldname": "opr_name",
		"fieldtype": "Link",
		"options": "Order Processing Request",
		"width": 135,
	}
	product_type_column = {"label": "Product Type", "fieldname": "product_type", "fieldtype": "Data", "width": 200}
	expected_completion_column = {
		"label": "Exp. Completion Date",
		"fieldname": "committed_end_date",
		"fieldtype": "Date",
		"width": 130,
	}
	workflow_state_column = {"label": "Workflow State", "fieldname": "workflow_state", "fieldtype": "Data", "width": 145}

	opr_qty_columns = [
		{"label": "Total OPR SQM", "fieldname": "total_sqm", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": "Total OPR Nos", "fieldname": "total_no", "fieldtype": "Float", "precision": 2, "width": 110},
	]
	std_columns = [
		{"label": "Total Std SQM", "fieldname": "total_straight_sqm", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": "Total Std Nos", "fieldname": "total_straight_nos", "fieldtype": "Float", "precision": 2, "width": 110},
	]
	fitt_columns = [
		{"label": "Total Fitt SQM", "fieldname": "total_fittings_sqm", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": "Total Fitt Nos", "fieldname": "total_fittings_nos", "fieldtype": "Float", "precision": 2, "width": 110},
	]
	produced_columns = [
		{"label": "Produced SQM", "fieldname": "total_sqm_produced", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": "Produced Nos", "fieldname": "total_nos_produced", "fieldtype": "Float", "precision": 2, "width": 110},
	]
	rem_production_columns = [
		{
			"label": "Rem. Production SQM",
			"fieldname": "remaining_sqm_production",
			"fieldtype": "Float",
			"precision": 2,
			"width": 135,
		},
		{
			"label": "Rem. Production Nos",
			"fieldname": "remaining_nos_production",
			"fieldtype": "Float",
			"precision": 2,
			"width": 135,
		},
	]
	delivered_columns = [
		{"label": "Delivered SQM", "fieldname": "total_sqm_delivered", "fieldtype": "Float", "precision": 2, "width": 110},
		{"label": "Delivered Nos", "fieldname": "total_nos_delivered", "fieldtype": "Float", "precision": 2, "width": 110},
	]
	rem_delivery_columns = [
		{
			"label": "Rem. Delivery SQM",
			"fieldname": "remaining_sqm_delivery",
			"fieldtype": "Float",
			"precision": 2,
			"width": 125,
		},
		{
			"label": "Rem. Delivery Nos",
			"fieldname": "remaining_nos_delivery",
			"fieldtype": "Float",
			"precision": 2,
			"width": 125,
		},
	]
	ready_dispatch_columns = [
		{
			"label": "Ready Dispatch SQM",
			"fieldname": "remaining_produced_sqm_to_delivered",
			"fieldtype": "Float",
			"precision": 2,
			"width": 140,
		},
		{
			"label": "Ready Dispatch Nos",
			"fieldname": "remaining_produced_no_to_delivered",
			"fieldtype": "Float",
			"precision": 2,
			"width": 140,
		},
	]

	if view_mode == "Production":
		return (
			[customer_column, project_column, region_column, opr_no_column, product_type_column, expected_completion_column]
			+ opr_qty_columns
			+ std_columns
			+ fitt_columns
			+ produced_columns
			+ rem_production_columns
			+ [workflow_state_column]
		)

	if view_mode == "Logistics":
		return (
			[customer_column, project_column, region_column, opr_no_column, product_type_column]
			+ opr_qty_columns
			+ delivered_columns
			+ rem_delivery_columns
			+ ready_dispatch_columns
			+ [workflow_state_column]
		)

	# Operations: the full, combined column set.
	return (
		[customer_column, project_column, region_column, opr_no_column, product_type_column]
		+ opr_qty_columns
		+ std_columns
		+ fitt_columns
		+ produced_columns
		+ rem_production_columns
		+ delivered_columns
		+ rem_delivery_columns
		+ ready_dispatch_columns
		+ [workflow_state_column]
	)

# CVS Coil Summary Report — Script Report (ERPNext v15 / Frappe v15)
#
# Classification rules:
#   Grade = "GI G90"      → GI Coils table,   column = Brand  (blank Brand  → "Others")
#   Grade = anything else → Other Coils table, column = Grade  (blank Grade  → "Others")
#
# Brand and Grade columns are discovered dynamically from actual stock data.
# No hard-coded grade mapping from item_group names.
#
# Group Type (Coil / Slitted) is read from the item's group_type field if it
# exists on the doctype; otherwise inferred from the item_group name.



import re

import frappe
from frappe.utils import flt


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════


def execute(filters=None):
    filters = frappe._dict(filters or {})
    stock_rows = _get_stock_data(filters)
    classified = _classify_rows(stock_rows)
    cfg = _build_config_from_data(classified)
    pivot = _build_pivot(classified, cfg)
    html = _render_html(pivot, len(stock_rows), cfg)
    columns = [
        {
            "fieldname": "report_html",
            "label": "CVS Coil Summary",
            "fieldtype": "HTML",
            "width": 9999,
        }
    ]
    return columns, [{"report_html": html}]


# ═════════════════════════════════════════════════════════════════════════════
# Data fetching
# ═════════════════════════════════════════════════════════════════════════════


def _get_warehouse_list(warehouse, company):
    try:
        lft, rgt = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"])
        if not lft:
            return [warehouse]
    except Exception:
        return [warehouse]
    return (
        frappe.db.sql_list(
            """SELECT name FROM `tabWarehouse`
               WHERE lft >= %s AND rgt <= %s
                 AND company = %s AND disabled = 0""",
            (lft, rgt, company),
        )
        or [warehouse]
    )


def _get_item_group_list(item_group):
    try:
        lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])
        if not lft:
            return [item_group]
    except Exception:
        return [item_group]
    return frappe.db.sql_list(
        "SELECT name FROM `tabItem Group` WHERE lft >= %s AND rgt <= %s",
        (lft, rgt),
    ) or [item_group]


COIL_PARENT_GROUP = "Coils (ton)"


def _resolve_fieldname(doctype, candidates):
    """Return the first fieldname from `candidates` that actually exists as a
    column on `doctype`, or None if none of them do. Lets the report work on
    sites where a field was added under a different name (e.g. a custom
    field prefixed "custom_" instead of the plain fieldname)."""
    for fieldname in candidates:
        if frappe.db.has_column(doctype, fieldname):
            return fieldname
    return None


def _get_stock_data(filters):
    # Include group_type only when the column actually exists on tabItem
    has_group_type = frappe.db.has_column("Item", "group_type")
    gt_select = "i.group_type," if has_group_type else ""
    gt_group  = "i.group_type," if has_group_type else ""

    # Grade / Guage may exist as plain fields or as "custom_" prefixed
    # custom fields depending on the site — use whichever is present.
    grade_field = _resolve_fieldname("Item", ["grade", "custom_grade"])
    guage_field = _resolve_fieldname("Item", ["guage", "custom_guage"])

    grade_select = f"i.{grade_field} AS grade," if grade_field else "NULL AS grade,"
    guage_select = f"i.{guage_field} AS guage," if guage_field else "NULL AS guage,"
    grade_group  = f"i.{grade_field}," if grade_field else ""
    guage_group  = f"i.{guage_field}," if guage_field else ""

    # Dynamically expand all child item groups under "Coils (ton)"
    coil_groups = _get_item_group_list(COIL_PARENT_GROUP)
    coil_groups_tuple = tuple(coil_groups) if coil_groups else ("__none__",)

    conditions = [
        "COALESCE(sle.is_cancelled, 0) != 1",
        "i.stock_uom IN %(ton_uoms)s",
        "i.item_group IN %(coil_groups)s",
    ]
    params = {
        "ton_uoms":    ("MT", "Ton", "Metric Ton", "MTS", "Tonnes"),
        "coil_groups": coil_groups_tuple,
    }

    if filters.get("company"):
        conditions.append("sle.company = %(company)s")
        params["company"] = filters.company

    if filters.get("to_date"):
        conditions.append("sle.posting_date <= %(to_date)s")
        params["to_date"] = filters.to_date

    if filters.get("warehouse") and filters.get("company"):
        selected_warehouses = filters.get("warehouse")
        if isinstance(selected_warehouses, str):
            selected_warehouses = [w.strip() for w in selected_warehouses.split(",") if w.strip()]
        if not isinstance(selected_warehouses, list):
            selected_warehouses = [selected_warehouses]
        wh_list = []
        for wh in selected_warehouses:
            wh_list.extend(_get_warehouse_list(wh, filters.company))
        if wh_list:
            conditions.append("sle.warehouse IN %(warehouses)s")
            params["warehouses"] = tuple(set(wh_list))

    if filters.get("item_group"):
        ig_list = _get_item_group_list(filters.item_group)
        if ig_list:
            conditions.append("i.item_group IN %(item_groups)s")
            params["item_groups"] = tuple(ig_list)

    where = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            sle.item_code,
            i.item_name,
            i.item_group,
            {gt_select}
            i.brand,
            {grade_select}
            {guage_select}
            i.stock_uom,
            SUM(sle.actual_qty) AS qty
        FROM `tabStock Ledger Entry` sle
        INNER JOIN `tabItem` i ON i.name = sle.item_code
        WHERE {where}
        GROUP BY
            sle.item_code, i.item_name, i.item_group,
            {gt_group}
            i.brand, {grade_group} {guage_group} i.stock_uom
        HAVING SUM(sle.actual_qty) > 0
        """,
        params,
        as_dict=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Classification
# ═════════════════════════════════════════════════════════════════════════════


def _parse_thickness(item_name):
    """Extract the gauge/thickness number from an item name string."""
    if not item_name:
        return None
    s = str(item_name)
    m = re.search(r"(\d+\.?\d*)\s*[Xx]\s*\d", s)
    if m:
        return m.group(1)
    m = re.search(r"(\d+\.?\d*)\s*mm", s, re.IGNORECASE)
    if m:
        try:
            v = float(m.group(1))
            if 0.1 <= v <= 10.0:
                return m.group(1)
        except ValueError:
            pass
    m = re.search(r"\b(\d+\.\d{1,3})\b", s)
    if m:
        v = float(m.group(1))
        if 0.1 <= v <= 10.0:
            return m.group(1)
    return None


def _classify_rows(stock_rows):
    """
    Classify each stock row using grade and brand fields only.

    Section:
      grade == "GI G90"  →  GI Coils,    column = brand (blank → "Others")
      anything else      →  Other Coils,  column = grade (blank → "Others")

    Group Type (row grouping within each section):
      Uses the group_type field when present; otherwise infers from item_group name.
    """
    result = []
    for row in stock_rows:
        grade = (row.get("grade") or "").strip()
        brand = (row.get("brand") or "").strip()
        guage = row.get("guage")
        iname = row.item_name or ""

        # Determine Coil vs Slitted
        gt_val = (row.get("group_type") or "").strip().lower()
        if gt_val:
            coil_type = "Slitted Coil" if "slitted" in gt_val else "Coils"
        else:
            coil_type = "Slitted Coil" if "slitted" in (row.item_group or "").lower() else "Coils"

        # Section and column — purely from grade field
        if grade == "GI G90":
            section = "GI Coils"
            col     = brand if brand else "Others"
        else:
            section = "Other Coils"
            col     = grade if grade else "Others"

        # Normalise thickness to a consistent float string
        thickness_raw = guage or _parse_thickness(iname)
        thickness = str(flt(thickness_raw, 2)) if thickness_raw else "N/A"

        result.append({
            "coil_section": section,
            "coil_type":    coil_type,
            "col_key":      col,
            "thickness":    thickness,
            "qty":          flt(row.qty, 2),
        })
    return result


def _build_config_from_data(classified):
    """
    Build dynamic column lists from the classified rows.

    GI Coils columns  = distinct brand values found in GI G90 stock, sorted A→Z, "Others" last.
    Other Coils cols  = distinct grade values found in non-GI stock,  sorted A→Z, "Others" last.
    Summary cols      = "GI G90" + Other Coils grade cols + "Others".

    "Others" is included only when at least one row maps to it (blank/null
    Brand or Grade), or when no named columns exist at all.
    """
    gi_brands        = []
    gi_has_others    = False
    other_grades     = []
    other_has_others = False

    for r in classified:
        col = r["col_key"]
        if r["coil_section"] == "GI Coils":
            if col == "Others":
                gi_has_others = True
            elif col not in gi_brands:
                gi_brands.append(col)
        else:
            if col == "Others":
                other_has_others = True
            elif col not in other_grades:
                other_grades.append(col)

    gi_cols = sorted(gi_brands)
    if gi_has_others or not gi_cols:
        gi_cols.append("Others")

    other_cols = sorted(other_grades)
    if other_has_others or not other_cols:
        other_cols.append("Others")

    # Summary aggregates all GI Coils into "GI G90"; Other Coils keep their grade
    summary_cols = ["GI G90"] + sorted(other_grades)
    if other_has_others or not other_grades:
        summary_cols.append("Others")

    return {
        "gi_cols":      gi_cols,
        "other_cols":   other_cols,
        "summary_cols": summary_cols,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Pivot builder
# ═════════════════════════════════════════════════════════════════════════════


def _build_pivot(classified, cfg):
    pivot = {
        "GI Coils":    {"Coils": {}, "Slitted Coil": {}},
        "Other Coils": {"Coils": {}, "Slitted Coil": {}},
    }
    for r in classified:
        t_dict = pivot[r["coil_section"]][r["coil_type"]]
        thk = r["thickness"]
        t_dict.setdefault(thk, {})
        t_dict[thk][r["col_key"]] = flt(
            t_dict[thk].get(r["col_key"], 0) + r["qty"], 2
        )
    return pivot


# ═════════════════════════════════════════════════════════════════════════════
# HTML rendering
# ═════════════════════════════════════════════════════════════════════════════


def _fmt(val):
    v = flt(val, 2)
    return f"{v:.2f}" if v else ""


def _safe_f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 9999.0


def _fmt_thickness(t):
    if not t or t == "N/A":
        return "N/A"
    try:
        clean = str(t).lower().replace("mm", "").strip()
        v = float(clean)
        return f"{v:.2f} mm"
    except (TypeError, ValueError):
        return str(t)


_CT_DISPLAY = {
    "Coils":        ("Coil",    "Coil Total"),
    "Slitted Coil": ("Slitted", "Slitted Total"),
}


def _section_rows(section_data, cols, grand_label):
    rows = []
    grand_col = {c: 0.0 for c in cols}
    has_any = False

    for ct in ["Coils", "Slitted Coil"]:
        td = section_data.get(ct, {})
        thicknesses = sorted(td.keys(), key=_safe_f)

        ct_has_data = any(
            any(flt(td[t].get(c, 0), 2) for c in cols) for t in thicknesses
        )
        if not ct_has_data:
            continue

        has_any = True
        hdr_label, sub_label = _CT_DISPLAY.get(ct, (ct, f"{ct} Total"))
        rows.append(
            f'<tr class="csr-type-hdr">'
            f'<td colspan="{len(cols) + 2}">□ {hdr_label}</td>'
            f"</tr>"
        )

        ct_col = {c: 0.0 for c in cols}
        for t in thicknesses:
            row_d = td[t]
            row_total = 0.0
            cells = ""
            for c in cols:
                v = flt(row_d.get(c, 0), 2)
                ct_col[c] = flt(ct_col[c] + v, 2)
                row_total = flt(row_total + v, 2)
                cells += f'<td class="csr-num">{_fmt(v)}</td>'
            if not row_total:
                continue
            rows.append(
                f"<tr>"
                f'<td class="csr-indent">{_fmt_thickness(t)}</td>'
                f"{cells}"
                f'<td class="csr-num csr-bold">{_fmt(row_total)}</td>'
                f"</tr>"
            )

        sub_total = 0.0
        sub_cells = ""
        for c in cols:
            sub_cells += f'<td class="csr-num csr-bold">{_fmt(ct_col[c])}</td>'
            grand_col[c] = flt(grand_col[c] + ct_col[c], 2)
            sub_total = flt(sub_total + ct_col[c], 2)
        rows.append(
            f'<tr class="csr-sub">'
            f'<td class="csr-bold">{sub_label}</td>'
            f"{sub_cells}"
            f'<td class="csr-num csr-bold">{_fmt(sub_total)}</td>'
            f"</tr>"
        )

    gt_total = flt(sum(grand_col.values()), 2)
    gt_cells = "".join(
        f'<td class="csr-num csr-bold">{_fmt(grand_col[c])}</td>' for c in cols
    )

    if has_any:
        rows.append(
            f'<tr class="csr-grand">'
            f'<td class="csr-bold">{grand_label}</td>'
            f"{gt_cells}"
            f'<td class="csr-num csr-bold">{_fmt(gt_total)}</td>'
            f"</tr>"
        )
    else:
        rows.append(
            f'<tr class="csr-nodata">'
            f'<td colspan="{len(cols) + 2}" style="text-align:center;'
            f'color:var(--text-muted,#8d99a6);font-style:italic;">No stock data</td>'
            f"</tr>"
        )

    return rows, grand_col, gt_total


def _build_table(title, cols, section_data, grand_label="Grand Total"):
    hdr = "".join(f"<th>{c}</th>" for c in cols)
    body_rows, _, _ = _section_rows(section_data, cols, grand_label)
    tbody = "\n".join(body_rows)
    span = len(cols) + 2
    return (
        f'<table class="csr-table">'
        f"<thead>"
        f'<tr class="csr-title"><th colspan="{span}">{title}</th></tr>'
        f'<tr class="csr-col-hdr"><th>Type</th>{hdr}<th>Total</th></tr>'
        f"</thead>"
        f"<tbody>{tbody}</tbody>"
        f"</table>"
    )


def _render_summary_table(pivot, cfg):
    gi    = pivot["GI Coils"]
    other = pivot["Other Coils"]
    cols  = cfg["summary_cols"]
    rows_html  = []
    col_totals = {c: 0.0 for c in cols}

    for ct in ["Coils", "Slitted Coil"]:
        row_vals = {c: 0.0 for c in cols}

        # All GI Coils quantities collapse into the "GI G90" summary column
        for t_data in gi.get(ct, {}).values():
            row_vals["GI G90"] = flt(
                row_vals["GI G90"] + sum(flt(v, 2) for v in t_data.values()), 2
            )

        # Other Coils quantities map to their grade column directly
        for t_data in other.get(ct, {}).values():
            for g, v in t_data.items():
                if g in row_vals:
                    row_vals[g] = flt(row_vals[g] + flt(v, 2), 2)

        cells     = "".join(f'<td class="csr-num">{_fmt(row_vals[c])}</td>' for c in cols)
        row_total = sum(row_vals[c] for c in cols)
        for c in cols:
            col_totals[c] = flt(col_totals[c] + row_vals[c], 2)

        ct_display = "Coil" if ct == "Coils" else "Slitted"
        rows_html.append(
            f"<tr><td>{ct_display}</td>{cells}"
            f'<td class="csr-num csr-bold">{_fmt(row_total)}</td></tr>'
        )

    gt_cells = "".join(
        f'<td class="csr-num csr-bold">{_fmt(col_totals[c])}</td>' for c in cols
    )
    gt_total = sum(col_totals.values())
    rows_html.append(
        f'<tr class="csr-grand">'
        f'<td class="csr-bold">Grand Total</td>{gt_cells}'
        f'<td class="csr-num csr-bold">{_fmt(gt_total)}</td>'
        f"</tr>"
    )

    hdr  = "".join(f"<th>{c}</th>" for c in cols)
    span = len(cols) + 2
    return (
        f'<table class="csr-table">'
        f"<thead>"
        f'<tr class="csr-title"><th colspan="{span}">Coil Summary (MT)</th></tr>'
        f'<tr class="csr-col-hdr"><th>Type</th>{hdr}<th>Total</th></tr>'
        f"</thead>"
        f'<tbody>{"".join(rows_html)}</tbody>'
        f"</table>"
    )


def _render_html(pivot, row_count, cfg):
    gi_table      = _build_table("GI Coils (MT)",    cfg["gi_cols"],    pivot["GI Coils"])
    other_table   = _build_table("Other Coils (MT)", cfg["other_cols"], pivot["Other Coils"])
    summary_table = _render_summary_table(pivot, cfg)

    no_data_warn = ""
    if row_count == 0:
        no_data_warn = (
            '<div class="csr-msg-muted">'
            "No stock found for the selected filters."
            "</div>"
        )

    css = _get_css()

    return f"""
<div class="csr-wrap">
{css}
{no_data_warn}
<div class="csr-layout">
  <div class="csr-left">{gi_table}</div>
  <div class="csr-right">{other_table}{summary_table}</div>
</div>
</div>
"""

def _get_css():
    return """
<style>
.csr-wrap {
    font-family: var(--font-stack);
    font-size: var(--text-sm, 12px);
    color: var(--text-color);
    padding: 8px 4px;
    width: 100%;
    box-sizing: border-box;
    overflow-x: auto;
}
.csr-layout {
    display: flex;
    gap: 20px;
    align-items: flex-start;
    width: 100%;
}
.csr-left {
    flex: 3 1 400px;
    min-width: 0;
}
.csr-right {
    flex: 2 1 300px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.csr-msg-muted {
    padding: 8px 0;
    color: var(--text-muted);
    font-style: italic;
    font-size: var(--text-sm, 12px);
}

/* ── Table base ── */
.csr-table {
    border-collapse: collapse;
    width: 100%;
    border: 1px solid var(--border-color);
}
.csr-table th,
.csr-table td {
    border: 1px solid var(--border-color);
    padding: 4px 8px;
    white-space: nowrap;
    font-size: var(--text-sm, 12px);
}

/* ── Section title (e.g. "GI Coils") ── */
.csr-table tr.csr-title th {
    background: var(--subtle-accent);
    font-weight: 700;
    text-align: center;
    font-size: var(--text-base, 13px);
    letter-spacing: 0.2px;
    color: var(--heading-color);
    border-bottom: 2px solid var(--border-color);
}

/* ── Column header row ── */
.csr-table tr.csr-col-hdr th {
    background: var(--control-bg);
    font-weight: 600;
    text-align: center;
    color: var(--text-color);
}

/* ── Coil-type header (□ Coil / □ Slitted) ── */
.csr-table tr.csr-type-hdr td {
    background: var(--fg-color);
    font-weight: 600;
    padding-left: 6px;
    color: var(--text-color);
}

/* ── Sub-total row (Coil Total / Slitted Total) ── */
.csr-table tr.csr-sub td {
    background: var(--control-bg);
    font-weight: 600;
}

/* ── Grand-total row ── */
.csr-table tr.csr-grand td {
    font-weight: 700;
    border-top: 2px solid var(--border-color);
    background: var(--subtle-accent);
}

.csr-num    { text-align: right; }
.csr-indent { padding-left: 20px !important; }
.csr-bold   { font-weight: 600; }

@media print {
    .csr-layout { display: flex !important; flex-wrap: nowrap !important; }
    .csr-table  { page-break-inside: avoid; }
}
</style>
"""

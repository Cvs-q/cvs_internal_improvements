# CVS Internal Improvements

Single Frappe app holding CVS's custom ERPNext reports and AI extraction tools.

| Module | Contents |
|---|---|

| CVS Stock | CVS Coil Summary Report, CVS Stock Balance Quantity, CVS Stock Ledger |
| CVS Production | OPR Production and Logistics Overview |
| CVS Stock Entry Import | CVS Stock Entry Import tool (AI extraction to Stock Entry) |
| CVS Invoice Tool | CVS Invoice Tool (AI invoice extraction), GPT Setting |

## Install

```
bench get-app <repo-url>
bench --site <site> install-app cvs_internal_improvements
bench --site <site> migrate
```

import frappe
from frappe.utils.password import set_encrypted_password


def execute():
	"""GPT API Key changed from Data to Password: move any existing plain-text key into the
	encrypted store and mask the stored column, so saved keys keep working and stop showing."""
	if not frappe.db.exists("DocType", "GPT Setting"):
		return

	for name, key in frappe.db.sql("select name, gpt_key from `tabGPT Setting`"):
		if not key or set(key) == {"*"}:
			continue
		set_encrypted_password("GPT Setting", name, key, "gpt_key")
		frappe.db.set_value("GPT Setting", name, "gpt_key", "*" * len(key), update_modified=False)

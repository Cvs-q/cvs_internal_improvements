(function () {
	"use strict";

	// Prevent a second copy if this script loads twice.
	if (window.cvsShortcutsLoaded) return;
	window.cvsShortcutsLoaded = true;

	// Ctrl (or Cmd) + Shift + key, on every document form:
	//   A -> Approve        X -> Reject        S -> Submit        Z -> Toggle sidebar
	const SHORTCUTS = {
		KeyA: () => workflowAction("approve"),
		KeyX: () => workflowAction("reject"),
		KeyS: () => submitDocument(),
		KeyZ: () => toggleSidebar(),
	};

	function currentForm() {
		if (!window.cur_frm || !cur_frm.doc || !cur_frm.page) return null;
		if (!cur_frm.page.wrapper.is(":visible")) return null;
		return cur_frm;
	}

	function notify(message) {
		frappe.show_alert({ message, indicator: "orange" }, 4);
	}

	// Approve / Reject are workflow actions. Frappe keeps every available action as a hidden
	// <li><a> in the form's Actions menu, so clicking that link runs exactly what the menu item
	// would (permission checks and "Are you sure?" confirmation included).
	function workflowAction(word) {
		const frm = currentForm();
		if (!frm) return;

		const links = frm.page.actions.find("li:not(.dropdown-divider) > a");
		const match = links.filter(function () {
			const label = $(this).find(".menu-item-label").text().trim().toLowerCase();
			return label === word || label.startsWith(word + " ");
		});

		if (!match.length) {
			notify(__("{0} is not available for this document right now.", [__(frappe.utils.to_title_case(word))]));
			return;
		}
		match.first().trigger("click");
	}

	// Submit: a workflow action called "Submit" if the doctype has a workflow, otherwise the form's
	// own Submit button (only shown when the document is saved and the user may submit it).
	function submitDocument() {
		const frm = currentForm();
		if (!frm) return;

		const links = frm.page.actions.find("li:not(.dropdown-divider) > a").filter(function () {
			return $(this).find(".menu-item-label").text().trim().toLowerCase() === "submit";
		});
		if (links.length) {
			links.first().trigger("click");
			return;
		}

		const button = frm.page.btn_primary;
		if (
			button &&
			button.length &&
			!button.hasClass("hide") &&
			button.is(":visible") &&
			button.text().trim() === __("Submit")
		) {
			button.trigger("click");
			return;
		}

		notify(
			frm.is_dirty()
				? __("Save the document first (Ctrl+S), then submit.")
				: __("Submit is not available for this document.")
		);
	}

	// On a form: the document sidebar (same as menu > Toggle Sidebar). On any other page:
	// the main desk sidebar.
	function toggleSidebar() {
		const frm = currentForm();

		if (
			frm &&
			!frm.page.hide_sidebar &&
			frappe.boot.desk_settings.form_sidebar &&
			frm.sidebar &&
			frm.sidebar.sidebar
		) {
			frm.toolbar.setup_sidebar_toggle(frm.sidebar.sidebar.parent());
			return;
		}

		if (frappe.app && frappe.app.sidebar) {
			frappe.app.sidebar.toggle_width();
		}
	}

	function onKeydown(event) {
		if (!(event.ctrlKey || event.metaKey) || !event.shiftKey || event.altKey) return;

		const handler = SHORTCUTS[event.code];
		if (!handler) return;

		// Leave pop-ups (confirm boxes, dialogs) alone.
		if (document.querySelector(".modal.show")) return;

		event.preventDefault();
		// Frappe already uses Ctrl+Shift+Z (redo) on forms; stop it from also firing.
		event.stopImmediatePropagation();

		try {
			handler();
		} catch (error) {
			console.error("CVS shortcuts:", error);
		}
	}

	// Capture phase, so this runs before Frappe's own key handlers.
	window.addEventListener("keydown", onKeydown, true);
})();

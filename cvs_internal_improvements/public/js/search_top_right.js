// Frappe v16 moved Search into the left dock. Put a v15-style search bar at the top right.
// The bar calls the awesome bar directly (like Ctrl+K does) instead of sharing the dock
// button's ".navbar-modal-search-mobile" class, so Frappe's delegated click handler can't
// also fire and close the modal again.
(function () {
	const DOCK_SEARCH = "#desk-dock .navbar-modal-search-mobile";

	// Frappe only creates the awesome bar when a Page is built (page.js setup_awesomebar), which
	// hasn't happened yet on the Home workspace. Create it the same way if it's missing;
	// the existence check stops Frappe from creating a second one later.
	function ensure_awesome_bar() {
		if (frappe.app.awesome_bar) return;
		if (!frappe.boot.desk_settings.search_bar) return;
		if (!frappe.search || !frappe.search.AwesomeBar) return;
		const awesome_bar = new frappe.search.AwesomeBar();
		awesome_bar.setup(".navbar-modal-search-mobile");
		frappe.app.awesome_bar = awesome_bar;
	}

	function open_search() {
		ensure_awesome_bar();
		const bar = frappe.app && frappe.app.awesome_bar;
		if (bar && typeof bar.open === "function") {
			if (bar.is_open && bar.is_open()) bar.close();
			else bar.open();
			return;
		}
		// Same entry point as the Ctrl+K shortcut.
		const shortcut = frappe.search && frappe.search.open_awesomebar_from_global_search_shortcut;
		if (typeof shortcut === "function") {
			shortcut({ preventDefault() {}, stopPropagation() {} });
			return;
		}
		// Last resort: click the dock's own search button.
		const dock_btn = document.querySelector(DOCK_SEARCH);
		if (dock_btn) dock_btn.click();
	}

	function add_top_search() {
		if (document.querySelector(".cvs-top-search")) return true;
		if (!window.frappe || !frappe.boot || !frappe.boot.desk_settings) return false;
		if (!frappe.boot.desk_settings.search_bar) return true; // search disabled: nothing to add
		if (!document.querySelector("#desk-dock")) return false; // desk not rendered yet

		const btn = document.createElement("button");
		btn.type = "button";
		btn.className = "cvs-top-search";
		btn.setAttribute("aria-label", __("Search"));
		btn.innerHTML =
			frappe.utils.icon("search", "sm") +
			'<span class="cvs-top-search-text">' +
			__("Search or type a command (Ctrl + K)") +
			"</span>";
		btn.addEventListener("click", (e) => {
			e.preventDefault();
			e.stopPropagation();
			open_search();
		});
		document.body.appendChild(btn);
		document.body.classList.add("cvs-top-search-on");
		return true;
	}

	function start() {
		if (add_top_search()) return;
		const observer = new MutationObserver(() => {
			if (add_top_search()) observer.disconnect();
		});
		observer.observe(document.body, { childList: true, subtree: true });
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start);
	} else {
		start();
	}
})();

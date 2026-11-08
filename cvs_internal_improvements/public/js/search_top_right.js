// Frappe v16 moved Search into the left dock. Put a v15-style search bar at the top right.
// Frappe (page.js) opens the search modal from a delegated click on ".navbar-modal-search-mobile",
// so the new bar carries that class itself and Frappe's own handler does the work.
(function () {
	function add_top_search() {
		if (document.querySelector(".cvs-top-search")) return true;
		if (!window.frappe || !frappe.boot || !frappe.boot.desk_settings) return false;
		if (!frappe.boot.desk_settings.search_bar) return true; // search disabled: nothing to add
		if (!document.querySelector("#desk-dock")) return false; // desk not rendered yet

		const btn = document.createElement("button");
		btn.type = "button";
		btn.className = "cvs-top-search navbar-modal-search-mobile";
		btn.setAttribute("aria-label", __("Search"));
		btn.innerHTML =
			frappe.utils.icon("search", "sm") +
			'<span class="cvs-top-search-text">' +
			__("Search or type a command (Ctrl + G)") +
			"</span>";
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

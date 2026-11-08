// Frappe v16 moved Search into the left dock. Put a Search button at the top right (as in v15)
// that triggers the dock's own search button, so it opens the same search.
(function () {
	const DOCK_SEARCH = "#desk-dock .navbar-modal-search-mobile";

	function add_top_search() {
		if (document.querySelector(".cvs-top-search")) return true;
		if (!document.querySelector(DOCK_SEARCH)) return false;

		const btn = document.createElement("button");
		btn.type = "button";
		btn.className = "cvs-top-search btn btn-default icon-btn";
		btn.title = __("Search");
		btn.setAttribute("aria-label", __("Search"));
		btn.innerHTML = frappe.utils.icon("search", "md");
		// Look the dock button up on click, in case the dock re-renders.
		btn.addEventListener("click", () => {
			const dock_btn = document.querySelector(DOCK_SEARCH);
			if (dock_btn) dock_btn.click();
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

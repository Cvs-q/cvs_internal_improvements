(function () {
	"use strict";

	// Prevent duplicate observers if this script loads twice.
	if (window.cvsTopSearchLoaded) return;
	window.cvsTopSearchLoaded = true;

	function getAwesomeBar() {
		if (!frappe.app || !frappe.search?.AwesomeBar) return null;

		if (!frappe.app.awesome_bar) {
			const bar = new frappe.search.AwesomeBar();
			bar.setup(".navbar-modal-search-mobile");
			frappe.app.awesome_bar = bar;
		}

		return frappe.app.awesome_bar;
	}

	function openSearch(event) {
		event.preventDefault();
		event.stopPropagation();

		try {
			const bar = getAwesomeBar();

			if (!bar) {
				frappe.msgprint(__("Search is still loading. Please try again."));
				return;
			}

			// Always open; do not toggle and accidentally close it.
			bar.open();
		} catch (error) {
			console.error("CVS top search:", error);
			frappe.msgprint(__("Unable to open search. Check the browser console."));
		}
	}

	function syncSearch() {
		if (!window.frappe?.boot?.desk_settings || !frappe.app) return;

		const enabled = Boolean(frappe.boot.desk_settings.search_bar);
		let button = document.getElementById("cvs-top-search");

		if (!enabled) {
			button?.remove();
			document.body.classList.remove("cvs-top-search-on");
			return;
		}

		if (!button) {
			button = document.createElement("button");
			button.id = "cvs-top-search";
			button.className = "cvs-top-search";
			button.type = "button";
			button.setAttribute("aria-label", __("Search or type a command"));
			button.setAttribute("aria-haspopup", "dialog");
			button.title = __("Search or type a command (Ctrl + K)");

			const label = document.createElement("span");
			label.className = "cvs-top-search-text";
			label.textContent = __("Search or type a command");

			const shortcut = document.createElement("span");
			shortcut.className = "cvs-top-search-shortcut";
			shortcut.textContent = frappe.utils.is_mac() ? "⌘K" : "Ctrl+K";

			button.innerHTML = frappe.utils.icon("search", "sm");
			button.append(label, shortcut);
			button.addEventListener("click", openSearch);
			document.body.appendChild(button);
		}

		document.body.classList.add("cvs-top-search-on");
	}

	function start() {
		let pending = false;

		function scheduleSync() {
			if (pending) return;
			pending = true;

			requestAnimationFrame(() => {
				pending = false;
				syncSearch();
			});
		}

		// Stay active when ERPNext rebuilds its page elements.
		const observer = new MutationObserver(scheduleSync);
		observer.observe(document.body, {
			childList: true,
			subtree: true,
		});

		scheduleSync();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start, { once: true });
	} else {
		start();
	}
})();
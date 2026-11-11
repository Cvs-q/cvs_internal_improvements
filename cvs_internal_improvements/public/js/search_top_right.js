(function () {
	"use strict";

	// Prevent duplicate observers if this script loads twice.
	if (window.cvsTopSearchLoaded) return;
	window.cvsTopSearchLoaded = true;

	let recentReady = false;

	// Frappe v16's AwesomeBar only knows how to live inside its pop-up modal. Its input/autocomplete
	// wiring (setup_event_listeners) just needs an object with find("#navbar-search") and modal(),
	// so we hand it a tiny stand-in around our own inline <input>. That gives the v15 behaviour:
	// type right in the header, results (and the calculator, e.g. "=2+3*4") drop down underneath.
	function attachAwesomeBar(input) {
		if (!window.frappe?.search?.AwesomeBar || !frappe.search.utils) return false;

		if (!recentReady) {
			frappe.search.utils.setup_recent();
			recentReady = true;
		}

		const bar = new frappe.search.AwesomeBar();
		bar.options = [];
		bar.global_results = [];

		const $input = $(input);
		const standIn = {
			find: (selector) => (selector === "#navbar-search" ? $input : $()),
			modal: () => {},
		};

		bar.setup_event_listeners(standIn);
		input._cvsBar = bar;
		return true;
	}

	function createSearch() {
		const wrapper = document.createElement("div");
		wrapper.className = "cvs-top-search";

		const input = document.createElement("input");
		input.type = "text";
		input.className = "cvs-top-search-input";
		input.setAttribute("autocomplete", "off");
		input.setAttribute("aria-label", __("Search or type a command"));
		input.placeholder = __("Search or type a command");
		wrapper.appendChild(input);

		if (!attachAwesomeBar(input)) return null;

		const shortcut = document.createElement("span");
		shortcut.className = "cvs-top-search-shortcut";
		shortcut.textContent = frappe.utils.is_mac() ? "⌘K" : "Ctrl+K";
		wrapper.appendChild(shortcut);

		return wrapper;
	}

	function visibleInput() {
		return Array.from(document.querySelectorAll(".cvs-top-search-input")).find(
			(el) => el.offsetParent !== null
		);
	}

	// Ctrl/Cmd+K focuses the inline box instead of opening Frappe's pop-up.
	function setupShortcut() {
		window.addEventListener(
			"keydown",
			(event) => {
				if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== "k") return;
				if (!document.body.classList.contains("cvs-top-search-on")) return;

				const input = visibleInput();
				if (!input) return;

				event.preventDefault();
				event.stopPropagation();
				input.focus();
				input.select();
			},
			true
		);
	}

	// The search box goes inside each page header, as the first item of the right-hand group,
	// so it sits on the same line with the page's own buttons (Actions, refresh, menu ...)
	// to its right, however many buttons that page has.
	function insertInto(container) {
		if (!container || container.querySelector(":scope > .cvs-top-search")) return;
		const search = createSearch();
		if (search) container.insertBefore(search, container.firstChild);
	}

	function syncSearch() {
		if (!window.frappe?.boot?.desk_settings || !frappe.app) return;

		const enabled = Boolean(frappe.boot.desk_settings.search_bar);

		if (!enabled) {
			document.querySelectorAll(".cvs-top-search").forEach((el) => el.remove());
			document.body.classList.remove("cvs-top-search-on");
			return;
		}

		document
			.querySelectorAll(".page-head .standard-items-section")
			.forEach((section) => insertInto(section));

		// The /desk start page has its own top bar (centered search, then bell and avatar on the
		// right). Put the search at the start of the right-hand group; the CSS hides the centered one.
		insertInto(document.querySelector(".desktop-navbar > .flex"));

		if (document.querySelector(".cvs-top-search")) {
			document.body.classList.add("cvs-top-search-on");
		}
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

		setupShortcut();
		scheduleSync();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", start, { once: true });
	} else {
		start();
	}
})();

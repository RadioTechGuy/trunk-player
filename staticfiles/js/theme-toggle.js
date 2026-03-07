// Theme toggle — persists to localStorage, respects prefers-color-scheme
(function () {
  const STORAGE_KEY = "gasda-theme";

  function getPreferred() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "dark" || stored === "light") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
    // Update toggle button icons
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      btn.textContent = theme === "dark" ? "\u2600" : "\u263E";
      btn.setAttribute("aria-label", theme === "dark" ? "Switch to light mode" : "Switch to dark mode");
    });
  }

  function toggle() {
    var current = document.documentElement.getAttribute("data-theme") || "light";
    apply(current === "dark" ? "light" : "dark");
  }

  // Apply on load
  apply(getPreferred());

  // Bind toggle buttons
  document.addEventListener("click", function (e) {
    if (e.target.closest(".theme-toggle")) {
      toggle();
    }
  });

  // Listen for OS theme changes
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", function (e) {
      if (!localStorage.getItem(STORAGE_KEY)) {
        apply(e.matches ? "dark" : "light");
      }
    });
})();

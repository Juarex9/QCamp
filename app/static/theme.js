(() => {
  const KEY = "qcamp-theme";
  const root = document.documentElement;
  const COLORS = { dark: "#121008", light: "#f0e8d6" };

  function apply(theme) {
    root.dataset.theme = theme;
    localStorage.setItem(KEY, theme);
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = COLORS[theme] || COLORS.dark;
    const btn = document.getElementById("theme-toggle");
    if (btn) btn.setAttribute("aria-pressed", theme === "light" ? "true" : "false");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.setAttribute(
      "aria-pressed",
      root.dataset.theme === "light" ? "true" : "false",
    );
    btn.addEventListener("click", () => {
      apply(root.dataset.theme === "light" ? "dark" : "light");
    });
  });
})();

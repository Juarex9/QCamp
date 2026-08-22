(() => {
  const hxHeaders = { "HX-Request": "true", Accept: "text/html" };

  function targetOf(el, selector) {
    if (!selector || selector === "this") return el;
    return document.querySelector(selector);
  }

  function swap(el, html, mode) {
    const how = (mode || "innerHTML").toLowerCase();
    if (how === "outerhtml") {
      el.outerHTML = html;
      return;
    }
    if (how === "afterbegin") {
      el.insertAdjacentHTML("afterbegin", html);
      return;
    }
    if (how === "beforeend") {
      el.insertAdjacentHTML("beforeend", html);
      return;
    }
    el.innerHTML = html;
  }

  async function exchange(el, url, method, body) {
    const res = await fetch(url, { method, headers: hxHeaders, body });
    const html = await res.text();
    const dest = targetOf(
      el,
      res.headers.get("HX-Retarget") || el.getAttribute("hx-target"),
    );
    if (dest) {
      swap(
        dest,
        html,
        res.headers.get("HX-Reswap") || el.getAttribute("hx-swap"),
      );
    }
    const trigger = res.headers.get("HX-Trigger");
    if (trigger) {
      document.body.dispatchEvent(new CustomEvent(trigger, { bubbles: true }));
    }
  }

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    const post = form.getAttribute("hx-post");
    const get = form.getAttribute("hx-get");
    if (!post && !get) return;
    event.preventDefault();
    const method = post ? "POST" : "GET";
    const url = post || get || form.action;
    exchange(form, url, method, method === "POST" ? new FormData(form) : null);
  });

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const el = event.target.closest("button[hx-get], a[hx-get]");
    if (!el) return;
    const trigger = el.getAttribute("hx-trigger") || "";
    if (trigger && !trigger.includes("click")) return;
    event.preventDefault();
    exchange(el, el.getAttribute("hx-get"), "GET");
  });

  document.body.addEventListener("remitoSaved", () => {
    document.querySelectorAll("[hx-get]").forEach((el) => {
      const trigger = el.getAttribute("hx-trigger") || "";
      if (trigger.includes("remitoSaved")) {
        exchange(el, el.getAttribute("hx-get"), "GET");
      }
    });
  });
})();

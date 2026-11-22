/* FarmConnect global desktop-style navigation — no hamburger menus. */
(function () {
  "use strict";
  function init() {
    if (document.getElementById("fc-global-nav")) return;
    const page = (location.pathname.split("/").pop() || "index.html").toLowerCase();
    const simple = ["login.html","register.html","profile.html","admin.html"].includes(page);
    if (simple) document.body.classList.add("fc-simple-page");

    const nav = document.createElement("nav");
    nav.id = "fc-global-nav";
    nav.className = "fc-global-nav";
    nav.setAttribute("aria-label", "Main navigation");

    const inner = document.createElement("div");
    inner.className = "fc-nav-inner";
    const brand = document.createElement("a");
    brand.className = "fc-brand";
    brand.href = "index.html";
    brand.innerHTML = '<span class="fc-brand-mark" aria-hidden="true">FC</span><span>FarmConnect <span class="fc-brand-accent">Zambia</span></span>';

    const links = document.createElement("div");
    links.className = "fc-nav-links";
    const items = [
      ["index.html","Home"],
      ["prices.html","Market Prices"],
      ["find-buyers.html","Buyers & Sellers"],
      ["news.html","News"]
    ];
    for (const [href,label] of items) {
      const a = document.createElement("a");
      a.href = href;
      a.textContent = label;
      if (page === href) {
        a.classList.add("fc-current");
        a.setAttribute("aria-current", "page");
      }
      links.appendChild(a);
    }

    // The public navigation intentionally contains no administrator link.
    // Administrators continue to access the protected control center via its URL.

    inner.append(brand,links);
    nav.appendChild(inner);
    document.body.insertBefore(nav,document.body.firstChild);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded",init);
  } else {
    init();
  }
})();

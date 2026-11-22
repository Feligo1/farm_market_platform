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
    brand.innerHTML = '<span class="fc-brand-mark" aria-hidden="true">▣</span><span>FarmConnect <span class="fc-brand-accent">Zambia</span></span>';

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

    let user = null;
    try { user = JSON.parse(localStorage.getItem("userData") || "null"); } catch (_) {}
    const isAdmin = !!localStorage.getItem("authToken") && user?.role === "admin";
    const admin = document.createElement("a");
    admin.href = isAdmin ? "admin.html" : "login.html";
    admin.textContent = isAdmin ? "Admin Panel" : "Admin";
    if (page === "admin.html" || page === "login.html") {
      admin.classList.add("fc-current");
      admin.setAttribute("aria-current", "page");
    }
    links.appendChild(admin);
    if (isAdmin) {
      const logout = document.createElement("a");
      logout.href = "login.html";
      logout.textContent = "Log out";
      logout.addEventListener("click", function (event) {
        event.preventDefault();
        localStorage.removeItem("authToken");
        localStorage.removeItem("userData");
        location.href = "index.html";
      });
      links.appendChild(logout);
    }

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

(function () {
  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");
  var year = document.getElementById("year");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (year) {
    year.textContent = String(new Date().getFullYear());
  }

  function setHeaderState() {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  }

  function closeNav() {
    if (!toggle) return;
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Открыть меню");
    document.body.classList.remove("nav-open");
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var expanded = toggle.getAttribute("aria-expanded") === "true";
      if (expanded) {
        closeNav();
      } else {
        toggle.setAttribute("aria-expanded", "true");
        toggle.setAttribute("aria-label", "Закрыть меню");
        document.body.classList.add("nav-open");
      }
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeNav();
  });

  window.addEventListener("resize", function () {
    if (window.matchMedia("(min-width: 980px)").matches) closeNav();
  });

  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });

  var revealNodes = document.querySelectorAll("[data-reveal]");
  if (reduce || !("IntersectionObserver" in window)) {
    revealNodes.forEach(function (el) {
      el.classList.add("is-visible");
    });
  } else {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16, rootMargin: "0px 0px -8% 0px" }
    );
    revealNodes.forEach(function (el) {
      observer.observe(el);
    });
  }

  function cycleActive(selector, interval) {
    var items = document.querySelectorAll(selector);
    if (!items.length) return;
    var index = 0;
    items[0].classList.add("is-active");
    if (reduce) return;
    setInterval(function () {
      items[index].classList.remove("is-active");
      index = (index + 1) % items.length;
      items[index].classList.add("is-active");
    }, interval);
  }

  cycleActive(".hero-flow li", 1400);
  cycleActive(".ai-flow li", 1600);
  cycleActive(".trust-nodes li", 960);
  cycleActive(".offline-flow li", 1200);
  cycleActive(".mbv-sources li", 1400);

  document.querySelectorAll("[data-copy]").forEach(function (button) {
    button.addEventListener("click", function () {
      var source = document.getElementById(button.getAttribute("data-copy"));
      if (!source) return;
      var text = source.textContent.replace(/^\s+|\s+$/g, "");
      function done() {
        button.textContent = "Copied";
        setTimeout(function () {
          button.textContent = "Copy";
        }, 1200);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done);
        return;
      }
      var area = document.createElement("textarea");
      area.value = text;
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      document.body.removeChild(area);
      done();
    });
  });

  var cookieNotice = document.getElementById("cookie-notice");
  var cookieBtn = document.getElementById("cookie-accept");
  if (cookieNotice) {
    if (localStorage.getItem("refiq_cookie_ok")) {
      cookieNotice.hidden = true;
    } else if (cookieBtn) {
      cookieBtn.addEventListener("click", function () {
        localStorage.setItem("refiq_cookie_ok", "1");
        cookieNotice.hidden = true;
      });
    }
  }
})();

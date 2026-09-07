(function () {
  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("nav");
  var year = document.getElementById("year");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (year) {
    year.textContent = String(new Date().getFullYear());
  }

  function updateHeader() {
    if (header) {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    }
  }

  function closeNav() {
    if (!toggle) return;
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Открыть меню");
    document.body.classList.remove("nav-open");
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      if (open) {
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

  window.addEventListener("resize", function () {
    if (window.matchMedia("(min-width: 981px)").matches) closeNav();
  });
  window.addEventListener("scroll", updateHeader, { passive: true });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeNav();
  });
  updateHeader();

  var revealNodes = document.querySelectorAll("[data-reveal]");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealNodes.forEach(function (node) {
      node.classList.add("is-visible");
    });
  } else {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
    );
    revealNodes.forEach(function (node) {
      observer.observe(node);
    });
  }

  document.querySelectorAll("[data-copy]").forEach(function (block) {
    var button = block.matches("button") ? block : block.querySelector(".copy-btn");
    var source = block.matches("button")
      ? document.getElementById(block.getAttribute("data-copy"))
      : block.querySelector("code");
    if (!button || !source) return;

    button.addEventListener("click", function () {
      var text = source.textContent.trim();
      var original = button.textContent;
      function done() {
        button.textContent = "Скопировано";
        setTimeout(function () {
          button.textContent = original;
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
      area.remove();
      done();
    });
  });

  var cookieNotice = document.getElementById("cookie-notice");
  var cookieButton = document.getElementById("cookie-accept");
  var storageKey = "refiq_cookie_ok";
  if (cookieNotice) {
    try {
      if (localStorage.getItem(storageKey)) {
        cookieNotice.hidden = true;
      } else if (cookieButton) {
        cookieButton.addEventListener("click", function () {
          localStorage.setItem(storageKey, "1");
          document.documentElement.classList.add("cookie-accepted");
          cookieNotice.hidden = true;
        });
      }
    } catch (error) {
      if (cookieButton) {
        cookieButton.addEventListener("click", function () {
          cookieNotice.hidden = true;
        });
      }
    }
  }
})();
